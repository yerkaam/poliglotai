"""Active review: the learner proves they remember a word instead of judging it themselves.

The exercise gets harder as the word climbs the stages:
  stages 1-2  choice  — the English word, pick its Kazakh translation out of four;
  stages 3-4  listen  — the word is read aloud, pick how it is written out of four;
  stages 5-6  type    — the Kazakh translation, type the English word.
The server picks the exercise and checks the answer, so the stage and the statistics stay honest.
"""

import random

from vocabulary import forms
from vocabulary.models import Vocabulary

OPTIONS = 4


def mode_for(stage: int) -> str:
    if stage <= 2:
        return "choice"
    if stage <= 4:
        return "listen"
    return "type"


DIFFICULTY = {"choice": 0, "listen": 1, "type": 2}


def allowed(mode: str, stage: int) -> bool:
    """The card may be answered in its stage's mode or a harder one (a word that just slipped back a stage
    is still asked the old way until the screen reloads), never in an easier one."""
    return DIFFICULTY[mode] >= DIFFICULTY[mode_for(stage)]


def _distractors(vocab: Vocabulary, field: str, count: int) -> list[str]:
    """Other words of the same kind (verbs with verbs), course words first: their translations are curated."""
    taken = {getattr(vocab, field).strip().lower()}
    pools = [
        Vocabulary.objects.filter(is_verb=vocab.is_verb, course_step__isnull=False),
        Vocabulary.objects.filter(is_verb=vocab.is_verb),
        Vocabulary.objects.all(),
    ]
    if field == "word":
        # Listening is harder with words that look alike: the same first letter where possible.
        pools.insert(0, pools[0].filter(word__istartswith=vocab.word[:1]))
    result: list[str] = []
    for pool in pools:
        values = list(pool.exclude(id=vocab.id).order_by("?").values_list(field, flat=True)[: count * 4])
        for value in values:
            key = value.strip().lower()
            if value and key not in taken:
                taken.add(key)
                result.append(value)
            if len(result) == count:
                return result
    return result


def build(vocab: Vocabulary, stage: int) -> dict:
    mode = mode_for(stage)
    if mode == "type":
        return {"mode": mode}
    field = "translation_kk" if mode == "choice" else "word"
    options = [getattr(vocab, field), *_distractors(vocab, field, OPTIONS - 1)]
    random.shuffle(options)
    return {"mode": mode, "options": options}


def _distance(a: str, b: str) -> int:
    """Levenshtein distance, enough for one-word answers."""
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def check(vocab: Vocabulary, mode: str, answer: str) -> dict:
    """{"correct": bool, "almost": bool, "right": str}. A single typo in a longer typed word still counts."""
    answer = answer.strip()
    if mode == "choice":
        return {"correct": answer == vocab.translation_kk, "almost": False, "right": vocab.translation_kk}
    if mode == "listen":
        return {"correct": answer.lower() == vocab.word.lower(), "almost": False, "right": vocab.word}
    given, expected = forms.normalize(answer), forms.normalize(vocab.word)
    if given == expected:
        return {"correct": True, "almost": False, "right": vocab.word}
    almost = bool(given) and len(expected) >= 5 and _distance(given, expected) == 1
    return {"correct": almost, "almost": almost, "right": vocab.word}
