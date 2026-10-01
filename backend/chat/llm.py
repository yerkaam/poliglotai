"""The AI tutor. Only Django talks to the LLM; the API key stays in the server environment.

The model answers in a fixed structure: the reply, its Kazakh translation, an answer template,
corrections of the learner's last sentence (each tied to a cell of the verb table) and new words.
Without ANTHROPIC_API_KEY an offline tutor answers instead, so the app works in development.
"""

import json
import logging
import re
import time
from collections.abc import Iterator
from typing import Literal

import anthropic
from django.conf import settings
from pydantic import BaseModel, Field

from vocabulary import forms

logger = logging.getLogger(__name__)


class Correction(BaseModel):
    wrong: str = Field(description="The learner's wrong fragment, as written")
    right: str = Field(description="The corrected fragment or sentence")
    explanation_kk: str = Field(description="One short sentence in Kazakh explaining the rule")
    verb: str | None = Field(description="Base form of the verb involved, e.g. 'buy', or null")
    pronoun: Literal["I", "you", "we", "they", "he", "she"] | None = Field(
        description="Subject pronoun of the table cell, or null"
    )
    tense: Literal["future", "present", "past"] | None = Field(description="Table row, or null")
    form: Literal["question", "affirmative", "negative"] | None = Field(description="Table column, or null")


class NewWord(BaseModel):
    word: str = Field(description="An English word from your reply the learner probably does not know")
    translation_kk: str


class TutorReply(BaseModel):
    reply: str = Field(description="Your next line in English, 1–2 short simple sentences")
    reply_kk: str = Field(description="Kazakh translation of your reply")
    answer_template: str = Field(description="A short English template the learner could use to answer")
    learner_correct: bool | None = Field(
        description="Was the learner's last sentence grammatically correct? null for the opening line"
    )
    corrections: list[Correction]
    new_words: list[NewWord]
    finished: bool = Field(description="True when the scenario has reached its natural end")
    off_topic: bool = Field(description="True if the learner asked for something outside study and daily life")


SYSTEM_PROMPT = """You are PoliglotAi, a friendly English conversation partner for adult Kazakh-speaking \
beginners (level {level}). All explanations, translations and hints are in Kazakh (Cyrillic).

The learner knows only these structures: the basic verb table — Future Simple, Present Simple and \
Past Simple, each as question, affirmative and negative (will/won't, do/does/don't/doesn't, did/didn't). \
Course steps opened so far: {steps}.
Also completed: {grammar}.
Verbs they are learning now: {verbs}.

Speak only at this level: short sentences, the structures above, mostly the verbs above and very common \
everyday words.{forbidden}

{mode_rules}

How to correct:
- First answer the meaning of what the learner wrote so the conversation keeps going. Put corrections \
only in `corrections`, never inside `reply`.
- Correct only real grammar or word errors in the learner's LAST message. Ignore capital letters and \
punctuation. If it is correct, set learner_correct=true and corrections=[].
- Tie each correction to the verb table: verb (base form), pronoun, tense, form. Example: "I buyed" → \
right "I bought", explanation_kk "buy — бұрыс етістік: өткен шақта bought.", verb "buy", pronoun "I", \
tense "past", form "affirmative".
- new_words: at most 2 words from your reply that are outside the learner's verb list and likely new.

Stay on study and everyday situations (introductions, café, travel, shopping, work). If the learner \
goes elsewhere or writes something inappropriate, set off_topic=true and gently bring them back in \
one simple English sentence."""

MODE_RULES = {
    "dialog": (
        "Mode: situational dialog. {scenario} Lead the conversation and ask one question at a time. "
        "The dialog lasts about {turns} of your lines; after that, close it kindly and set finished=true."
    ),
    "builder": (
        "Mode: phrase builder. Each turn give the learner one task in Kazakh inside `reply_kk` and in simple "
        'English inside `reply`, e.g. "Ask me what I did yesterday". The task must require one cell of the '
        "table (a tense and a form). Then check their sentence against that cell."
    ),
    "free": (
        "Mode: free conversation. The learner writes about anything from daily life; you answer in simple "
        "sentences and ask a follow-up question."
    ),
}

