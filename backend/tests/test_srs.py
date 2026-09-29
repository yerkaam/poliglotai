from datetime import timedelta

import pytest
from django.utils import timezone

from srs.models import UserVocabulary
from users.models import Profile
from vocabulary.models import Vocabulary

pytestmark = pytest.mark.django_db


def _answer(client, word, answer):
    return client.post(f"/api/srs/{word.id}/answer/", {"answer": answer}, format="json")


def test_start_puts_word_on_stage_1_for_tomorrow(client, user):
    buy = Vocabulary.objects.get(word="buy")
    r = _answer(client, buy, "start")
    assert r.status_code == 200
    item = UserVocabulary.objects.get(user=user, vocabulary=buy)
    assert item.stage == 1
    assert item.next_review_date == timezone.localdate() + timedelta(days=1)


def test_remember_on_stage_2_moves_to_stage_3_in_4_days(client, user):
    buy = Vocabulary.objects.get(word="buy")
    UserVocabulary.objects.create(user=user, vocabulary=buy, stage=2, next_review_date=timezone.localdate())
    r = _answer(client, buy, "remember")
    assert r.json()["stage"] == 3
    item = UserVocabulary.objects.get(user=user, vocabulary=buy)
    assert item.next_review_date == timezone.localdate() + timedelta(days=4)


def test_forget_on_stage_3_goes_back_and_shows_again(client, user):
    buy = Vocabulary.objects.get(word="buy")
    UserVocabulary.objects.create(user=user, vocabulary=buy, stage=3, next_review_date=timezone.localdate())
    r = _answer(client, buy, "forget")
    assert r.json()["stage"] == 2
    assert r.json()["again_today"] is True
    today = client.get("/api/srs/today/").json()
    assert "buy" in [w["word"] for w in today["review"]]


def test_six_reviews_make_a_word_learned(client, user):
    buy = Vocabulary.objects.get(word="buy")
    UserVocabulary.objects.create(user=user, vocabulary=buy, stage=6, next_review_date=timezone.localdate())
    r = _answer(client, buy, "remember")
    assert r.json()["status"] == "learned"


def test_reviews_come_before_new_words_and_limit_is_respected(client, user):
    Profile.objects.filter(user=user).update(daily_new_limit=5)
    buy = Vocabulary.objects.get(word="buy")
    UserVocabulary.objects.create(
        user=user,
        vocabulary=buy,
        stage=2,
        next_review_date=timezone.localdate(),
        started_on=timezone.localdate() - timedelta(days=3),
    )
    today = client.get("/api/srs/today/").json()
    assert [w["word"] for w in today["review"]] == ["buy"]
    assert len(today["new"]) == 5

    for word in today["new"]:
        assert client.post(f"/api/srs/{word['id']}/answer/", {"answer": "start"}, format="json").status_code == 200

    after = client.get("/api/srs/today/").json()
    assert after["new"] == []
    assert after["new_left"] == 0
    extra = Vocabulary.objects.exclude(id__in=UserVocabulary.objects.values("vocabulary_id")).first()
    assert _answer(client, extra, "start").status_code == 409


def test_already_know_does_not_use_the_limit(client, user):
    Profile.objects.filter(user=user).update(daily_new_limit=5)
    for word in Vocabulary.objects.all()[:3]:
        assert _answer(client, word, "known").status_code == 200
    assert client.get("/api/srs/today/").json()["new_left"] == 5


def test_progress_survives_a_new_login(client, user):
    buy = Vocabulary.objects.get(word="buy")
    _answer(client, buy, "start")
    from rest_framework.test import APIClient

    other_device = APIClient()
    other_device.post("/api/auth/login/", {"email": user.email, "password": "englishday1"}, format="json")
    verbs = other_device.get("/api/verbs/").json()
    assert next(v for v in verbs if v["word"] == "buy")["status"] == "learning"


def test_progress_endpoint_and_reset(client, user):
    buy = Vocabulary.objects.get(word="buy")
    _answer(client, buy, "start")
    data = client.get("/api/progress/").json()
    assert data["stats"]["learning"] == 1
    assert data["stages"][0] == {"stage": 1, "count": 1}
    assert data["learned_of"]["total"] == 40
    assert client.post("/api/progress/reset/", {"confirm": False}, format="json").status_code == 400
    assert client.post("/api/progress/reset/", {"confirm": True}, format="json").status_code == 204
    assert client.get("/api/progress/").json()["stats"]["learning"] == 0
