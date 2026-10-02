import json
from collections import Counter

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from progress.models import ProgressLog
from progress.services import log_activity
from srs.models import UserVocabulary
from users.models import Profile
from vocabulary.course import course_state
from vocabulary.forms import FORM_LABELS_KK, TENSE_LABELS_KK

from .llm import BLOCKLIST, UNAVAILABLE_TEXT, TutorUnavailable, ask_tutor, build_system_prompt, stream_tutor
from .models import Conversation, Message, Scenario


def usage(user) -> dict:
    """Calls to the AI today (opening lines and replies), against the daily limit that keeps API costs down.

    Counted per calendar day, like the counter on the screen; rejected and failed requests do not count.
    """
    log = ProgressLog.objects.filter(user=user, date=timezone.localdate()).first()
    return {"used": log.chat_requests if log else 0, "limit": settings.CHAT_DAILY_LIMIT}


def limit_reached(user) -> bool:
    current = usage(user)
    return current["used"] >= current["limit"]


LIMIT_REACHED = {"detail": "Бүгінгі хабарламалар лимиті бітті. Ертең жалғастырамыз!", "code": "chat_limit"}


class ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = ["slug", "title_kk", "max_turns"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "role",
            "text",
            "translation_kk",
            "hint_en",
            "new_words",
            "correct",
            "corrections",
            "created_at",
        ]


class ConversationSerializer(serializers.ModelSerializer):
    scenario = ScenarioSerializer(read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "mode", "scenario", "finished", "created_at", "messages"]


def _system_prompt(conversation: Conversation) -> str:
    """The learner block for this chat: built once, then reused unchanged so the prompt cache keeps hitting."""
    if not conversation.system_prompt:
        conversation.system_prompt = _build_system_prompt(conversation)
        if conversation.pk:
            conversation.save(update_fields=["system_prompt"])
    return conversation.system_prompt


def _build_system_prompt(conversation: Conversation) -> str:
    user = conversation.user
    profile, _ = Profile.objects.get_or_create(user=user)
    # The 60 most recently started verbs, alphabetically: a stable order, so the same words give the same text.
    verbs = sorted(
        UserVocabulary.objects.filter(user=user, vocabulary__is_verb=True)
        .exclude(status=UserVocabulary.Status.KNOWN)
        .order_by("-started_on", "-id")
        .values_list("vocabulary__word", flat=True)[:60]
    )
    states = course_state(user)
    steps = [f"{s.step.number}. {s.step.title_en}" for s in states if s.unlocked]
    done = [s.step for s in states if s.status == "done"]
    return build_system_prompt(
        level=profile.level,
        steps=steps,
        verbs=verbs,
        mode=conversation.mode,
        scenario=conversation.scenario,
        grammar=[s.grammar_en for s in done if s.grammar_en],
        done_numbers={s.number for s in done},
    )


def _history(conversation: Conversation) -> list[dict]:
    return [{"role": m.role, "content": m.text} for m in conversation.messages.all()]


def _save_assistant(conversation: Conversation, reply) -> Message:
    if reply.finished:
        conversation.finished = True
        conversation.save(update_fields=["finished"])
    return Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        text=reply.reply,
        translation_kk=reply.reply_kk,
        hint_en=reply.answer_template,
        new_words=[w.model_dump() for w in reply.new_words],
    )


UNAVAILABLE_BODY = {"detail": UNAVAILABLE_TEXT}


def unavailable() -> Response:
    return Response(UNAVAILABLE_BODY, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class ScenarioListView(APIView):
    def get(self, request):
        return Response(
            {
                "scenarios": ScenarioSerializer(Scenario.objects.filter(is_active=True), many=True).data,
                "usage": usage(request.user),
            }
        )


class StartSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=Conversation.Mode.choices)
    scenario = serializers.SlugField(required=False, allow_null=True)


class ConversationListView(APIView):
    def post(self, request):
        serializer = StartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mode = serializer.validated_data["mode"]
        scenario = None
        if mode == Conversation.Mode.DIALOG:
            slug = serializer.validated_data.get("scenario") or "cafe"
            scenario = get_object_or_404(Scenario, slug=slug, is_active=True)
        if limit_reached(request.user):
            return Response(LIMIT_REACHED, status=status.HTTP_429_TOO_MANY_REQUESTS)
        conversation = Conversation.objects.create(user=request.user, mode=mode, scenario=scenario)
        try:
            reply = ask_tutor(system=_system_prompt(conversation), history=[])
        except TutorUnavailable:
            conversation.delete()
            return unavailable()
        _save_assistant(conversation, reply)
        log_activity(request.user, chat_requests=1)
        return Response(ConversationSerializer(conversation).data, status=status.HTTP_201_CREATED)


class ConversationDetailView(APIView):
    def get(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
        return Response(ConversationSerializer(conversation).data)


class SendSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=500)


