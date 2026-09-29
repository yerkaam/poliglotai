# wiktionary_en_kk.jsonl

English words with Kazakh translations, built from two parts of [Wiktionary](https://en.wiktionary.org/)
(via the [kaikki.org](https://kaikki.org/) wiktextract dumps):

1. **English → Kazakh** (`via: "en"`): translation tables of English entries, frequent words only
   ([wordfreq](https://github.com/rspeer/wordfreq)). The more reliable source; it wins on overlap.
2. **Kazakh → English, reversed** (`via: "kk"`): Kazakh entries whose main meaning is a single English word.
   Fills words the first source lacks. The top 1000 English words are skipped here (too polysemous:
   "may" → мамыр), as are names, months, medicines and crude or archaic words.

Licence: **CC BY-SA 4.0** — © Wiktionary contributors. Wherever these translations are shown, the site
credits Wiktionary; changes to this file stay under CC BY-SA.

Topics: `topics.json` (hand-assigned) first; otherwise, for Kazakh-dictionary words, the entry's category
("Mammals" → animals); otherwise `general`.

Rebuild:

```bash
curl -s https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl \
  | WORDFREQ_TOP=30000 python scripts/extract_wiktionary_kk.py > /tmp/wikt_kk_raw.jsonl
curl -s https://kaikki.org/dictionary/Kazakh/kaikki.org-dictionary-Kazakh.jsonl \
  | python scripts/extract_kazakh_dictionary.py > /tmp/kk_dict_raw.jsonl
python scripts/build_wiktionary_dataset.py /tmp/wikt_kk_raw.jsonl /tmp/kk_dict_raw.jsonl
python manage.py import_wiktionary
```

Fields: `word`, `rank` (frequency), `pos`, `translation_kk` (up to 3, comma-separated), `ipa`, `past`,
`topic`, `via`. Translations come from volunteers and are not reviewed: the methodologist should check
them in the admin before words are added to course steps.
