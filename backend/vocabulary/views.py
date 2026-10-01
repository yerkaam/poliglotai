from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from srs.models import UserVocabulary

from . import course, forms
from .models import Vocabulary


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
    """GET /api/course/ — the 16 steps for this learner: done, open, locked or not published yet."""

    def get(self, request):
        return Response([state.as_dict() for state in course.course_state(request.user)])


def _unlocked_state(user, number):
    state = next((s for s in course.course_state(user) if s.step.number == number), None)
    if state is None:
        raise NotFound()
    if not state.unlocked:
        raise PermissionDenied("Бұл қадам әлі ашылмады. Алдыңғы қадамды аяқтаңыз.")
    return state


class StepView(APIView):
    """GET /api/course/{n}/ — the lesson, the step's words and its check (without the answers)."""

    def get(self, request, number):
        state = _unlocked_state(request.user, number)
        step = state.step
        words = Vocabulary.objects.filter(course_step=step)
        return Response(
            {
                **state.as_dict(),
                "intro_kk": step.intro_kk,
                "lesson": step.lesson,
                "exercises": course.public_exercises(step),
                "words": VocabularySerializer(words, many=True, context={"progress": progress_map(request.user)}).data,
                "pass_percent": course.PASS_PERCENT,
            }
        )


class LessonsDoneSerializer(serializers.Serializer):
    done = serializers.IntegerField(min_value=0, max_value=100)


class StepLessonsView(APIView):
    """POST /api/course/{n}/lessons/ {done} — the learner finished a lesson; resume there next time."""

    def post(self, request, number):
        state = _unlocked_state(request.user, number)
        serializer = LessonsDoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {"lessons_done": course.save_lessons_done(request.user, state.step, serializer.validated_data["done"])}
        )


class CheckAnswersSerializer(serializers.Serializer):
    answers = serializers.ListField(child=serializers.CharField(max_length=200, allow_blank=True), max_length=50)


class StepCheckView(APIView):
    """POST /api/course/{n}/check/ {answers: [...]} — scores the check; a pass may open the next step."""

    def post(self, request, number):
        state = _unlocked_state(request.user, number)
        serializer = CheckAnswersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(course.check(request.user, state.step, serializer.validated_data["answers"]))
