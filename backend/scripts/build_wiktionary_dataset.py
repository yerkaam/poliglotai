#!/usr/bin/env python3
"""Step 2: collapse the raw extract into vocabulary/data/wiktionary_en_kk.jsonl (one row per English word).

Usage: python scripts/build_wiktionary_dataset.py /tmp/wikt_kk_raw.jsonl
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "vocabulary" / "data" / "wiktionary_en_kk.jsonl"
MAX_TRANSLATIONS = 3
# Wiktionary gives prepositions context-dependent case endings, not usable one-word translations.
SKIP_POS = {"prep"}


# Topics are assigned by hand in data/topics.json: Wiktionary's own categories proved too noisy
# (they come from rare senses: "foot" → animals, "bishop" → food).
TOPICS_FILE = OUT.parent / "topics.json"


def load_topics() -> dict[str, str]:
    data = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
    return {word: topic for topic, words in data.items() if not topic.startswith("_") for word in words}


def distinct(items):
    seen, out = set(), []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def main(raw_path: str):
    topics = load_topics()
    by_word = defaultdict(list)
    with open(raw_path, encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            by_word[row["word"]].append(row)

    rows = []
    for word, entries in by_word.items():
        # The part of speech with the most Kazakh translations is the word's main meaning here.
        entries = [e for e in entries if e["pos"] not in SKIP_POS]
        if not entries:
            continue
        primary = max(entries, key=lambda e: len(distinct(t["word"] for t in e["kk"])))
        translations = distinct(t["word"] for t in primary["kk"])[:MAX_TRANSLATIONS]
        ipa = primary["ipa"] or next((e["ipa"] for e in entries if e["ipa"]), "")
        rows.append(
            {
                "word": word,
                "rank": primary["rank"],
                "pos": primary["pos"],
                "translation_kk": ", ".join(translations),
                "ipa": ipa,
                "past": (primary.get("past") or [""])[0] if primary["pos"] == "verb" else "",
                "topic": topics.get(word, ""),
            }
        )
    rows.sort(key=lambda r: r["rank"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{len(rows)} words → {OUT}")
    counts = {}
    for row in rows:
        counts[row["topic"] or "(none)"] = counts.get(row["topic"] or "(none)", 0) + 1
    print(dict(sorted(counts.items(), key=lambda kv: -kv[1])))


if __name__ == "__main__":
    main(sys.argv[1])
