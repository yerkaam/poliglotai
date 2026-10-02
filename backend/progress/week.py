"""The week in numbers: what the learner did on each of the last 7 days, compared with the week before."""

from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from srs.models import UserVocabulary
from trainer.models import TrainerAttempt

from .models import Achievement, ProgressLog
from .services import streak_days

WEEKDAYS_KK = ["Дс", "Сс", "Ср", "Бс", "Жм", "Сб", "Жс"]
FIELDS = ["reviews", "new_words", "trainer_total", "chat_messages"]


def _total(log) -> int:
    return sum(getattr(log, f) for f in FIELDS) if log else 0


def week_summary(user, today=None) -> dict:
    today = today or timezone.localdate()
    start = today - timedelta(days=6)
    logs = {log.date: log for log in ProgressLog.objects.filter(user=user, date__gte=start, date__lte=today)}
    days = []
    for i in range(7):
        day = start + timedelta(days=i)
        log = logs.get(day)
        days.append(
            {
                "date": day,
                "weekday_kk": WEEKDAYS_KK[day.weekday()],
                "reviews": log.reviews if log else 0,
                "new_words": log.new_words if log else 0,
                "trainer": log.trainer_total if log else 0,
                "chat": log.chat_messages if log else 0,
                "total": _total(log),
            }
        )
    previous = ProgressLog.objects.filter(user=user, date__gte=start - timedelta(days=7), date__lt=start)
    previous_total = sum(_total(log) for log in previous)
    attempts = TrainerAttempt.objects.filter(user=user, created_at__date__gte=start)
    tries = attempts.count()
    right = attempts.filter(correct=True).count()
    sums = ProgressLog.objects.filter(user=user, date__gte=start, date__lte=today).aggregate(
        **{f: Sum(f) for f in FIELDS}
    )
    return {
        "days": days,
        "total": sum(d["total"] for d in days),
        "previous_total": previous_total,
        "active_days": sum(1 for d in days if d["total"]),
        "reviews": sums["reviews"] or 0,
        "new_words": sums["new_words"] or 0,
        "sentences": sums["trainer_total"] or 0,
        "chat_messages": sums["chat_messages"] or 0,
        "accuracy": round(100 * right / tries) if tries else None,
        "learned": UserVocabulary.objects.filter(
            user=user, status=UserVocabulary.Status.LEARNED, last_reviewed_at__date__gte=start
        ).count(),
        "streak": streak_days(user),
        "achievements": list(
            Achievement.objects.filter(user=user, unlocked_at__date__gte=start).values_list("key", flat=True)
        ),
    }
