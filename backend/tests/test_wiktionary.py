import json

import pytest

from vocabulary import forms
from vocabulary.models import Vocabulary
from vocabulary.wiktionary import load

pytestmark = pytest.mark.django_db


@pytest.fixture
def no_imported_words():
    """The migration already loaded the shipped dataset; these tests import their own rows."""
    Vocabulary.objects.filter(source="wiktionary").delete()


def _write(tmp_path, rows):
    path = tmp_path / "words.jsonl"
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    return path


ROWS = [
    {"word": "buy", "rank": 300, "pos": "verb", "translation_kk": "WRONG", "ipa": "", "past": "bought"},
    {"word": "shake", "rank": 2000, "pos": "verb", "translation_kk": "сілку", "ipa": "/ʃeɪk/", "past": "shook"},
    {"word": "cook", "rank": 1800, "pos": "verb", "translation_kk": "пісіру", "ipa": "/kʊk/", "past": "cooked"},
    {"word": "might", "rank": 40, "pos": "verb", "translation_kk": "мүмкін", "ipa": "", "past": ""},
    {"word": "water", "rank": 500, "pos": "noun", "translation_kk": "су", "ipa": "", "past": "", "topic": "nature"},
]


def test_import_keeps_course_words_and_detects_irregular_verbs(tmp_path, no_imported_words):
    result = load(Vocabulary, _write(tmp_path, ROWS))
    assert result == {"created": 4, "updated": 0, "skipped": 1}
    assert Vocabulary.objects.get(word="buy").translation_kk == "сатып алу"

    shake = Vocabulary.objects.get(word="shake")
    assert (shake.is_verb, shake.is_irregular, shake.past, shake.source) == (True, True, "shook", "wiktionary")
    assert shake.course_step is None

    cook = Vocabulary.objects.get(word="cook")
    assert (cook.is_irregular, cook.past_form, cook.past) == (False, "", "cooked")

    assert Vocabulary.objects.get(word="might").is_verb is False  # modal: not for the do/does/did table
    assert Vocabulary.objects.get(word="water").topic == "nature"
    assert Vocabulary.objects.get(word="shake").topic == "general"


def test_imported_verbs_build_a_correct_table(tmp_path, no_imported_words):
    load(Vocabulary, _write(tmp_path, ROWS))
    shake = Vocabulary.objects.get(word="shake")
    texts = [c["text"] for c in forms.table(shake, "he")]
    assert texts[4] == "He shakes." and texts[7] == "He shook." and texts[6] == "Did he shake?"


def test_import_is_idempotent(tmp_path, no_imported_words):
    path = _write(tmp_path, ROWS)
    load(Vocabulary, path)
    assert load(Vocabulary, path)["created"] == 0


def test_shipped_dataset_is_loaded_by_migration():
    assert Vocabulary.objects.filter(source="wiktionary").count() > 100
    assert not Vocabulary.objects.filter(source="wiktionary", translation_kk="").exists()


def test_topics_file_matches_the_dataset():
    from vocabulary.wiktionary import DATA_FILE, TOPICS_KK

    topics = json.loads((DATA_FILE.parent / "topics.json").read_text(encoding="utf-8"))
    words = {json.loads(line)["word"] for line in DATA_FILE.read_text(encoding="utf-8").splitlines() if line}
    assigned = [w for topic, ws in topics.items() if not topic.startswith("_") for w in ws]
    assert len(assigned) == len(set(assigned)), "a word is in two topics"
    assert set(assigned) <= words, set(assigned) - words
    assert {t for t in topics if not t.startswith("_")} <= set(TOPICS_KK)


def _build_module():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / "scripts" / "build_wiktionary_dataset.py"
    spec = importlib.util.spec_from_file_location("build_wiktionary_dataset", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_topic_from_kazakh_dictionary_categories():
    build = _build_module()
    assert build.category_topic({"pos": "noun", "categories": [["Mammals", "Kazakh lemmas"]]}) == "animals"
    assert build.category_topic({"pos": "noun", "categories": [["Months"]]}) == ""  # қазан: October / cauldron
    assert build.category_topic({"pos": "num", "categories": [[]]}) == "numbers"
    assert build.category_topic({"pos": "noun", "categories": [["Pages with 1 entry"]]}) == ""


def test_english_source_wins_over_reversed_kazakh_dictionary(tmp_path, monkeypatch):
    build = _build_module()
    monkeypatch.setattr(build, "OUT", tmp_path / "out.jsonl")
    en = tmp_path / "en.jsonl"
    kk = tmp_path / "kk.jsonl"
    row = {"rank": 10, "pos": "noun", "ipa": "", "past": [], "categories": [[]]}
    en.write_text(json.dumps({**row, "word": "cat", "kk": [{"word": "мысық", "sense": ""}]}, ensure_ascii=False))
    kk.write_text(
        "\n".join(
            json.dumps(
                {
                    **row,
                    "word": w,
                    "kk": [{"word": t, "sense": ""}],
                    "source": "kk-dictionary",
                    "categories": [["Mammals"]],
                },
                ensure_ascii=False,
            )
            for w, t in [("cat", "WRONG"), ("horse", "ат")]
        )
    )
    build.main(str(en), str(kk))
    out = {r["word"]: r for r in map(json.loads, (tmp_path / "out.jsonl").read_text().splitlines())}
    assert out["cat"]["translation_kk"] == "мысық" and out["cat"]["via"] == "en"
    assert out["horse"]["translation_kk"] == "ат" and out["horse"]["topic"] == "animals"


def test_irregular_past_is_filled_when_the_source_has_no_forms(tmp_path, no_imported_words):
    rows = [{"word": "catch", "rank": 900, "pos": "verb", "translation_kk": "ұстау", "ipa": "", "past": ""}]
    load(Vocabulary, _write(tmp_path, rows))
    catch = Vocabulary.objects.get(word="catch")
    assert (catch.is_irregular, catch.past) == (True, "caught")
