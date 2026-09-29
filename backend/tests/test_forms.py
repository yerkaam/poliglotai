"""All 54 forms (6 pronouns × 9 cells) for every verb, checked against hand-written forms."""

import pytest

from vocabulary import forms
from vocabulary.models import Vocabulary

# Hand-written third-person and past forms, independent of the spelling rules in forms.py.
THIRD = {
    "have": "has",
    "do": "does",
    "say": "says",
    "go": "goes",
    "get": "gets",
    "make": "makes",
    "know": "knows",
    "think": "thinks",
    "take": "takes",
    "see": "sees",
    "come": "comes",
    "want": "wants",
    "look": "looks",
    "use": "uses",
    "find": "finds",
    "give": "gives",
    "tell": "tells",
    "work": "works",
    "call": "calls",
    "try": "tries",
    "ask": "asks",
    "need": "needs",
    "study": "studies",
    "leave": "leaves",
    "live": "lives",
    "love": "loves",
    "like": "likes",
    "help": "helps",
    "start": "starts",
    "play": "plays",
    "buy": "buys",
    "speak": "speaks",
    "read": "reads",
    "write": "writes",
    "open": "opens",
    "close": "closes",
    "eat": "eats",
    "drink": "drinks",
    "learn": "learns",
    "watch": "watches",
}
PAST = {
    "have": "had",
    "do": "did",
    "say": "said",
    "go": "went",
    "get": "got",
    "make": "made",
    "know": "knew",
    "think": "thought",
    "take": "took",
    "see": "saw",
    "come": "came",
    "want": "wanted",
    "look": "looked",
    "use": "used",
    "find": "found",
    "give": "gave",
    "tell": "told",
    "work": "worked",
    "call": "called",
    "try": "tried",
    "ask": "asked",
    "need": "needed",
    "study": "studied",
    "leave": "left",
    "live": "lived",
    "love": "loved",
    "like": "liked",
    "help": "helped",
    "start": "started",
    "play": "played",
    "buy": "bought",
    "speak": "spoke",
    "read": "read",
    "write": "wrote",
    "open": "opened",
    "close": "closed",
    "eat": "ate",
    "drink": "drank",
    "learn": "learned",
    "watch": "watched",
}


def expected(pronoun: str, verb: str, tense: str, form: str) -> str:
    third = pronoun in ("he", "she")
    subj = pronoun if pronoun == "I" else pronoun.capitalize()
    if tense == "future":
        return {
            "question": f"Will {pronoun} {verb}?",
            "affirmative": f"{subj} will {verb}.",
            "negative": f"{subj} won't {verb}.",
        }[form]
    if tense == "present":
        do = "does" if third else "do"
        return {
            "question": f"{do.capitalize()} {pronoun} {verb}?",
            "affirmative": f"{subj} {THIRD[verb] if third else verb}.",
            "negative": f"{subj} {do}n't {verb}.",
        }[form]
    return {
        "question": f"Did {pronoun} {verb}?",
        "affirmative": f"{subj} {PAST[verb]}.",
        "negative": f"{subj} didn't {verb}.",
    }[form]


@pytest.mark.django_db
def test_every_verb_has_all_54_forms_right():
    verbs = list(Vocabulary.objects.filter(is_verb=True))
    assert len(verbs) == 40
    assert {v.word for v in verbs} == set(THIRD)
    checked = 0
    for vocab in verbs:
        for pronoun in forms.PRONOUNS:
            cells = forms.table(vocab, pronoun)
            assert len(cells) == 9
            for cell in cells:
                assert cell["text"] == expected(pronoun, vocab.word, cell["tense"], cell["form"]), (
                    vocab.word,
                    pronoun,
                    cell["tense"],
                    cell["form"],
                )
                checked += 1
    assert checked == 40 * 54


@pytest.mark.django_db
def test_irregular_verbs_never_get_ed():
    for vocab in Vocabulary.objects.filter(is_irregular=True):
        for pronoun in forms.PRONOUNS:
            text = forms.sentence(forms.build_for(vocab, pronoun, "past", "affirmative"))
            assert not text.rstrip(".").endswith(vocab.word + "ed"), text


def test_parts_highlight_auxiliaries_and_endings():
    parts = forms.build("she", "watch", "present", "affirmative")
    assert [p.as_dict() for p in parts] == [
        {"text": "She watch", "kind": "plain"},
        {"text": "es", "kind": "ending"},
        {"text": ".", "kind": "plain"},
    ]
    assert forms.build("I", "buy", "past", "affirmative", past_form="bought")[1].kind == "irregular"
    assert forms.build("they", "go", "future", "negative")[1].as_dict() == {"text": "won't", "kind": "aux"}


@pytest.mark.parametrize(
    "verb,past",
    [
        ("stop", "stopped"),
        ("plan", "planned"),
        ("open", "opened"),
        ("visit", "visited"),
        ("study", "studied"),
        ("play", "played"),
        ("like", "liked"),
    ],
)
def test_regular_past_spelling(verb, past):
    assert forms.past_simple(verb) == past


@pytest.mark.parametrize(
    "answer,ok",
    [
        ("she didn't buy", True),
        ("She did not buy.", True),
        ("SHE   DIDN’T BUY!!", True),
        ("She didnt buy", True),
        ("She don't buy", False),
        ("She didn't bought", False),
    ],
)
def test_answer_normalisation(answer, ok):
    assert forms.is_correct(answer, "She didn't buy.") is ok


def test_will_not_equals_wont():
    assert forms.is_correct("I will not go", "I won't go.")