KICKOFF = "(The lesson starts. Write your first line.)"

BLOCKLIST = re.compile(r"\b(fuck|shit|bitch|porn|sex|kill|drugs?)\b", re.IGNORECASE)


UNAVAILABLE_TEXT = "AI-әңгімелесуші қазір қолжетімсіз. Бір минуттан кейін қайталаңыз."


class TutorUnavailable(Exception):
    pass


# Structures the tutor must avoid until the learner has completed the course step that teaches them.
LATER_STRUCTURES = {8: "Continuous forms", 9: "Perfect forms", 12: "the passive voice"}


def build_system_prompt(
    *,
    level: str,
    steps: list[str],
    verbs: list[str],
    mode: str,
    scenario=None,
    grammar: list[str] | None = None,
    done_numbers: set[int] | None = None,
) -> str:
    rules = MODE_RULES[mode].format(
        scenario=f"Scenario: {scenario.brief_en}" if scenario else "",
        turns=scenario.max_turns if scenario else 8,
    )
    done = done_numbers or set()
    forbidden = [name for number, name in LATER_STRUCTURES.items() if number not in done]
    return SYSTEM_PROMPT.format(
        level=level,
        steps=", ".join(steps) or "none yet",
        grammar="; ".join(grammar or []) or "nothing beyond the verb table yet",
        verbs=", ".join(verbs) or "the 40 most common verbs",
        forbidden=f" Never use {', '.join(forbidden)}." if forbidden else "",
        mode_rules=rules,
    )


def _request(system: str, history: list[dict]) -> dict:
    # The API needs a user turn first; the stored dialog starts with the tutor's opening line.
    return {
        "model": settings.CHAT_MODEL,
        "max_tokens": 16000,
        "system": system,
        "messages": [{"role": "user", "content": KICKOFF}, *history],
        "output_format": TutorReply,
        "output_config": {"effort": settings.CHAT_EFFORT},
        # If the main model declines, the API re-runs the request on a fallback model.
        "betas": ["server-side-fallback-2026-07-01"],
        "fallbacks": "default",
    }


def _client():
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY, max_retries=2, timeout=60)


def _unavailable(exc: Exception) -> TutorUnavailable:
    if isinstance(exc, anthropic.RateLimitError):
        logger.warning("LLM rate limited: %s", exc)
        return TutorUnavailable("rate_limited")
    if isinstance(exc, anthropic.APIStatusError):
        logger.error("LLM API error %s: %s", exc.status_code, exc)
        return TutorUnavailable("api_error")
    logger.error("LLM connection error: %s", exc)
    return TutorUnavailable("connection")


DECLINED = TutorReply(
    reply="Let's talk about something else. What did you do today?",
    reply_kk="Басқа тақырып туралы сөйлесейік. Бүгін не істедіңіз?",
    answer_template="Today I …",
    learner_correct=None,
    corrections=[],
    new_words=[],
    finished=False,
    off_topic=True,
)


def ask_tutor(*, system: str, history: list[dict]) -> TutorReply:
    """history: [{"role": "user"|"assistant", "content": str}, …] ending with the learner's line."""
    if not settings.ANTHROPIC_API_KEY:
        return offline_reply(history)
    try:
        response = _client().beta.messages.parse(**_request(system, history))
    except (anthropic.APIStatusError, anthropic.APIConnectionError) as exc:
        raise _unavailable(exc) from exc
    if response.stop_reason == "refusal" or response.parsed_output is None:
        return DECLINED
    return response.parsed_output


