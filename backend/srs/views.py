from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from progress.services import log_activity
from users.models import Profile
from vocabulary.models import Vocabulary
from vocabulary.views import VocabularySerializer, progress_map

from .models import INTERVALS, UserVocabulary


def new_words_left(user, today) -> tuple[int, int]:
    profile, _ = Profile.objects.get_or_create(user=user)
    # "Already know" and words added from the chat do not use up the limit.
    started_today = (
        UserVocabulary.objects.filter(user=user, started_on=today)
        .exclude(status=UserVocabulary.Status.KNOWN)
        .exclude(vocabulary__source=Vocabulary.Source.CHAT)
        .count()
    )
    return max(0, profile.daily_new_limit - started_today), profile.daily_new_limit


class TodayView(APIView):
    """GET /api/srs/today/ — reviews first, then new words up to the daily limit (SRS-06, SRS-07)."""

    def get(self, request):
        today = timezone.localdate()
        user = request.user
        due = (
            UserVocabulary.objects.filter(user=user, status=UserVocabulary.Status.LEARNING, next_review_date__lte=today)
            .select_related("vocabulary")
            .order_by("next_review_date", "stage")
        )
        left, limit = new_words_left(user, today)
        taken = UserVocabulary.objects.filter(user=user).values_list("vocabulary_id", flat=True)
        new = Vocabulary.objects.filter(course_step__is_open=True).exclude(id__in=taken)[:left] if left else []
        progress = progress_map(user)
        ctx = {"progress": progress}
        return Response(
            {
                "review": VocabularySerializer([uv.vocabulary for uv in due], many=True, context=ctx).data,
                "new": VocabularySerializer(new, many=True, context=ctx).data,
                "new_limit": limit,
                "new_left": left,
                "intervals": INTERVALS,
            }
        )


class AnswerSerializer(serializers.Serializer):
    answer = serializers.ChoiceField(choices=["start", "known", "remember", "forget"])


class AnswerView(APIView):
    """POST /api/srs/{word_id}/answer/ — start / known / remember / forget."""

    @transaction.atomic
    def post(self, request, word_id):
        serializer = AnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answer = serializer.validated_data["answer"]
        vocab = get_object_or_404(Vocabulary, pk=word_id)
        today = timezone.localdate()
        item = UserVocabulary.objects.select_for_update().filter(user=request.user, vocabulary=vocab).first()

        if answer in {"start", "known"}:
            if item is not None:
                return Response({"detail": "Бұл сөз бұрыннан тізімде."}, status=status.HTTP_409_CONFLICT)
            if answer == "start":
                left, _ = new_words_left(request.user, today)
                if left <= 0:
                    return Response(
                        {"detail": "Бүгінгі жаңа сөздер лимиті бітті.", "code": "limit"},
                        status=status.HTTP_409_CONFLICT,
                    )
            item = UserVocabulary(user=request.user, vocabulary=vocab, started_on=today)
            if answer == "start":
                item.start(today)
                log_activity(request.user, new_words=1)
            else:
                item.status = UserVocabulary.Status.KNOWN
                item.next_review_date = None
        else:
            if item is None or item.status != UserVocabulary.Status.LEARNING:
                return Response({"detail": "Бұл сөз қайталауда жоқ."}, status=status.HTTP_409_CONFLICT)
            if answer == "remember":
                item.remember(today)
            else:
                item.forget(today)
            item.last_reviewed_at = timezone.now()
            log_activity(request.user, reviews=1, remembered=1 if answer == "remember" else 0)
        item.save()
        return Response(
            {
                "word_id": vocab.id,
                "status": item.status,
                "stage": item.stage,
                "next_review_date": item.next_review_date,
                "again_today": item.next_review_date == today,
            }
        )


class AddWordSerializer(serializers.Serializer):
    word = serializers.CharField(max_length=60)
    translation_kk = serializers.CharField(max_length=120)
    example_en = serializers.CharField(max_length=200, required=False, allow_blank=True)


class AddWordView(APIView):
    """Adds a word met in the AI chat to the learner's cards (outside the daily new-word limit)."""

    def post(self, request):
        serializer = AddWordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        word = data["word"].strip().lower()
        vocab, _ = Vocabulary.objects.get_or_create(
            word=word,
            defaults={
                "translation_kk": data["translation_kk"].strip(),
                "example_en": data.get("example_en", ""),
                "is_verb": False,
                "topic": "chat",
                "source": Vocabulary.Source.CHAT,
                "frequency_rank": 5000,
            },
        )
        today = timezone.localdate()
        item, created = UserVocabulary.objects.get_or_create(
            user=request.user, vocabulary=vocab, defaults={"started_on": today}
        )
        if created:
            item.start(today)
            item.save()
        return Response(
            {"word_id": vocab.id, "word": vocab.word, "added": created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
