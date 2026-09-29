"""Builds the nine sentences of the basic verb table.

build(pronoun, verb, tense, form) is the single source of truth for the table screen and
for checking answers in the trainer. A sentence is returned as parts so the UI can colour
auxiliaries and endings.
"""

import re
from dataclasses import dataclass

PRONOUNS = ["I", "you", "we", "they", "he", "she"]
TENSES = ["future", "present", "past"]
FORMS = ["question", "affirmative", "negative"]
THIRD_PERSON = {"he", "she"}
VOWELS = set("aeiou")

PRONOUN_LABELS_KK = {
    "I": "мен",
    "you": "сен / сіз",
    "we": "біз",
    "they": "олар",
    "he": "ол (ер)",
    "she": "ол (әйел)",
}
TENSE_LABELS_KK = {"future": "Келер шақ", "present": "Осы шақ", "past": "Өткен шақ"}
FORM_LABELS_KK = {"question": "сұрақ", "affirmative": "болымды", "negative": "болымсыз"}


@dataclass(frozen=True)
class Part:
    text: str
    kind: str = "plain"  # plain | aux | ending | irregular

    def as_dict(self):
        return {"text": self.text, "kind": self.kind}


def third_person(verb: str) -> tuple[str, str]:
    """Returns (stem, ending) for he/she in the present: buys, watches, studies, has."""
    if verb == "have":
        return "ha", "s"
    if verb in {"do", "go"}:
        return verb, "es"
    if verb.endswith(("s", "sh", "ch", "x", "z", "o")):
        return verb, "es"
    if len(verb) > 1 and verb.endswith("y") and verb[-2] not in VOWELS:
        return verb[:-1], "ies"
    return verb, "s"


def _is_short_cvc(verb: str) -> bool:
    """stop → stopped, plan → planned. Only one vowel group, ends consonant-vowel-consonant."""
    if len(verb) < 3 or verb[-1] in VOWELS | {"w", "x", "y"}:
        return False
    vowel_groups = len(re.findall(r"[aeiou]+", verb))
    return vowel_groups == 1 and verb[-2] in VOWELS and verb[-3] not in VOWELS


def regular_past(verb: str) -> tuple[str, str]:
    """Returns (stem, ending) for a regular verb: worked, liked, studied, stopped."""
    if verb.endswith("e"):
        return verb, "d"
    if len(verb) > 1 and verb.endswith("y") and verb[-2] not in VOWELS:
        return verb[:-1], "ied"
    if _is_short_cvc(verb):
        return verb + verb[-1], "ed"
    return verb, "ed"


def past_simple(verb: str, past_form: str = "") -> str:
    if past_form:
        return past_form
    stem, ending = regular_past(verb)
    return stem + ending


def build(
    pronoun: str, verb: str, tense: str, form: str, past_form: str = "", is_irregular: bool = False
) -> list[Part]:
    if pronoun not in PRONOUNS:
        raise ValueError(f"Unknown pronoun: {pronoun}")
    if tense not in TENSES:
        raise ValueError(f"Unknown tense: {tense}")
    if form not in FORMS:
        raise ValueError(f"Unknown form: {form}")

    third = pronoun in THIRD_PERSON
    subject = pronoun

    if tense == "future":
        if form == "question":
            return [Part("Will", "aux"), Part(f" {subject} {verb}?")]
        aux = "will" if form == "affirmative" else "won't"
        return [Part(f"{_cap(subject)} "), Part(aux, "aux"), Part(f" {verb}.")]

    if tense == "present":
        do = "does" if third else "do"
        if form == "question":
            return [Part(_cap(do), "aux"), Part(f" {subject} {verb}?")]
        if form == "negative":
            return [Part(f"{_cap(subject)} "), Part(f"{do}n't", "aux"), Part(f" {verb}.")]
        if third:
            stem, ending = third_person(verb)
            return [Part(f"{_cap(subject)} {stem}"), Part(ending, "ending"), Part(".")]
        return [Part(f"{_cap(subject)} {verb}.")]

    # past
    if form == "question":
        return [Part("Did", "aux"), Part(f" {subject} {verb}?")]
    if form == "negative":
        return [Part(f"{_cap(subject)} "), Part("didn't", "aux"), Part(f" {verb}.")]
    if is_irregular or past_form:
        return [Part(f"{_cap(subject)} "), Part(past_simple(verb, past_form), "irregular"), Part(".")]
    stem, ending = regular_past(verb)
    return [Part(f"{_cap(subject)} {stem}"), Part(ending, "ending"), Part(".")]


def sentence(parts: list[Part]) -> str:
    return "".join(p.text for p in parts)


def build_for(vocab, pronoun: str, tense: str, form: str) -> list[Part]:
    return build(pronoun, vocab.word, tense, form, vocab.past_form, vocab.is_irregular)


def table(vocab, pronoun: str) -> list[dict]:
    """All nine cells for one pronoun and verb, row by row (future, present, past)."""
    cells = []
    for tense in TENSES:
        for form in FORMS:
            parts = build_for(vocab, pronoun, tense, form)
            cells.append(
                {
                    "tense": tense,
                    "form": form,
                    "text": sentence(parts),
                    "parts": [p.as_dict() for p in parts],
                }
            )
    return cells


def _cap(word: str) -> str:
    return word if word == "I" else word[:1].upper() + word[1:]


# ---- answer checking (trainer) -------------------------------------------------------

CONTRACTIONS = {
    "wont": "will not",
    "dont": "do not",
    "doesnt": "does not",
    "didnt": "did not",
}


def normalize(text: str) -> str:
    """Case, punctuation and spacing do not matter; full forms equal contractions (won't, wont)."""
    text = text.lower().replace("’", "").replace("'", "").replace("`", "")
    text = re.sub(r"[^a-z ]+", " ", text)
    return " ".join(CONTRACTIONS.get(token, token) for token in text.split())


def is_correct(answer: str, expected: str) -> bool:
    return normalize(answer) == normalize(expected)
