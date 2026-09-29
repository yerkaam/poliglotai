#!/usr/bin/env python3
"""Step 2: merge the raw extracts into vocabulary/data/wiktionary_en_kk.jsonl (one row per English word).

Usage: python scripts/build_wiktionary_dataset.py /tmp/wikt_kk_raw.jsonl [/tmp/kk_dict_raw.jsonl …]
Earlier files win: pass the English→Kazakh extract first, the reversed Kazakh dictionary after it.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "vocabulary" / "data" / "wiktionary_en_kk.jsonl"
MAX_TRANSLATIONS = 3
# Wiktionary gives prepositions context-dependent case endings, not usable one-word translations.
SKIP_POS = {"prep"}

# Topics are assigned by hand in data/topics.json. English Wiktionary categories proved too noisy (they
# come from rare senses: "foot" → animals), so they are not used. Kazakh dictionary entries usually have
# one meaning, and their categories are used as a fallback through the keyword table below.
TOPICS_FILE = OUT.parent / "topics.json"
TOPIC_KEYWORDS = [
    ("colors", ["colou?rs?"]),
    ("numbers", ["cardinal numbers", "ordinal numbers", "numerals?"]),
    (
        "food",
        [
            "foods?",
            "beverages?",
            "drinks?",
            "fruits?",
            "vegetables?",
            "meals?",
            "breads?",
            "dairy",
            "meats?",
            "cooking",
            "sweets?",
            "desserts?",
            "spices?",
            "nuts?",
            "condiments?",
            "cuisine",
            "soups?",
            "berries",
            "cereals?",
            "dishes",
        ],
    ),
    (
        "animals",
        [
            "animals?",
            "mammals?",
            "birds?",
            "fish",
            "insects?",
            "reptiles?",
            "livestock",
            "rodents?",
            "felids?",
            "canids?",
            "horses?",
            "cattle",
            "amphibians?",
        ],
    ),
    ("clothes", ["clothing", "footwear", "jewelry", "jewellery", "headwear", "garments?"]),
    ("it", ["computing", "internet", "software", "programming", "telecommunications?", "electronics"]),
    (
        "work",
        [
            "occupations?",
            "professions?",
            "business",
            "money",
            "currenc(y|ies)",
            "finance",
            "economics",
            "trade",
            "commerce",
            "banking",
        ],
    ),
    (
        "travel",
        [
            "transport",
            "vehicles?",
            "travel",
            "tourism",
            "aviation",
            "aircraft",
            "automobiles?",
            "ships?",
            "roads?",
            "countries",
            "cities",
        ],
    ),
    # not "Months": Kazakh month names double as nouns (қазан = October and cauldron)
    ("time", ["units of time", "times of day", "days of the week", "seasons"]),
    ("family", ["family", "family members", "kinship", "marriage"]),
    ("body", ["anatomy", "body parts", "medicine", "diseases?", "health", "organs?", "teeth"]),
    ("feelings", ["emotions?"]),
    ("home", ["furniture", "rooms?", "buildings?", "household", "kitchenware", "tools?", "containers?"]),
    (
        "nature",
        [
            "weather",
            "meteorology",
            "plants?",
            "trees?",
            "flowers?",
            "landforms?",
            "minerals?",
            "astronomy",
            "geography",
        ],
    ),
    ("hobbies", ["sports?", "games?", "music", "musical instruments?", "dances?", "films?", "art"]),
    ("education", ["education", "schools?", "linguistics", "grammar", "mathematics", "writing", "literature"]),
]
_TOPIC_RE = [(slug, re.compile(r"^(" + "|".join(kws) + r")$", re.IGNORECASE)) for slug, kws in TOPIC_KEYWORDS]
_ORDER = {slug: i for i, (slug, _) in enumerate(TOPIC_KEYWORDS)}
META = re.compile(r"Kazakh|English|Pages|terms|entries|Requests", re.IGNORECASE)


def load_topics() -> dict[str, str]:
    data = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
    return {word: topic for topic, words in data.items() if not topic.startswith("_") for word in words}


def category_topic(entry) -> str:
    """Topic from a Kazakh dictionary entry's categories ("Mammals" → animals); '' when none match."""
    if entry["pos"] == "num":
        return "numbers"
    cats = [c for sense in entry.get("categories", [])[:1] for c in sense if not META.search(c)]
    found = {slug for cat in cats for slug, rx in _TOPIC_RE if rx.match(cat)}
    return min(found, key=_ORDER.get) if found else ""


def distinct(items):
    seen, out = set(), []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def main(*raw_paths: str):
    topics = load_topics()
    by_word: dict[str, list] = defaultdict(list)
    source_of: dict[str, str] = {}
    for path in raw_paths:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                word = row["word"]
                if word in source_of and source_of[word] != path:
                    continue  # an earlier, more reliable source already has this word
                source_of[word] = path
                by_word[word].append(row)

    rows = []
    for word, entries in by_word.items():
        entries = [e for e in entries if e["pos"] not in SKIP_POS]
        if not entries:
            continue
        # The part of speech with the most Kazakh translations is the word's main meaning here.
        primary = max(entries, key=lambda e: len(distinct(t["word"] for t in e["kk"])))
        translations = distinct(t["word"] for t in primary["kk"])[:MAX_TRANSLATIONS]
        ipa = primary["ipa"] or next((e["ipa"] for e in entries if e["ipa"]), "")
        from_kk_dictionary = primary.get("source") == "kk-dictionary"
        rows.append(
            {
                "word": word,
                "rank": primary["rank"],
                "pos": primary["pos"],
                "translation_kk": ", ".join(translations),
                "ipa": ipa,
                "past": (primary.get("past") or [""])[0] if primary["pos"] == "verb" else "",
                "topic": topics.get(word) or (category_topic(primary) if from_kk_dictionary else ""),
                "via": "kk" if from_kk_dictionary else "en",
            }
        )
    rows.sort(key=lambda r: r["rank"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{len(rows)} words → {OUT}")
    print("sources:", dict(Counter(r["via"] for r in rows)))
    print("topics:", dict(Counter(r["topic"] or "(none)" for r in rows).most_common()))


if __name__ == "__main__":
    main(*sys.argv[1:])
