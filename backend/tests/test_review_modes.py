import pytest
from django.utils import timezone

from progress.models import ProgressLog
from srs import quiz
from srs.models import UserVocabulary
from vocabulary.models import Vocabulary

pytestmark = pytest.mark.django_db


def _due(user, word, stage):
    vocab = Vocabulary.objects.get(word=word)
    UserVocabulary.objects.create(user=user, vocabulary=vocab, stage=stage, next_review_date=timezone.localdate())
    return vocab


def _card(client, word):
    return next(c for c in client.get("/api/srs/today/").json()["review"] if c["word"] == word)


def _check(client, vocab, mode, answer):
    return client.post(f"/api/srs/{vocab.id}/check/", {"mode": mode, "answer": answer}, format="json").json()


def test_the_exercise_gets_harder_with_the_stage(client, user):
    _due(user, "buy", 1)
    _due(user, "go", 3)
    _due(user, "eat", 5)
    assert _card(client, "buy")["quiz"]["mode"] == "choice"
    assert _card(client, "go")["quiz"]["mode"] == "listen"
    assert _card(client, "eat")["quiz"] == {"mode": "type"}


def test_choice_offers_four_different_translations_with_the_right_one(client, user):
    _due(user, "buy", 1)
    options = _card(client, "buy")["quiz"]["options"]
    assert len(options) == 4 and len(set(options)) == 4
    assert "сатып алу" in options


def test_listening_offers_four_spellings(client, user):
    _due(user, "speak", 4)
    options = _card(client, "speak")["quiz"]["options"]
    assert len(set(options)) == 4 and "speak" in options


def test_a_right_choice_moves_the_word_up(client, user):
    buy = _due(user, "buy", 2)
    r = _check(client, buy, "choice", "сатып алу")
    assert r["correct"] and r["stage"] == 3
    assert ProgressLog.objects.get(user=user).remembered == 1


def test_a_wrong_answer_shows_the_right_one_and_brings_the_word_back_today(client, user):
    go = _due(user, "go", 3)
    r = _check(client, go, "listen", "goat")
    assert not r["correct"] and r["right"] == "go"
    assert r["stage"] == 2 and r["again_today"]


def test_i_dont_know_counts_as_forgotten(client, user):
    eat = _due(user, "eat", 5)
    r = _check(client, eat, "type", "")
    assert not r["correct"] and r["stage"] == 4


def test_typing_forgives_one_typo_in_a_longer_word(client, user):
    study = _due(user, "study", 5)
    r = _check(client, study, "type", "Study ")
    assert r["correct"] and not r["almost"]
    item = UserVocabulary.objects.get(user=user, vocabulary=study)
    item.stage, item.next_review_date = 5, timezone.localdate()
    item.save()
    r = _check(client, study, "type", "studdy")
    assert r["correct"] and r["almost"] and r["right"] == "study"
    assert not quiz.check(Vocabulary.objects.get(word="go"), "type", "do")["correct"]  # short words: exact only


def test_only_words_in_review_can_be_checked(client):
    buy = Vocabulary.objects.get(word="buy")
    r = client.post(f"/api/srs/{buy.id}/check/", {"mode": "choice", "answer": "x"}, format="json")
    assert r.status_code == 409


def test_a_card_cannot_be_answered_in_an_easier_mode(client, user):
    from srs.models import UserVocabulary
    from vocabulary.models import Vocabulary

    vocab = Vocabulary.objects.filter(is_verb=True).first()
    UserVocabulary.objects.create(user=user, vocabulary=vocab, stage=5, next_review_date="2000-01-01")
    r = client.post(f"/api/srs/{vocab.id}/check/", {"mode": "choice", "answer": vocab.translation_kk}, format="json")
    assert r.status_code == 409 and r.json()["code"] == "stale"
    assert UserVocabulary.objects.get(user=user, vocabulary=vocab).stage == 5


def test_a_word_that_slipped_back_is_still_asked_the_old_way(client, user):
    from srs.models import UserVocabulary
    from vocabulary.models import Vocabulary

    vocab = Vocabulary.objects.filter(is_verb=True).first()
    UserVocabulary.objects.create(user=user, vocabulary=vocab, stage=2, next_review_date="2000-01-01")
    r = client.post(f"/api/srs/{vocab.id}/check/", {"mode": "listen", "answer": vocab.word}, format="json")
    assert r.status_code == 200 and r.json()["correct"] is True
