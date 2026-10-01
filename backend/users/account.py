"""The learner's own account: everything we keep about them, as one file, and the checks before changing it."""

from django.core.cache import cache
from django.utils import timezone

from chat.models import Conversation
from classroom.models import Group, Membership
from progress.models import Achievement, ProgressLog
from srs.models import UserVocabulary
from trainer.models import TrainerAttempt
from vocabulary.models import StepResult

# A stolen session must not become a stolen account: the current password is asked, with few tries.
PASSWORD_TRIES = 5
PASSWORD_LOCK_SECONDS = 15 * 60
WRONG_PASSWORD = "Ағымдағы құпиясөз қате."
TOO_MANY_TRIES = "Құпиясөз тым көп рет қате енгізілді. 15 минуттан кейін қайталаңыз."


def _fails_key(user) -> str:
    return f"account-password-fails:{user.pk}"


def password_locked(user) -> bool:
    return cache.get(_fails_key(user), 0) >= PASSWORD_TRIES


def confirm_password(user, password: str) -> bool:
    """True if the password is right; wrong tries are counted towards the lock."""
    if user.check_password(password or ""):
        cache.delete(_fails_key(user))
        return True
    key = _fails_key(user)
    cache.add(key, 0, PASSWORD_LOCK_SECONDS)
    try:
        cache.incr(key)
    except ValueError:  # expired between add and incr
        cache.set(key, 1, PASSWORD_LOCK_SECONDS)
    return False


def _dt(value):
    return value.isoformat() if value else None


def export_data(user) -> dict:
    """Everything stored about the learner, in plain JSON (GDPR-style "download my data")."""
    profile = getattr(user, "profile", None)
    return {
        "exported_at": timezone.now().isoformat(),
        "account": {
            "name": user.name,
            "email": user.email,
            "email_verified": user.email_verified,
            "is_teacher": user.is_teacher,
            "date_joined": _dt(user.date_joined),
            "last_login": _dt(user.last_login),
        },
        "profile": profile
        and {
            "level": profile.level,
            "daily_new_limit": profile.daily_new_limit,
            "daily_minutes": profile.daily_minutes,
            "onboarded": profile.onboarded,
            "reminder_enabled": profile.reminder_enabled,
            "reminder_hour": profile.reminder_hour,
        },
        "words": [
            {
                "word": w.vocabulary.word,
                "translation_kk": w.vocabulary.translation_kk,
                "status": w.status,
                "stage": w.stage,
                "started_on": _dt(w.started_on),
                "next_review_date": _dt(w.next_review_date),
                "last_reviewed_at": _dt(w.last_reviewed_at),
                "lapses": w.lapses,
            }
            for w in UserVocabulary.objects.filter(user=user).select_related("vocabulary").order_by("started_on", "id")
        ],
        "course": [
            {
                "step": r.step.number,
                "title": r.step.title_kk,
                "lessons_done": r.lessons_done,
                "best_percent": r.best_percent,
                "passed": r.passed,
                "updated_at": _dt(r.updated_at),
            }
            for r in StepResult.objects.filter(user=user).select_related("step").order_by("step__number")
        ],
        "trainer": [
            {
                "verb": a.vocabulary.word,
                "pronoun": a.pronoun,
                "tense": a.tense,
                "form": a.form,
                "answer": a.answer,
                "expected": a.expected,
                "correct": a.correct,
                "at": _dt(a.created_at),
            }
            for a in TrainerAttempt.objects.filter(user=user).select_related("vocabulary").order_by("created_at")
        ],
        "chat": [
            {
                "mode": c.mode,
                "scenario": c.scenario.title_kk if c.scenario else None,
                "started_at": _dt(c.created_at),
                "finished": c.finished,
                "messages": [
                    {
                        "role": m.role,
                        "text": m.text,
                        "translation_kk": m.translation_kk,
                        "correct": m.correct,
                        "corrections": m.corrections,
                        "new_words": m.new_words,
                        "at": _dt(m.created_at),
                    }
                    for m in c.messages.all()
                ],
            }
            for c in Conversation.objects.filter(user=user)
            .select_related("scenario")
            .prefetch_related("messages")
            .order_by("created_at")
        ],
        "daily_progress": [
            {
                "date": _dt(p.date),
                "reviews": p.reviews,
                "remembered": p.remembered,
                "new_words": p.new_words,
                "trainer_total": p.trainer_total,
                "trainer_correct": p.trainer_correct,
                "chat_messages": p.chat_messages,
            }
            for p in ProgressLog.objects.filter(user=user).order_by("date")
        ],
        "achievements": [
            {"key": a.key, "unlocked_at": _dt(a.unlocked_at)}
            for a in Achievement.objects.filter(user=user).order_by("unlocked_at")
        ],
        "groups_joined": [
            {"group": m.group.name, "teacher": m.group.teacher.name, "joined_at": _dt(m.joined_at)}
            for m in Membership.objects.filter(student=user).select_related("group__teacher")
        ],
        "groups_taught": [
            {"name": g.name, "students": g.memberships.count()} for g in Group.objects.filter(teacher=user)
        ],
    }
