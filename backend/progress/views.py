from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import Conversation
from srs.models import MAX_STAGE, UserVocabulary
from srs.views import new_words_left
from trainer.models import TrainerAttempt, trainer_stats
from vocabulary.models import Vocabulary

from .models import DailyGoal, ProgressLog
from .services import streak_days


def _daily_goal(user, today, due_count: int) -> DailyGoal:
    goal = DailyGoal.objects.filter(user=user, date=today).first()
    if goal is None:
        left, _ = new_words_left(user, today)
        goal = DailyGoal.objects.create(user=user, date=today, reviews_target=due_count, new_target=min(5, left))
    return goal


class ProgressView(APIView):
    """GET /api/progress/ — the stats bar, the day's goal and the words by stage (3.5)."""

    def get(self, request):
        user = request.user
        today = timezone.localdate()
        words = UserVocabulary.objects.filter(user=user)
        learning = words.filter(status=UserVocabulary.Status.LEARNING)
        due = learning.filter(next_review_date__lte=today).count()
        learned = words.filter(status__in=[UserVocabulary.Status.LEARNED, UserVocabulary.Status.KNOWN]).count()
        total = Vocabulary.objects.filter(course_step__is_open=True).count()
        started_ids = words.values_list("vocabulary_id", flat=True)
        not_started = Vocabulary.objects.filter(course_step__is_open=True).exclude(id__in=started_ids).count()

        stages = [{"stage": s, "count": learning.filter(stage=s).count()} for s in range(1, MAX_STAGE + 1)]
        log = ProgressLog.objects.filter(user=user, date=today).first()
        goal = _daily_goal(user, today, due)
        chat_today = log.chat_messages if log else 0

        tasks = []
        if goal.reviews_target:
            tasks.append({"key": "reviews", "target": goal.reviews_target, "done": log.reviews if log else 0})
        if goal.new_target:
            tasks.append({"key": "new", "target": goal.new_target, "done": log.new_words if log else 0})
        tasks.append({"key": "trainer", "target": goal.trainer_target, "done": log.trainer_total if log else 0})
        tasks.append({"key": "chat", "target": goal.chat_target, "done": chat_today, "scenario": goal.chat_scenario})
        for t in tasks:
            t["complete"] = t["done"] >= t["target"]

        return Response(
            {
                "stats": {
                    "learning": learning.count(),
                    "learned": learned,
                    "due": due,
                    "accuracy": trainer_stats(user)["accuracy"],
                    "streak": streak_days(user),
                },
                "stages": stages,
                "not_started": not_started,
                "learned_of": {"learned": learned, "total": total},
                "goal": {
                    "tasks": tasks,
                    "done": sum(1 for t in tasks if t["complete"]),
                    "total": len(tasks),
                },
            }
        )


class ResetSerializer(serializers.Serializer):
    confirm = serializers.BooleanField()


class ResetView(APIView):
    """POST /api/progress/reset/ {confirm: true} — wipes words, trainer history, chats and logs."""

    @transaction.atomic
    def post(self, request):
        serializer = ResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not serializer.validated_data["confirm"]:
            return Response({"detail": "Растау керек."}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        UserVocabulary.objects.filter(user=user).delete()
        TrainerAttempt.objects.filter(user=user).delete()
        Conversation.objects.filter(user=user).delete()
        ProgressLog.objects.filter(user=user).delete()
        DailyGoal.objects.filter(user=user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
