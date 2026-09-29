"""English–Kazakh words from Wiktionary.

`data/wiktionary_en_kk.jsonl` is extracted from the English Wiktionary (via kaikki.org / wiktextract):
frequent English words that have Kazakh translations. Licence: CC BY-SA 4.0 — the site must credit
Wiktionary where these translations are shown. The 40 hand-written course verbs are never overwritten.
"""

import json
from pathlib import Path

from .forms import past_simple

DATA_FILE = Path(__file__).parent / "data" / "wiktionary_en_kk.jsonl"

# Verbs the basic table cannot conjugate with do/does/did.
# Past tense of common irregular verbs, for rows that come without forms (the reversed Kazakh dictionary).
IRREGULAR_PAST = {
    "arise": "arose",
    "awake": "awoke",
    "bear": "bore",
    "beat": "beat",
    "become": "became",
    "begin": "began",
    "bend": "bent",
    "bet": "bet",
    "bind": "bound",
    "bite": "bit",
    "bleed": "bled",
    "blow": "blew",
    "break": "broke",
    "breed": "bred",
    "bring": "brought",
    "build": "built",
    "burn": "burnt",
    "burst": "burst",
    "buy": "bought",
    "cast": "cast",
    "catch": "caught",
    "choose": "chose",
    "cling": "clung",
    "come": "came",
    "cost": "cost",
    "creep": "crept",
    "cut": "cut",
    "deal": "dealt",
    "dig": "dug",
    "draw": "drew",
    "dream": "dreamt",
    "drink": "drank",
    "drive": "drove",
    "eat": "ate",
    "fall": "fell",
    "feed": "fed",
    "feel": "felt",
    "fight": "fought",
    "find": "found",
    "flee": "fled",
    "fling": "flung",
    "fly": "flew",
    "forbid": "forbade",
    "forget": "forgot",
    "forgive": "forgave",
    "freeze": "froze",
    "get": "got",
    "give": "gave",
    "go": "went",
    "grind": "ground",
    "grow": "grew",
    "hang": "hung",
    "hear": "heard",
    "hide": "hid",
    "hit": "hit",
    "hold": "held",
    "hurt": "hurt",
    "keep": "kept",
    "kneel": "knelt",
    "know": "knew",
    "lay": "laid",
    "lead": "led",
    "lean": "leant",
    "leap": "leapt",
    "learn": "learnt",
    "leave": "left",
    "lend": "lent",
    "let": "let",
    "lie": "lay",
    "light": "lit",
    "lose": "lost",
    "make": "made",
    "mean": "meant",
    "meet": "met",
    "pay": "paid",
    "put": "put",
    "quit": "quit",
    "read": "read",
    "ride": "rode",
    "ring": "rang",
    "rise": "rose",
    "run": "ran",
    "say": "said",
    "see": "saw",
    "seek": "sought",
    "sell": "sold",
    "send": "sent",
    "set": "set",
    "sew": "sewed",
    "shake": "shook",
    "shine": "shone",
    "shoot": "shot",
    "show": "showed",
    "shrink": "shrank",
    "shut": "shut",
    "sing": "sang",
    "sink": "sank",
    "sit": "sat",
    "sleep": "slept",
    "slide": "slid",
    "smell": "smelt",
    "speak": "spoke",
    "speed": "sped",
    "spell": "spelt",
    "spend": "spent",
    "spill": "spilt",
    "spin": "spun",
    "spit": "spat",
    "split": "split",
    "spread": "spread",
    "spring": "sprang",
    "stand": "stood",
    "steal": "stole",
    "stick": "stuck",
    "sting": "stung",
    "stink": "stank",
    "strike": "struck",
    "swear": "swore",
    "sweep": "swept",
    "swim": "swam",
    "swing": "swung",
    "take": "took",
    "teach": "taught",
    "tear": "tore",
    "tell": "told",
    "think": "thought",
    "throw": "threw",
    "understand": "understood",
    "wake": "woke",
    "wear": "wore",
    "weep": "wept",
    "win": "won",
    "wind": "wound",
    "write": "wrote",
}

NOT_TABLE_VERBS = {
    "be",
    "can",
    "could",
    "may",
    "might",
    "must",
    "shall",
    "should",
    "will",
    "would",
    "ought",
    "need",
    "dare",
    "do",
    "have",
    "used",
}
# Thematic dictionaries (spec, second queue). Slugs are stored in Vocabulary.topic.
TOPICS_KK = {
    "food": "Тамақ",
    "travel": "Саяхат",
    "work": "Жұмыс",
    "it": "IT",
    "family": "Отбасы және адамдар",
    "body": "Дене және денсаулық",
    "clothes": "Киім",
    "colors": "Түстер",
    "numbers": "Сандар",
    "time": "Уақыт",
    "nature": "Табиғат және ауа райы",
    "home": "Үй",
    "animals": "Жануарлар",
    "hobbies": "Спорт және хобби",
    "education": "Білім",
    "feelings": "Сезімдер",
    "general": "Жалпы сөздер",
}
RANK_OFFSET = 100  # keeps the course verbs (rank 1–40) first in lists
MAX_RANK = 32767  # frequency_rank is a smallint


def load(Vocabulary, path: Path = DATA_FILE, limit: int | None = None) -> dict:
    created = updated = skipped = 0
    course_words = set(Vocabulary.objects.exclude(source="wiktionary").values_list("word", flat=True))
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    rows.sort(key=lambda r: r["rank"])
    for row in rows[:limit]:
        word = row["word"]
        if word in course_words:
            skipped += 1
            continue
        is_verb = row["pos"] == "verb" and word not in NOT_TABLE_VERBS
        past = row.get("past") or IRREGULAR_PAST.get(word, "")
        irregular = bool(is_verb and past and past != past_simple(word))
        _, was_created = Vocabulary.objects.update_or_create(
            word=word,
            defaults={
                "translation_kk": row["translation_kk"][:120],
                "ipa": row.get("ipa", "")[:60],
                "pos": row["pos"],
                "is_verb": is_verb,
                "past_form": past if irregular else "",
                "is_irregular": irregular,
                "topic": row.get("topic") or "general",
                "frequency_rank": min(RANK_OFFSET + row["rank"], MAX_RANK),
                "source": "wiktionary",
                "course_step": None,
            },
        )
        created += was_created
        updated += not was_created
    return {"created": created, "updated": updated, "skipped": skipped}
