from django.conf import settings
from django.db import models


class TrainerAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trainer_attempts")
    vocabulary = models.ForeignKey("vocabulary.Vocabulary", on_delete=models.CASCADE)
    pronoun = models.CharField(max_length=5)
    tense = models.CharField(max_length=10)
    form = models.CharField(max_length=12)
    answer = models.CharField(max_length=200)
    expected = models.CharField(max_length=200)
    correct = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "trainer_attempts"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "created_at"])]


def trainer_stats(user) -> dict:
    attempts = TrainerAttempt.objects.filter(user=user)
    total = attempts.count()
    correct = attempts.filter(correct=True).count()
    streak = 0
    for ok in attempts.values_list("correct", flat=True)[:500]:
        if not ok:
            break
        streak += 1
    return {
        "total": total,
        "correct": correct,
        "accuracy": round(100 * correct / total) if total else None,
        "streak": streak,
    }
