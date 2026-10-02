from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import Conversation
from srs.models import MAX_STAGE, UserVocabulary
from srs.views import new_words_left
from trainer.models import TrainerAttempt, trainer_stats
from vocabulary.course import unlocked_steps
from vocabulary.models import StepResult, Vocabulary

from . import achievements
from .models import Achievement, DailyGoal, ProgressLog
from .services import streak_days
from .week import week_summary


def _daily_goal(user, today, due_count: int) -> DailyGoal:
    goal = DailyGoal.objects.filter(user=user, date=today).first()
    if goal is None:
        left, _ = new_words_left(user, today)
        # get_or_create: the stats bar and a screen may both ask for the first time today at once.
        goal, _ = DailyGoal.objects.get_or_create(
            user=user, date=today, defaults={"reviews_target": due_count, "new_target": min(5, left)}
        )
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
        course_words = Vocabulary.objects.filter(course_step__in=unlocked_steps(user))
        total = course_words.count()
        started_ids = words.values_list("vocabulary_id", flat=True)
        not_started = course_words.exclude(id__in=started_ids).count()

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

        achievements.unlock_new(user)
        fresh = Achievement.objects.filter(user=user, seen=False)
        return Response(
            {
                # Badges earned since the learner last looked: the app congratulates, then marks them seen.
                "new_achievements": [achievements.describe(a) for a in fresh],
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
    """POST /api/progress/reset/ {confirm: true} — wipes words, course results, trainer history, chats and logs.

    Badges stay: they were earned.
    """

    @transaction.atomic
    def post(self, request):
        serializer = ResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not serializer.validated_data["confirm"]:
            return Response({"detail": "Растау керек."}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        # Today's AI calls stay counted: a reset must not reopen the daily chat limit.
        today = ProgressLog.objects.filter(user=user, date=timezone.localdate()).first()
        UserVocabulary.objects.filter(user=user).delete()
        TrainerAttempt.objects.filter(user=user).delete()
        Conversation.objects.filter(user=user).delete()
        ProgressLog.objects.filter(user=user).delete()
        DailyGoal.objects.filter(user=user).delete()
        StepResult.objects.filter(user=user).delete()
        if today and today.chat_requests:
            ProgressLog.objects.create(user=user, date=today.date, chat_requests=today.chat_requests)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WeekView(APIView):
    """GET /api/progress/week/ — the last 7 days, day by day, and the totals against the week before."""

    def get(self, request):
        return Response(week_summary(request.user))


class AchievementsView(APIView):
    """GET /api/achievements/ — every badge with the progress toward it."""

    def get(self, request):
        return Response(achievements.overview(request.user))


class AchievementsSeenView(APIView):
    """POST /api/achievements/seen/ — the congratulations were shown."""

    def post(self, request):
        Achievement.objects.filter(user=request.user, seen=False).update(seen=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
