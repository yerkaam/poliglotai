#!/usr/bin/env python3
"""Second source: Wiktionary's Kazakh entries (Kazakh word → English meaning), reversed to English → Kazakh.

Usage:
  curl -s https://kaikki.org/dictionary/Kazakh/kaikki.org-dictionary-Kazakh.jsonl \
    | python scripts/extract_kazakh_dictionary.py > /tmp/kk_dict_raw.jsonl
Writes rows in the same format as extract_wiktionary_kk.py, so build_wiktionary_dataset.py can merge them.
Needs `pip install wordfreq`.
"""

import json
import re
import sys
from collections import defaultdict

from wordfreq import top_n_list, zipf_frequency

MIN_ZIPF = 3.0  # everyday English words only (≈ top 25–30k)
# The most frequent words (the, at, may, will, go…) are too polysemous to reverse reliably;
# the English→Kazakh source covers them.
MIN_RANK = 1000
RANK = {w: i for i, w in enumerate(top_n_list("en", 60000), start=1)}
CYR = re.compile(r"^[А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі -]+$")
POS = {"noun", "verb", "adj", "adv", "num", "pron", "intj", "conj"}
NOT_A_MEANING = re.compile(
    r"spelling of|form of|letter of|plural of|alternative|abbreviation|genitive|dative|accusative|locative|"
    r"ablative|instrumental|possessive|obsolete|archaic|synonym of|initialism|clipping",
    re.IGNORECASE,
)
ROUGH_TAGS = {"vulgar", "offensive", "derogatory", "slur", "obsolete", "archaic", "dialectal", "rare", "slang"}
SKIP_CATEGORIES = re.compile(r"given names|patronymics|surnames|drugs|Pharmac|Bible|Islam|Christianity|Ethnonyms")
BLOCKED = {"fuck", "shit", "bitch", "ass", "damn", "sex", "porn", "dick", "cock", "pussy", "whore", "drug"}


def english_meaning(gloss: str, pos: str) -> str:
    """'to buy; to purchase' → 'buy'; 'cat (animal)' → 'cat'. Empty when the gloss is a description."""
    gloss = re.sub(r"\([^)]*\)", "", gloss).strip()
    first = re.split(r"[;,]", gloss)[0].strip()
    if pos == "verb":
        first = re.sub(r"^to ", "", first)
    first = re.sub(r"^(a|an|the) ", "", first)
    if first[:1].isupper():
        return ""  # names, nationalities, months: "a Russian", "Sunday"
    first = first.lower()
    return first if re.fullmatch(r"[a-z][a-z'-]{0,23}[a-z]", first) else ""


def main():
    # english word → candidates (kazakh word, pos, score, categories)
    found = defaultdict(list)
    for line in sys.stdin:
        entry = json.loads(line)
        kk, pos = entry.get("word", "").strip(), entry.get("pos")
        if pos not in POS or not CYR.match(kk):
            continue
        for index, sense in enumerate(entry.get("senses", [])[:2]):
            if ROUGH_TAGS & set(sense.get("tags", [])):
                continue
            cats = [c.get("name", "") if isinstance(c, dict) else c for c in sense.get("categories", [])]
            if any(SKIP_CATEGORIES.search(c) for c in cats):
                continue
            glosses = sense.get("glosses", [])
            if not glosses or NOT_A_MEANING.search(glosses[0]) or glosses[0][:1].isupper():
                continue  # capitalised meanings are names, months, games
            en = english_meaning(glosses[0], pos)
            if not en or en in BLOCKED or zipf_frequency(en, "en") < MIN_ZIPF or RANK.get(en, 60000) <= MIN_RANK:
                continue
            # A Kazakh word whose main meaning is exactly this English word ranks first.
            exact = re.sub(r"\([^)]*\)", "", glosses[0]).strip().lower() in {en, f"to {en}"}
            score = (2 if index == 0 else 0) + (1 if exact else 0)
            found[en].append((kk, pos, score, [c for c in cats if c[:1].isupper()]))

    for en, candidates in found.items():
        candidates.sort(key=lambda c: (-c[2], len(c[0])))
        pos = candidates[0][1]
        same_pos = [c for c in candidates if c[1] == pos]
        print(
            json.dumps(
                {
                    "word": en,
                    "rank": RANK.get(en, 60000),
                    "pos": pos,
                    "kk": [{"word": c[0], "sense": ""} for c in same_pos],
                    "ipa": "",
                    "past": [],
                    "categories": [same_pos[0][3]],
                    "source": "kk-dictionary",
                },
                ensure_ascii=False,
            )
        )
    print(f"english words: {len(found)}", file=sys.stderr)


if __name__ == "__main__":
    main()
