# wiktionary_en_kk.jsonl

Frequent English words (top 6000 by [wordfreq](https://github.com/rspeer/wordfreq)) that have Kazakh
translations in the English [Wiktionary](https://en.wiktionary.org/), extracted from the
[kaikki.org](https://kaikki.org/) JSONL dump (wiktextract).

Licence: **CC BY-SA 4.0** — © Wiktionary contributors. Wherever these translations are shown, the site
credits Wiktionary; changes to this file stay under CC BY-SA.

Rebuild:

```bash
curl -s https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl \
  | python scripts/extract_wiktionary_kk.py > /tmp/wikt_kk_raw.jsonl
python scripts/build_wiktionary_dataset.py /tmp/wikt_kk_raw.jsonl
python manage.py import_wiktionary
```

Fields: `word`, `rank` (frequency), `pos`, `translation_kk` (up to 3, comma-separated), `ipa`, `past`.
Translations come from volunteers and are not reviewed: the methodologist should check them in the admin
before words are added to course steps.
