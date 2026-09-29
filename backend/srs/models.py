from datetime import date, timedelta

from django.conf import settings
from django.db import models

# SRS-04: six stages, reviewed after 1, 2, 4, 7, 14 and 30 days. INTERVALS[stage - 1] is the
# wait before the review at that stage.
INTERVALS = [1, 2, 4, 7, 14, 30]
MAX_STAGE = len(INTERVALS)


class UserVocabulary(models.Model):
    class Status(models.TextChoices):
        LEARNING = "learning", "Үйреніп жатыр"
        LEARNED = "learned", "Үйренілді"
        KNOWN = "known", "Бұрыннан біледі"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="words")
    vocabulary = models.ForeignKey("vocabulary.Vocabulary", on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.LEARNING)
    stage = models.PositiveSmallIntegerField(default=1)
    next_review_date = models.DateField(null=True, blank=True)
    started_on = models.DateField(default=date.today)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    lapses = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "user_vocabulary"
        unique_together = [("user", "vocabulary")]
        indexes = [
            models.Index(fields=["user", "next_review_date"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.vocabulary_id} stage {self.stage}"

    def start(self, today: date):
        self.status = self.Status.LEARNING
        self.stage = 1
        self.next_review_date = today + timedelta(days=INTERVALS[0])

    def remember(self, today: date):
        if self.stage >= MAX_STAGE:
            self.status = self.Status.LEARNED
            self.next_review_date = None
            return
        self.stage += 1
        self.next_review_date = today + timedelta(days=INTERVALS[self.stage - 1])

    def forget(self, today: date):
        # SRS-05: one stage down, and shown again in the same session.
        self.stage = max(1, self.stage - 1)
        self.status = self.Status.LEARNING
        self.next_review_date = today
        self.lapses += 1
