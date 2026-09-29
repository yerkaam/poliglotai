import random

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from progress.services import log_activity
from srs.models import UserVocabulary
from vocabulary import forms
from vocabulary.models import Vocabulary

from .models import TrainerAttempt, trainer_stats


def _task_payload(vocab: Vocabulary, pronoun: str, tense: str, form: str) -> dict:
    return {
        "verb": {"id": vocab.id, "word": vocab.word, "translation_kk": vocab.translation_kk},
        "pronoun": pronoun,
        "pronoun_kk": forms.PRONOUN_LABELS_KK[pronoun],
        "tense": tense,
        "tense_kk": forms.TENSE_LABELS_KK[tense],
        "form": form,
        "form_kk": forms.FORM_LABELS_KK[form],
    }


class TaskView(APIView):
    """GET /api/trainer/task/ — who · tense · form · verb. The verb comes from words being learned."""

    def get(self, request):
        learning = list(
            UserVocabulary.objects.filter(
                user=request.user, status=UserVocabulary.Status.LEARNING, vocabulary__is_verb=True
            ).values_list("vocabulary_id", flat=True)
        )
        pool = (
            Vocabulary.objects.filter(id__in=learning)
            if learning
            else Vocabulary.objects.filter(is_verb=True, course_step__number=1)[:10]
        )
        pool = list(pool)
        if not pool:
            return Response({"detail": "Етістіктер жоқ."}, status=404)
        vocab = random.choice(pool)
        task = _task_payload(
            vocab, random.choice(forms.PRONOUNS), random.choice(forms.TENSES), random.choice(forms.FORMS)
        )
        task["from_learning"] = bool(learning)
        return Response({"task": task, "stats": trainer_stats(request.user)})


class CheckSerializer(serializers.Serializer):
    verb_id = serializers.IntegerField()
    pronoun = serializers.ChoiceField(choices=forms.PRONOUNS)
    tense = serializers.ChoiceField(choices=forms.TENSES)
    form = serializers.ChoiceField(choices=forms.FORMS)
    answer = serializers.CharField(max_length=200, allow_blank=True)


class CheckView(APIView):
    """POST /api/trainer/check/ — the same form service as the table checks the answer."""

    def post(self, request):
        serializer = CheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        vocab = get_object_or_404(Vocabulary, pk=data["verb_id"], is_verb=True)
        parts = forms.build_for(vocab, data["pronoun"], data["tense"], data["form"])
        expected = forms.sentence(parts)
        correct = forms.is_correct(data["answer"], expected)
        TrainerAttempt.objects.create(
            user=request.user,
            vocabulary=vocab,
            pronoun=data["pronoun"],
            tense=data["tense"],
            form=data["form"],
            answer=data["answer"],
            expected=expected,
            correct=correct,
        )
        log_activity(request.user, trainer_total=1, trainer_correct=1 if correct else 0)
        return Response(
            {
                "correct": correct,
                "expected": expected,
                "parts": [p.as_dict() for p in parts],
                "stats": trainer_stats(request.user),
            }
        )
