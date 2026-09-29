"""The AI tutor. Only Django talks to the LLM; the API key stays in the server environment.

The model answers in a fixed structure: the reply, its Kazakh translation, an answer template,
corrections of the learner's last sentence (each tied to a cell of the verb table) and new words.
Without ANTHROPIC_API_KEY an offline tutor answers instead, so the app works in development.
"""

import logging
import re
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
Completed course steps: {steps}.
Verbs they are learning now: {verbs}.

Speak only at this level: short sentences, these three tenses, mostly the verbs above and very common \
everyday words. Never use Continuous, Perfect or passive forms.

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


class TutorUnavailable(Exception):
    pass


def build_system_prompt(*, level: str, steps: list[str], verbs: list[str], mode: str, scenario=None) -> str:
    rules = MODE_RULES[mode].format(
        scenario=f"Scenario: {scenario.brief_en}" if scenario else "",
        turns=scenario.max_turns if scenario else 8,
    )
    return SYSTEM_PROMPT.format(
        level=level,
        steps=", ".join(steps) or "none yet",
        verbs=", ".join(verbs) or "the 40 most common verbs",
        mode_rules=rules,
    )


def ask_tutor(*, system: str, history: list[dict]) -> TutorReply:
    """history: [{"role": "user"|"assistant", "content": str}, …] ending with the learner's line."""
    if not settings.ANTHROPIC_API_KEY:
        return offline_reply(history)

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY, max_retries=2, timeout=60)
    # The API needs a user turn first; the stored dialog starts with the tutor's opening line.
    messages = [{"role": "user", "content": KICKOFF}, *history]
    try:
        response = client.beta.messages.parse(
            model=settings.CHAT_MODEL,
            max_tokens=16000,
            system=system,
            messages=messages,
            output_format=TutorReply,
            output_config={"effort": settings.CHAT_EFFORT},
            # If the main model declines, the API re-runs the request on a fallback model.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.RateLimitError as exc:
        logger.warning("LLM rate limited: %s", exc)
        raise TutorUnavailable("rate_limited") from exc
    except anthropic.APIStatusError as exc:
        logger.error("LLM API error %s: %s", exc.status_code, exc)
        raise TutorUnavailable("api_error") from exc
    except anthropic.APIConnectionError as exc:
        logger.error("LLM connection error: %s", exc)
        raise TutorUnavailable("connection") from exc

    if response.stop_reason == "refusal" or response.parsed_output is None:
        return TutorReply(
            reply="Let's talk about something else. What did you do today?",
            reply_kk="Басқа тақырып туралы сөйлесейік. Бүгін не істедіңіз?",
            answer_template="Today I …",
            learner_correct=None,
            corrections=[],
            new_words=[],
            finished=False,
            off_topic=True,
        )
    return response.parsed_output


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
