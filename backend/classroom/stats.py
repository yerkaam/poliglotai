"""What a teacher sees about the learners of a group: progress numbers only, never the chat texts."""

from collections import Counter
from datetime import timedelta

from django.utils import timezone

from chat.models import Message
from progress.models import ProgressLog
from progress.services import streak_days
from srs.models import UserVocabulary
from trainer.models import TrainerAttempt
from vocabulary.course import course_state
from vocabulary.forms import FORM_LABELS_KK, TENSE_LABELS_KK


def _active(log) -> bool:
    return bool(log.reviews or log.new_words or log.trainer_total or log.chat_messages)


def student_row(user) -> dict:
    today = timezone.localdate()
    logs = [log for log in ProgressLog.objects.filter(user=user) if _active(log)]
    words = UserVocabulary.objects.filter(user=user)
    steps = course_state(user)
    current = next((s for s in steps if s.status == "open"), None)
    attempts = TrainerAttempt.objects.filter(user=user, created_at__date__gt=today - timedelta(days=30))
    tries = attempts.count()
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "last_active": max((log.date for log in logs), default=None),
        "streak": streak_days(user),
        "active_days_week": sum(1 for log in logs if log.date > today - timedelta(days=7)),
        "words_learning": words.filter(status=UserVocabulary.Status.LEARNING).count(),
        "words_learned": words.filter(status__in=[UserVocabulary.Status.LEARNED, UserVocabulary.Status.KNOWN]).count(),
        "steps_done": sum(1 for s in steps if s.status == "done"),
        "current_step": current.step.number if current else None,
        "current_step_title": current.step.title_kk if current else "",
        "accuracy_30d": round(100 * attempts.filter(correct=True).count() / tries) if tries else None,
    }


def common_mistakes(users, limit: int = 5) -> list[dict]:
    """The verb-table cells (tense × form) the group gets wrong most, in the trainer and the AI chat."""
    since = timezone.now() - timedelta(days=30)
    cells: Counter = Counter()
    learners: dict[tuple, set] = {}
    for user_id, tense, form in TrainerAttempt.objects.filter(
        user__in=users, correct=False, created_at__gte=since
    ).values_list("user_id", "tense", "form"):
        cells[(tense, form)] += 1
        learners.setdefault((tense, form), set()).add(user_id)
    for user_id, corrections in (
        Message.objects.filter(conversation__user__in=users, role=Message.Role.USER, created_at__gte=since)
        .exclude(corrections=[])
        .values_list("conversation__user_id", "corrections")
    ):
        for c in corrections:
            if c.get("tense") and c.get("form"):
                key = (c["tense"], c["form"])
                cells[key] += 1
                learners.setdefault(key, set()).add(user_id)
    return [
        {
            "tense": tense,
            "form": form,
            "label_kk": f"{TENSE_LABELS_KK.get(tense, tense)} · {FORM_LABELS_KK.get(form, form)}",
            "mistakes": count,
            "learners": len(learners[(tense, form)]),
        }
        for (tense, form), count in cells.most_common(limit)
    ]
