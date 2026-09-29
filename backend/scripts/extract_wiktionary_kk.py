#!/usr/bin/env python3
"""Step 1: stream the kaikki.org English Wiktionary JSONL and keep frequent words with Kazakh translations.

Usage:
  curl -s https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl \
    | python scripts/extract_wiktionary_kk.py > /tmp/wikt_kk_raw.jsonl
Needs `pip install wordfreq`. Then run scripts/build_wiktionary_dataset.py.
"""

import json
import re
import sys

from wordfreq import top_n_list

TOP = {w: i for i, w in enumerate(top_n_list("en", 6000), start=1)}
CYR = re.compile(r"^[А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі \-]+$")
META = re.compile(r"English|terms|Terms|Pages|Requests|Entries|with |Translation|Quotation|Rhymes|Undefined")
ROUGH = {"vulgar", "offensive", "derogatory", "slur", "ethnic"}
BLOCKED = {"fuck", "shit", "bitch", "ass", "damn", "hell", "sex", "porn", "dick", "cock", "pussy", "whore"}
POS = {"noun", "verb", "adj", "adv", "pron", "prep", "conj", "num", "intj", "det"}
seen = kept = 0
for line in sys.stdin:
    seen += 1
    if '"kk"' not in line:
        continue
    try:
        e = json.loads(line)
    except ValueError:
        continue
    word = e.get("word", "")
    if word not in TOP or e.get("pos") not in POS:
        continue
    tr = [
        {"word": t["word"].strip(), "sense": t.get("sense", "")}
        for t in e.get("translations", [])
        if (t.get("code") == "kk" or t.get("lang") == "Kazakh") and CYR.match(t.get("word", "").strip())
    ]
    if not tr:
        continue
    ipas = [s for s in e.get("sounds", []) if s.get("ipa")]
    uk = [s["ipa"] for s in ipas if any(t in ("UK", "Received-Pronunciation", "British") for t in s.get("tags", []))]
    ipa = (uk or [s["ipa"] for s in ipas] or [""])[0]
    past = [f["form"] for f in e.get("forms", []) if f.get("tags") == ["past"]]
    examples = [
        x.get("text", "")
        for s in e.get("senses", [])
        for x in s.get("examples", [])
        if x.get("text") and len(x.get("text", "")) < 90 and x.get("type") != "quotation"
    ]
    glosses = [g for s in e.get("senses", []) for g in s.get("glosses", [])][:3]
    senses = e.get("senses", [])[:6]
    # Learners never see crude or offensive words.
    if word in BLOCKED or any(ROUGH & set(sn.get("tags", [])) for sn in senses[:2]):
        continue
    # Categories per sense, in Wiktionary's order; the build step takes the first one that maps to a topic.
    cats = []
    for sn in senses:
        names = {c.get("name", "") if isinstance(c, dict) else c for c in sn.get("categories", [])}
        names |= set(sn.get("topics", []))
        cats.append(sorted(c for c in names if c and not META.search(c)))
    kept += 1
    print(
        json.dumps(
            {
                "word": word,
                "rank": TOP[word],
                "pos": e["pos"],
                "kk": tr,
                "ipa": ipa,
                "past": past[:2],
                "example": examples[:1],
                "glosses": glosses,
                "categories": cats,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
print(f"seen={seen} kept={kept}", file=sys.stderr)