def _check_send(request, pk):
    """(conversation, text, None) when the message may go to the tutor, else (…, error Response)."""
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    serializer = SendSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    text = serializer.validated_data["text"].strip()
    if not text:
        return conversation, text, Response({"detail": "Бос хабарлама."}, status=status.HTTP_400_BAD_REQUEST)
    if conversation.finished:
        error = Response({"detail": "Диалог аяқталды. Жаңасын бастаңыз."}, status=status.HTTP_409_CONFLICT)
        return conversation, text, error
    if BLOCKLIST.search(text):
        # Inappropriate content never reaches the model.
        error = Response(
            {"detail": "Бұл тақырыпты талқыламаймыз. Оқуға қатысты жазыңыз.", "code": "filtered"},
            status=status.HTTP_400_BAD_REQUEST,
        )
        return conversation, text, error
    if limit_reached(request.user):
        return conversation, text, Response(LIMIT_REACHED, status=status.HTTP_429_TOO_MANY_REQUESTS)
    return conversation, text, None


def _save_turn(user, conversation, text, reply) -> dict:
    """Stores the learner's line with its corrections and the tutor's reply; counts the AI call."""
    user_message = Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        text=text,
        correct=reply.learner_correct if reply.learner_correct is not None else not reply.corrections,
        corrections=[c.model_dump() for c in reply.corrections],
    )
    assistant_message = _save_assistant(conversation, reply)
    log_activity(user, chat_messages=1, chat_requests=1)
    return {
        "user_message": MessageSerializer(user_message).data,
        "assistant_message": MessageSerializer(assistant_message).data,
        "finished": conversation.finished,
        "off_topic": reply.off_topic,
        "usage": usage(user),
    }


class SendMessageView(APIView):
    def post(self, request, pk):
        conversation, text, error = _check_send(request, pk)
        if error:
            return error
        history = _history(conversation) + [{"role": "user", "content": text}]
        try:
            reply = ask_tutor(system=_system_prompt(conversation), history=history)
        except TutorUnavailable:
            return unavailable()
        return Response(_save_turn(request.user, conversation, text, reply), status=status.HTTP_201_CREATED)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, cls=DjangoJSONEncoder)}\n\n"


class SendMessageStreamView(APIView):
    """POST …/messages/stream/ — the same as …/messages/, but the tutor's line arrives while it is written.

    Server-sent events: `reply` {text} as the line grows, then `done` with the same body as the plain endpoint,
    or `error` {detail, code, status}. Problems found before the model is asked come back as ordinary JSON errors.
    """

    def post(self, request, pk):
        conversation, text, error = _check_send(request, pk)
        if error:
            return error
        history = _history(conversation) + [{"role": "user", "content": text}]
        system = _system_prompt(conversation)
        user = request.user

        def events():
            reply = None
            saved = failed = False
            try:
                for kind, value in stream_tutor(system=system, history=history):
                    if kind == "reply":
                        yield _sse("reply", {"text": value})
                    else:
                        reply = value
                payload = _save_turn(user, conversation, text, reply)
                saved = True
                yield _sse("done", payload)
            except TutorUnavailable:
                failed = True
                yield _sse("error", {**UNAVAILABLE_BODY, "code": "unavailable", "status": 503})
            finally:
                # The learner closed the page while the tutor was writing: the model was still asked, so the
                # call counts toward the daily limit (otherwise aborting each reply would make it unlimited).
                if not saved and not failed:
                    log_activity(user, chat_requests=1)

        response = StreamingHttpResponse(events(), content_type="text/event-stream; charset=utf-8")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"  # nginx: pass every event on at once
        return response


class SummaryView(APIView):
    """Session summary: sentences written, how many correct, top 3 errors, new words."""

    def get(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
        user_messages = conversation.messages.filter(role=Message.Role.USER)
        errors = Counter()
        examples = {}
        for m in user_messages:
            for c in m.corrections:
                key = (c.get("tense"), c.get("form"), c.get("right"))
                errors[key] += 1
                examples.setdefault(key, c)
        top = []
        for key, count in errors.most_common(3):
            c = examples[key]
            label = " · ".join(x for x in [TENSE_LABELS_KK.get(c.get("tense")), FORM_LABELS_KK.get(c.get("form"))] if x)
            top.append({**c, "count": count, "cell_label_kk": label})

        words = []
        seen = set()
        known = set(UserVocabulary.objects.filter(user=request.user).values_list("vocabulary__word", flat=True))
        for m in conversation.messages.filter(role=Message.Role.ASSISTANT):
            for w in m.new_words:
                if w["word"].lower() not in seen:
                    seen.add(w["word"].lower())
                    words.append({**w, "added": w["word"].lower() in known})

        return Response(
            {
                "written": user_messages.count(),
                "correct": user_messages.filter(correct=True).count(),
                "top_errors": top,
                "new_words": words,
                "usage": usage(request.user),
            }
        )
