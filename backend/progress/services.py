from datetime import timedelta

from django.db.models import F
from django.utils import timezone

from .models import ProgressLog


def log_activity(user, **increments):
    """Adds counters to today's progress_log row, creating it when needed."""
    increments = {k: v for k, v in increments.items() if v}
    if not increments:
        return
    today = timezone.localdate()
    ProgressLog.objects.get_or_create(user=user, date=today)
    ProgressLog.objects.filter(user=user, date=today).update(**{k: F(k) + v for k, v in increments.items()})


def streak_days(user) -> int:
    """Consecutive active days ending today (or yesterday, if today has no activity yet)."""
    dates = set(ProgressLog.objects.filter(user=user).values_list("date", flat=True))
    day = timezone.localdate()
    if day not in dates:
        day -= timedelta(days=1)
    count = 0
    while day in dates:
        count += 1
        day -= timedelta(days=1)
    return count
