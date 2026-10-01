from django.conf import settings
from django.db import models


class ProgressLog(models.Model):
    """One row per learner per day: what they did. Feeds streaks and the daily goal."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="progress_log")
    date = models.DateField()
    reviews = models.PositiveIntegerField(default=0)
    remembered = models.PositiveIntegerField(default=0)
    new_words = models.PositiveIntegerField(default=0)
    trainer_total = models.PositiveIntegerField(default=0)
    trainer_correct = models.PositiveIntegerField(default=0)
    chat_messages = models.PositiveIntegerField(default=0)
    # Every AI call (a dialog's opening line or a reply) counts against the daily chat limit.
    chat_requests = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "progress_log"
        unique_together = [("user", "date")]
        indexes = [models.Index(fields=["user", "date"])]


class DailyGoal(models.Model):
    """The day's plan, fixed when the learner first opens the app that day."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_goals")
    date = models.DateField()
    reviews_target = models.PositiveSmallIntegerField(default=0)
    new_target = models.PositiveSmallIntegerField(default=5)
    trainer_target = models.PositiveSmallIntegerField(default=10)
    chat_target = models.PositiveSmallIntegerField(default=4)
    chat_scenario = models.CharField(max_length=20, default="cafe")

    class Meta:
        db_table = "daily_goals"
        unique_together = [("user", "date")]


class Achievement(models.Model):
    """A badge the learner earned (the rules live in progress/achievements.py). Kept, even after a reset."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="achievements")
    key = models.CharField(max_length=40)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    # The learner has seen the congratulation pop-up.
    seen = models.BooleanField(default=False)

    class Meta:
        db_table = "achievements"
        unique_together = [("user", "key")]
        ordering = ["unlocked_at"]
