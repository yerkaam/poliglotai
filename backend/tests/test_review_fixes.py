"""Regression tests for the issues found in the code review."""

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.test import RequestFactory
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

from chat.models import Conversation, Message
from srs.models import UserVocabulary
from users.views import _client_ip
from vocabulary.models import Vocabulary

from .conftest import PASSWORD


@pytest.fixture
def offline(settings):
    settings.ANTHROPIC_API_KEY = ""
    settings.CHAT_DAILY_LIMIT = 2
    return settings


def test_opening_a_dialog_counts_against_the_chat_limit(client, offline):
    assert client.post("/api/chat/conversations/", {"mode": "free"}, format="json").status_code == 201
    assert client.post("/api/chat/conversations/", {"mode": "free"}, format="json").status_code == 201
    r = client.post("/api/chat/conversations/", {"mode": "free"}, format="json")
    assert r.status_code == 429
    assert r.json()["code"] == "chat_limit"
    assert Conversation.objects.count() == 2


def test_rejected_messages_do_not_use_up_the_limit(client, offline):
    conv = client.post("/api/chat/conversations/", {"mode": "free"}, format="json").json()
    url = f"/api/chat/conversations/{conv['id']}/messages/"
    for _ in range(3):
        assert client.post(url, {"text": "drugs"}, format="json").status_code == 400
    r = client.post(url, {"text": "I like tea."}, format="json")
    assert r.status_code == 201
    assert r.json()["usage"] == {"used": 2, "limit": 2}
    # The counter on the screen and the server agree: the limit is reached now.
    assert client.post(url, {"text": "I like coffee."}, format="json").status_code == 429


def test_password_reset_logs_out_other_sessions(client, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    r = APIClient().post(
        "/api/auth/password-reset/confirm/", {"uid": uid, "token": token, "password": "newpass123"}, format="json"
    )
    assert r.status_code == 200
    assert client.post("/api/auth/refresh/").status_code == 401


def test_chat_word_translation_comes_from_the_tutor_not_the_request(client, user):
    r = client.post("/api/srs/add/", {"word": "zebra", "translation_kk": "кез келген мәтін"}, format="json")
    assert r.status_code == 400
    assert not Vocabulary.objects.filter(word="zebra").exists()

    conversation = Conversation.objects.create(user=user, mode=Conversation.Mode.FREE)
    Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        text="Look, a zebra!",
        new_words=[{"word": "zebra", "translation_kk": "зебра"}],
    )
    r = client.post("/api/srs/add/", {"word": "zebra", "translation_kk": "кез келген мәтін"}, format="json")
    assert r.status_code == 201
    assert Vocabulary.objects.get(word="zebra").translation_kk == "зебра"


def test_registration_survives_a_mail_server_failure(db, anon, settings, monkeypatch):
    settings.REQUIRE_EMAIL_VERIFICATION = True

    def broken(*args, **kwargs):
        raise ConnectionRefusedError("SMTP down")

    monkeypatch.setattr("users.verification.send_mail", broken)
    r = anon.post(
        "/api/auth/register/",
        {"name": "Ерлан", "email": "erlan@mail.kz", "password": PASSWORD, "password2": PASSWORD, "accept_terms": True},
        format="json",
    )
    assert r.status_code == 201
    # The learner is logged in and can ask for the code again at once; while mail is down that says so.
    r = anon.post("/api/auth/verify-email/resend/")
    assert r.status_code == 503
    assert r.json()["code"] == "mail_failed"


def test_login_lockout_ignores_a_spoofed_forwarded_for(settings):
    request = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="1.2.3.4", REMOTE_ADDR="10.0.0.1")
    settings.TRUSTED_PROXY_COUNT = 0
    assert _client_ip(request) == "10.0.0.1"
    # Behind one proxy the client is the entry that proxy appended, not the one the client sent.
    request = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="1.2.3.4, 5.6.7.8", REMOTE_ADDR="10.0.0.1")
    settings.TRUSTED_PROXY_COUNT = 1
    assert _client_ip(request) == "5.6.7.8"


def test_dictionary_words_follow_the_course_words(client, user):
    course = Vocabulary.objects.filter(course_step__is_open=True)
    UserVocabulary.objects.bulk_create(
        UserVocabulary(user=user, vocabulary=v, status=UserVocabulary.Status.KNOWN) for v in course
    )
    new = client.get("/api/srs/today/").json()["new"]
    assert new, "after the course words the learner gets dictionary words"
    assert {w["source"] for w in new} == {"wiktionary"}


def test_same_card_twice_is_a_conflict_not_a_server_error(client):
    word = Vocabulary.objects.filter(course_step__is_open=True).first()
    assert client.post(f"/api/srs/{word.id}/answer/", {"answer": "start"}, format="json").status_code == 200
    assert client.post(f"/api/srs/{word.id}/answer/", {"answer": "start"}, format="json").status_code == 409
