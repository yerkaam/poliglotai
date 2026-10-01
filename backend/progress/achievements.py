"""Badges: milestones computed from what the learner has already done, so nothing extra is tracked.

Each rule has a metric and a target; reaching the target unlocks the badge once, for good.
"""

from dataclasses import dataclass
from datetime import timedelta

from django.db.models import Count

from chat.models import Conversation, Message
from srs.models import UserVocabulary
from trainer.models import TrainerAttempt

from .models import Achievement, ProgressLog


@dataclass(frozen=True)
class Rule:
    key: str
    metric: str
    target: int
    title_kk: str
    description_kk: str
    icon: str  # an app icon name


RULES = [
    Rule("first_word", "words", 1, "Алғашқы сөз", "Бірінші сөзді үйрене бастадыңыз", "cards"),
    Rule("words_10", "words", 10, "10 сөз", "10 сөз үйренуде", "cards"),
    Rule("words_50", "words", 50, "50 сөз", "50 сөз үйренуде", "cards"),
    Rule("words_100", "words", 100, "100 сөз", "100 сөз үйренуде", "cards"),
    Rule("words_250", "words", 250, "250 сөз", "250 сөз үйренуде", "cards"),
    Rule("learned_10", "learned", 10, "10 сөз есте", "10 сөз толық үйренілді", "check"),
    Rule("learned_50", "learned", 50, "50 сөз есте", "50 сөз толық үйренілді", "check"),
    Rule("streak_3", "best_streak", 3, "3 күн қатарынан", "Үш күн үзбей оқыдыңыз", "flame"),
    Rule("streak_7", "best_streak", 7, "Бір апта", "Жеті күн үзбей оқыдыңыз", "flame"),
    Rule("streak_30", "best_streak", 30, "Бір ай", "Отыз күн үзбей оқыдыңыз", "flame"),
    Rule("trainer_50", "sentences", 50, "50 сөйлем", "Жаттықтырғышта 50 сөйлем", "target"),
    Rule("trainer_200", "sentences", 200, "200 сөйлем", "Жаттықтырғышта 200 сөйлем", "target"),
    Rule("trainer_row_10", "best_row", 10, "10 қатарынан", "Жаттықтырғышта 10 сөйлем қатесіз", "target"),
    Rule("chat_first", "chat_lines", 1, "Алғашқы диалог", "AI-мен алғаш сөйлестіңіз", "chat"),
    Rule("chat_dialogs_10", "dialogs_done", 10, "10 диалог", "10 диалогты соңына дейін жеткіздіңіз", "chat"),
    Rule("step_1", "steps_done", 1, "Негізгі кесте", "1-қадам аяқталды", "book"),
    Rule("steps_5", "steps_done", 5, "5 қадам", "Курстың 5 қадамы аяқталды", "book"),
    Rule("course_done", "steps_done", 16, "Курс аяқталды", "16 қадамның бәрі аяқталды", "book"),
]
RULES_BY_KEY = {r.key: r for r in RULES}


def best_streak(dates: set) -> int:
    best = run = 0
    previous = None
    for day in sorted(dates):
        run = run + 1 if previous is not None and day - previous == timedelta(days=1) else 1
        best = max(best, run)
        previous = day
    return best


def metrics(user) -> dict[str, int]:
    from vocabulary.course import course_state  # the course module imports srs, keep the import local

    words = UserVocabulary.objects.filter(user=user)
    active_days = {
        log.date
        for log in ProgressLog.objects.filter(user=user)
        if log.reviews or log.new_words or log.trainer_total or log.chat_messages
    }
    results = list(TrainerAttempt.objects.filter(user=user).order_by("created_at").values_list("correct", flat=True))
    best_row = run = 0
    for ok in results:
        run = run + 1 if ok else 0
        best_row = max(best_row, run)
    finished = (
        Conversation.objects.filter(user=user, finished=True)
        .annotate(lines=Count("messages"))
        .filter(lines__gt=1)
        .count()
    )
    return {
        "words": words.exclude(status=UserVocabulary.Status.KNOWN).count(),
        "learned": words.filter(status=UserVocabulary.Status.LEARNED).count(),
        "best_streak": best_streak(active_days),
        "sentences": len(results),
        "best_row": best_row,
        "chat_lines": Message.objects.filter(conversation__user=user, role=Message.Role.USER).count(),
        "dialogs_done": finished,
        "steps_done": sum(1 for s in course_state(user) if s.status == "done"),
    }


def unlock_new(user, values: dict[str, int] | None = None) -> list[Achievement]:
    """Saves the badges reached since last time and returns them (not yet seen by the learner)."""
    values = values or metrics(user)
    have = set(Achievement.objects.filter(user=user).values_list("key", flat=True))
    new = [r for r in RULES if r.key not in have and values[r.metric] >= r.target]
    created = [Achievement.objects.get_or_create(user=user, key=r.key)[0] for r in new]
    return created


def describe(achievement: Achievement) -> dict:
    rule = RULES_BY_KEY[achievement.key]
    return {"key": rule.key, "title_kk": rule.title_kk, "description_kk": rule.description_kk, "icon": rule.icon}


def overview(user) -> list[dict]:
    """Every badge, earned or not, with the progress toward it."""
    values = metrics(user)
    unlock_new(user, values)
    earned = {a.key: a for a in Achievement.objects.filter(user=user)}
    return [
        {
            "key": r.key,
            "title_kk": r.title_kk,
            "description_kk": r.description_kk,
            "icon": r.icon,
            "target": r.target,
            "current": min(values[r.metric], r.target),
            "unlocked_at": earned[r.key].unlocked_at if r.key in earned else None,
        }
        for r in RULES
    ]
