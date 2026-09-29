from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from srs.models import UserVocabulary

from . import forms
from .models import CourseStep, Vocabulary


class VocabularySerializer(serializers.ModelSerializer):
    past = serializers.CharField(read_only=True)
    status = serializers.SerializerMethodField()
    stage = serializers.SerializerMethodField()

    class Meta:
        model = Vocabulary
        fields = [
            "id",
            "word",
            "translation_kk",
            "ipa",
            "is_verb",
            "past",
            "is_irregular",
            "example_en",
            "example_kk",
            "topic",
            "course_step",
            "source",
            "status",
            "stage",
        ]

    def _progress(self, obj):
        return self.context.get("progress", {}).get(obj.id)

    def get_status(self, obj):
        item = self._progress(obj)
        return item.status if item else "new"

    def get_stage(self, obj):
        item = self._progress(obj)
        return item.stage if item else 0


def progress_map(user):
    return {uv.vocabulary_id: uv for uv in UserVocabulary.objects.filter(user=user)}


class VerbListView(APIView):
    """TBL-03: verbs for the picker, each marked new / learning / learned."""

    def get(self, request):
        verbs = Vocabulary.objects.filter(is_verb=True)
        data = VocabularySerializer(verbs, many=True, context={"progress": progress_map(request.user)}).data
        return Response(data)


class VerbFormsView(APIView):
    """GET /api/verbs/{id}/forms/?pronoun=she — the nine forms (TBL-04…07)."""

    def get(self, request, pk):
        vocab = get_object_or_404(Vocabulary, pk=pk, is_verb=True)
        pronoun = request.query_params.get("pronoun", "I")
        if pronoun not in forms.PRONOUNS:
            return Response({"detail": f"pronoun must be one of {forms.PRONOUNS}"}, status=400)
        return Response(
            {
                "verb": VocabularySerializer(vocab, context={"progress": progress_map(request.user)}).data,
                "pronoun": pronoun,
                "cells": forms.table(vocab, pronoun),
            }
        )


class CourseView(APIView):
    def get(self, request):
        steps = CourseStep.objects.all()
        learned = set(
            UserVocabulary.objects.filter(
                user=request.user, status__in=[UserVocabulary.Status.LEARNED, UserVocabulary.Status.KNOWN]
            ).values_list("vocabulary_id", flat=True)
        )
        started = set(UserVocabulary.objects.filter(user=request.user).values_list("vocabulary_id", flat=True))
        result = []
        for step in steps:
            ids = list(Vocabulary.objects.filter(course_step=step).values_list("id", flat=True))
            total = len(ids)
            done = sum(1 for i in ids if i in learned)
            touched = sum(1 for i in ids if i in started)
            # Step progress: learned words count fully, words in progress count half.
            percent = round(100 * (done + 0.5 * (touched - done)) / total) if total else 0
            result.append(
                {
                    "number": step.number,
                    "title_kk": step.title_kk,
                    "title_en": step.title_en,
                    "description_kk": step.description_kk,
                    "status": "open" if step.is_open else "soon",
                    "words_total": total,
                    "words_learned": done,
                    "percent": percent,
                }
            )
        return Response(result)
