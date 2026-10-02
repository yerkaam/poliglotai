import json

import pytest
from rest_framework.test import APIClient

from chat.models import Conversation, Message
from classroom.models import Group, Membership
from srs.models import UserVocabulary
from users.models import User
from vocabulary.models import Vocabulary

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db

NEW = "spring-words-42"


def _login(user, password=PASSWORD):
    api = APIClient()
    assert api.post("/api/auth/login/", {"email": user.email, "password": password}, format="json").status_code == 200
    return api


def _change(api, old=PASSWORD, new=NEW, new2=None):
    return api.post(
        "/api/auth/password/", {"old_password": old, "password": new, "password2": new2 or new}, format="json"
    )


def test_change_password_keeps_this_device_and_logs_out_others(user, client):
    other = _login(user)
    r = _change(client)
    assert r.status_code == 200
    assert client.get("/api/auth/me/").status_code == 200
    # the other device cannot renew its session
    assert other.post("/api/auth/refresh/").status_code == 401
    user.refresh_from_db()
    assert user.check_password(NEW)
    _login(user, NEW)


def test_change_password_checks_old_and_new(user, client):
    r = _change(client, old="wrong-password")
    assert r.status_code == 400 and "old_password" in r.json()
    assert _change(client, new2="something-else").json().keys() >= {"password2"}
    assert "password" in _change(client, new="123").json()
    assert "password" in _change(client, new=PASSWORD).json()
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_wrong_current_password_is_limited(user, client):
    for _ in range(5):
        assert _change(client, old="wrong-password").status_code == 400
    # even the right password waits now: a stolen session cannot guess its way in
    assert _change(client).status_code == 429


def test_export_contains_the_learners_data(user, client):
    word = Vocabulary.objects.get_or_create(word="apple", defaults={"translation_kk": "алма"})[0]
    UserVocabulary.objects.create(user=user, vocabulary=word, stage=2)
    convo = Conversation.objects.create(user=user, mode="free")
    Message.objects.create(conversation=convo, role="user", text="I like apples")
    teacher = User.objects.create_user(email="t@mail.kz", password=PASSWORD, name="Мұғалім", is_teacher=True)
    Membership.objects.create(group=Group.objects.create(teacher=teacher, name="7A", code="ABCDEF"), student=user)

    r = client.get("/api/auth/export/")
    assert r.status_code == 200
    assert "attachment" in r["Content-Disposition"]
    data = json.loads(r.content)
    assert data["account"]["email"] == user.email
    assert data["words"][0]["word"] == "apple" and data["words"][0]["stage"] == 2
    assert data["chat"][0]["messages"][0]["text"] == "I like apples"
    assert data["groups_joined"][0]["group"] == "7A"
    assert "password" not in json.dumps(data)


def test_export_shows_only_own_data(user, client):
    other = User.objects.create_user(email="o@mail.kz", password=PASSWORD, name="O", email_verified=True)
    Conversation.objects.create(user=other, mode="free")
    assert json.loads(client.get("/api/auth/export/").content)["chat"] == []


def test_delete_account_needs_password_and_removes_everything(user, client):
    word = Vocabulary.objects.get_or_create(word="apple", defaults={"translation_kk": "алма"})[0]
    UserVocabulary.objects.create(user=user, vocabulary=word)
    Conversation.objects.create(user=user, mode="free")

    assert client.post("/api/auth/delete/", {"password": "wrong-password"}, format="json").status_code == 400
    assert User.objects.filter(pk=user.pk).exists()

    r = client.post("/api/auth/delete/", {"password": PASSWORD}, format="json")
    assert r.status_code == 204
    assert not User.objects.filter(pk=user.pk).exists()
    assert not UserVocabulary.objects.exists() and not Conversation.objects.exists()
    assert Vocabulary.objects.filter(pk=word.pk).exists()  # the shared dictionary stays
    assert client.get("/api/auth/me/").status_code == 401
    assert (
        APIClient().post("/api/auth/login/", {"email": user.email, "password": PASSWORD}, format="json").status_code
        == 400
    )


def test_account_actions_need_login(anon):
    assert anon.get("/api/auth/export/").status_code == 401
    assert anon.post("/api/auth/delete/", {"password": PASSWORD}, format="json").status_code == 401
    assert _change(anon).status_code == 401