def stream_tutor(*, system: str, history: list[dict]) -> Iterator[tuple[str, object]]:
    """Like ask_tutor, but yields ("reply", text so far) while the model writes, then ("final", TutorReply).

    The model writes the TutorReply JSON with `reply` first, so the learner sees the tutor's line appear
    long before the translation, corrections and new words are ready.
    """
    if not settings.ANTHROPIC_API_KEY:
        reply = offline_reply(history)
        words = reply.reply.split(" ")
        for i in range(1, len(words) + 1):
            time.sleep(0.04)  # the offline tutor "types" too, so the screen behaves as in production
            yield "reply", " ".join(words[:i])
        yield "final", reply
        return
    try:
        with _client().beta.messages.stream(**_request(system, history)) as stream:
            text, shown = "", ""
            for event in stream:
                if event.type == "content_block_start" and event.content_block.type == "text":
                    text = ""  # a fallback model starts its own JSON from scratch
                elif event.type == "content_block_delta" and event.delta.type == "text_delta":
                    text += event.delta.text
                    current = partial_string(text, "reply")
                    if current and current != shown:
                        shown = current
                        yield "reply", current
            response = stream.get_final_message()
    except (anthropic.APIStatusError, anthropic.APIConnectionError) as exc:
        raise _unavailable(exc) from exc
    if response.stop_reason == "refusal" or response.parsed_output is None:
        yield "final", DECLINED
    else:
        yield "final", response.parsed_output


_FIELD = re.compile(r'"(?P<name>[a-z_]+)"\s*:\s*"')


def partial_string(text: str, field: str) -> str:
    """The value of a top-level string field in JSON that may still be incomplete ("" if not started)."""
    for match in _FIELD.finditer(text):
        if match.group("name") != field:
            continue
        raw = text[match.end() :]
        end, escaped = None, False
        for i, ch in enumerate(raw):
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                end = i
                break
        body = raw if end is None else raw[:end]
        if end is None:
            # Cut a half-received escape (\ or \u12) so the decoder never sees it.
            body = re.sub(r"\\(u[0-9a-fA-F]{0,3})?$", "", body)
        try:
            return json.loads(f'"{body}"')
        except json.JSONDecodeError:
            return body
    return ""


# ---- offline tutor (no API key) ----------------------------------------------------

_OFFLINE_LINES = [
    ("What did you do yesterday?", "Кеше не істедіңіз?", "Yesterday I …"),
    ("Do you like coffee?", "Сізге кофе ұнай ма?", "Yes, I like … / No, I don't like …"),
    ("Where do you work?", "Қайда жұмыс істейсіз?", "I work in …"),
    ("What will you do tomorrow?", "Ертең не істейсіз?", "Tomorrow I will …"),
    ("Did you watch TV yesterday?", "Кеше теледидар көрдіңіз бе?", "Yes, I did. / No, I didn't."),
]


def offline_reply(history: list[dict]) -> TutorReply:
    from vocabulary.seed import VERBS

    learner = history[-1]["content"] if history and history[-1]["role"] == "user" else None
    corrections: list[Correction] = []
    if learner:
        lowered = learner.lower()
        for word, _kk, _ipa, past, *_ in VERBS:
            if not past:
                continue
            wrong = "".join(forms.regular_past(word))
            if re.search(rf"\b{wrong}\b", lowered):
                corrections.append(
                    Correction(
                        wrong=wrong,
                        right=past,
                        explanation_kk=f"{word} — бұрыс етістік: өткен шақта {past}.",
                        verb=word,
                        pronoun=None,
                        tense="past",
                        form="affirmative",
                    )
                )
            if re.search(rf"\bdid(n't| not)? \w+ {past}\b", lowered):
                corrections.append(
                    Correction(
                        wrong=past,
                        right=word,
                        explanation_kk="did / didn't кейін етістік бастапқы формада тұрады.",
                        verb=word,
                        pronoun=None,
                        tense="past",
                        form="question" if lowered.rstrip().endswith("?") else "negative",
                    )
                )
    turn = sum(1 for m in history if m["role"] == "assistant")
    reply, reply_kk, template = _OFFLINE_LINES[turn % len(_OFFLINE_LINES)]
    prefix = ("Nice! " if not corrections else "I see. ") if learner else "Hi! "
    return TutorReply(
        reply=prefix + reply,
        reply_kk=reply_kk,
        answer_template=template,
        learner_correct=(not corrections) if learner else None,
        corrections=corrections,
        new_words=[NewWord(word="yesterday", translation_kk="кеше")] if turn == 0 else [],
        finished=turn >= 7,
        off_topic=False,
    )
