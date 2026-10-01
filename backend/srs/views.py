from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import Message
from progress.services import log_activity
from users.models import Profile
from vocabulary.course import unlocked_steps
from vocabulary.models import Vocabulary
from vocabulary.views import VocabularySerializer, progress_map

from . import quiz
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


def next_new_words(user, count: int) -> list:
    """Words of the open course steps first; after them the dictionary words, most frequent first."""
    if count <= 0:
        return []
    taken = UserVocabulary.objects.filter(user=user).values_list("vocabulary_id", flat=True)
    untouched = Vocabulary.objects.exclude(id__in=taken)
    # Words of the steps this learner has opened, in course order.
    steps = unlocked_steps(user)
    words = list(untouched.filter(course_step__in=steps).order_by("course_step__number", "frequency_rank")[:count])
    if len(words) < count:
        dictionary = untouched.filter(course_step__isnull=True, source=Vocabulary.Source.WIKTIONARY)
        words += list(dictionary[: count - len(words)])
    return words


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
        new = next_new_words(user, left)
        progress = progress_map(user)
        ctx = {"progress": progress}
        review = []
        for uv in due:
            card = VocabularySerializer(uv.vocabulary, context=ctx).data
            # The exercise that checks this word at its stage (choice → listening → typing).
            card["quiz"] = quiz.build(uv.vocabulary, uv.stage)
            review.append(card)
        return Response(
            {
                "review": review,
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
            else:
                item.status = UserVocabulary.Status.KNOWN
                item.next_review_date = None
            try:
                with transaction.atomic():
                    item.save()
            except IntegrityError:
                # A second click on the same card arrived while the first one was being saved.
                return Response({"detail": "Бұл сөз бұрыннан тізімде."}, status=status.HTTP_409_CONFLICT)
            if answer == "start":
                log_activity(request.user, new_words=1)
            return self._result(vocab, item, today)
        if item is None or item.status != UserVocabulary.Status.LEARNING:
            return Response(NOT_IN_REVIEW, status=status.HTTP_409_CONFLICT)
        review_word(request.user, item, answer == "remember", today)
        return self._result(vocab, item, today)

    @staticmethod
    def _result(vocab, item, today):
        return Response(review_result(vocab, item, today))


NOT_IN_REVIEW = {"detail": "Бұл сөз қайталауда жоқ."}


def review_word(user, item: UserVocabulary, remembered: bool, today):
    """Moves the word up a stage (or one down, to be shown again today) and logs the review."""
    if remembered:
        item.remember(today)
    else:
        item.forget(today)
    item.last_reviewed_at = timezone.now()
    item.save()
    log_activity(user, reviews=1, remembered=1 if remembered else 0)


def review_result(vocab, item, today) -> dict:
    return {
        "word_id": vocab.id,
        "status": item.status,
        "stage": item.stage,
        "next_review_date": item.next_review_date,
        "again_today": item.next_review_date == today,
    }


class CheckSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["choice", "listen", "type"])
    # Empty means "I don't know": the word goes back a stage and the answer is shown.
    answer = serializers.CharField(max_length=120, allow_blank=True)


class CheckView(APIView):
    """POST /api/srs/{word_id}/check/ {mode, answer} — the server checks the exercise and moves the word."""

    @transaction.atomic
    def post(self, request, word_id):
        serializer = CheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vocab = get_object_or_404(Vocabulary, pk=word_id)
        item = UserVocabulary.objects.select_for_update().filter(user=request.user, vocabulary=vocab).first()
        if item is None or item.status != UserVocabulary.Status.LEARNING:
            return Response(NOT_IN_REVIEW, status=status.HTTP_409_CONFLICT)
        mode = serializer.validated_data["mode"]
        if not quiz.allowed(mode, item.stage):
            # The stage moved on (e.g. on another device): the card on screen is out of date.
            return Response(
                {"detail": "Бұл карточка жаңарды, тізімді қайта жүктейміз.", "code": "stale"},
                status=status.HTTP_409_CONFLICT,
            )
        today = timezone.localdate()
        verdict = quiz.check(vocab, mode, serializer.validated_data["answer"])
        review_word(request.user, item, verdict["correct"], today)
        return Response({**verdict, **review_result(vocab, item, today)})


class AddWordSerializer(serializers.Serializer):
    word = serializers.CharField(max_length=60)


def chat_translation(user, word: str) -> str | None:
    """The tutor's translation of a word it suggested to this learner, or None if it never did."""
    messages = (
        Message.objects.filter(conversation__user=user, role=Message.Role.ASSISTANT)
        .exclude(new_words=[])
        .order_by("-created_at")
        .values_list("new_words", flat=True)[:500]
    )
    for new_words in messages:
        for item in new_words:
            if str(item.get("word", "")).strip().lower() == word and item.get("translation_kk"):
                return str(item["translation_kk"]).strip()[:120]
    return None


class AddWordView(APIView):
    """Adds a word met in the AI chat to the learner's cards (outside the daily new-word limit).

    The dictionary is shared by all learners, so the translation never comes from the request: it is the one
    the tutor gave this learner in the chat. Only words the tutor actually suggested can be added.
    """

    def post(self, request):
        serializer = AddWordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        word = serializer.validated_data["word"].strip().lower()
        vocab = Vocabulary.objects.filter(word=word).first()
        if vocab is None:
            translation = chat_translation(request.user, word)
            if translation is None:
                return Response(
                    {"detail": "Бұл сөз чатта кездеспеді.", "code": "not_in_chat"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            vocab, _ = Vocabulary.objects.get_or_create(
                word=word,
                defaults={
                    "translation_kk": translation,
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
