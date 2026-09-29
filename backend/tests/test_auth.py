import re

import pytest
from django.core import mail
from rest_framework.test import APIClient

from users.models import User

pytestmark = pytest.mark.django_db

REGISTER = {
    "name": "Айгерім",
    "email": "new@mail.kz",
    "password": "englishday1",
    "password2": "englishday1",
    "accept_terms": True,
}


def test_register_logs_in_and_needs_onboarding(anon):
    r = anon.post("/api/auth/register/", REGISTER, format="json")
    assert r.status_code == 201
    assert r.json()["profile"]["onboarded"] is False
    assert anon.get("/api/auth/me/").json()["email"] == "new@mail.kz"
    r = anon.patch("/api/auth/profile/", {"level": "A1", "daily_new_limit": 15, "onboarded": True}, format="json")
    assert r.json()["profile"] == {"level": "A1", "daily_new_limit": 15, "daily_minutes": 15, "onboarded": True}


@pytest.mark.parametrize("password", ["short1", "longpassword"])
def test_weak_password_is_rejected(anon, password):
    r = anon.post("/api/auth/register/", {**REGISTER, "password": password, "password2": password}, format="json")
    assert r.status_code == 400


def test_duplicate_email_has_clear_error(anon, user):
    r = anon.post("/api/auth/register/", {**REGISTER, "email": "AIGERIM@mail.kz"}, format="json")
    assert r.status_code == 400
    assert "бұрыннан бар" in r.json()["email"][0]


def test_wrong_password_and_unknown_email_give_the_same_error(anon, user):
    a = anon.post("/api/auth/login/", {"email": user.email, "password": "nope12345"}, format="json")
    b = anon.post("/api/auth/login/", {"email": "ghost@mail.kz", "password": "nope12345"}, format="json")
    assert a.status_code == b.status_code == 400
    assert a.json() == b.json() == {"detail": "Пошта немесе құпиясөз қате"}


def test_five_failures_lock_login(anon, user):
    for _ in range(5):
        anon.post("/api/auth/login/", {"email": user.email, "password": "nope12345"}, format="json")
    r = anon.post("/api/auth/login/", {"email": user.email, "password": "englishday1"}, format="json")
    assert r.status_code == 429


def test_tokens_are_httponly_cookies(anon, user):
    r = anon.post("/api/auth/login/", {"email": user.email, "password": "englishday1", "remember": True}, format="json")
    access, refresh = r.cookies["access_token"], r.cookies["refresh_token"]
    assert access["httponly"] and refresh["httponly"]
    assert refresh["max-age"] == 30 * 24 * 3600
    assert "access" not in r.json()


def test_without_remember_me_the_session_ends_with_the_browser(anon, user):
    r = anon.post("/api/auth/login/", {"email": user.email, "password": "englishday1"}, format="json")
    assert r.cookies["refresh_token"]["max-age"] == ""


def test_refresh_issues_new_access_token(client):
    assert client.post("/api/auth/refresh/").status_code == 200
    assert client.get("/api/auth/me/").status_code == 200


def test_logout_closes_private_pages(client):
    assert client.post("/api/auth/logout/").status_code == 204
    assert client.get("/api/auth/me/").status_code in (401, 403)
    assert client.post("/api/auth/refresh/").status_code == 401


def test_private_pages_need_login(anon):
    for url in ["/api/auth/me/", "/api/verbs/", "/api/srs/today/", "/api/progress/", "/api/chat/scenarios/"]:
        assert anon.get(url).status_code in (401, 403), url


def _reset_link():
    body = mail.outbox[-1].body
    uid = re.search(r"uid=([\w-]+)", body).group(1)
    token = re.search(r"token=([\w-]+)", body).group(1)
    return uid, token


def test_password_reset_link_works_once(anon, user):
    r = anon.post("/api/auth/password-reset/", {"email": user.email}, format="json")
    assert r.status_code == 200
    uid, token = _reset_link()
    ok = anon.post(
        "/api/auth/password-reset/confirm/", {"uid": uid, "token": token, "password": "newpass123"}, format="json"
    )
    assert ok.status_code == 200
    again = anon.post(
        "/api/auth/password-reset/confirm/", {"uid": uid, "token": token, "password": "other1234"}, format="json"
    )
    assert again.status_code == 400
    assert User.objects.get(pk=user.pk).check_password("newpass123")


def test_password_reset_link_expires_after_an_hour(anon, user, settings):
    from datetime import datetime, timedelta
    from unittest import mock

    anon.post("/api/auth/password-reset/", {"email": user.email}, format="json")
    uid, token = _reset_link()
    later = datetime.now() + timedelta(hours=1, minutes=1)
    with mock.patch("django.contrib.auth.tokens.PasswordResetTokenGenerator._now", return_value=later):
        r = anon.post(
            "/api/auth/password-reset/confirm/", {"uid": uid, "token": token, "password": "newpass123"}, format="json"
        )
    assert r.status_code == 400


def test_reset_answer_is_the_same_for_unknown_email_and_resend_waits(anon, user):
    known = anon.post("/api/auth/password-reset/", {"email": user.email}, format="json")
    unknown = anon.post("/api/auth/password-reset/", {"email": "ghost@mail.kz"}, format="json")
    assert known.json() == unknown.json()
    assert len(mail.outbox) == 1
    assert anon.post("/api/auth/password-reset/", {"email": user.email}, format="json").status_code == 429


def test_csrf_is_enforced_for_cookie_sessions(user):
    api = APIClient(enforce_csrf_checks=True)
    api.post("/api/auth/login/", {"email": user.email, "password": "englishday1"}, format="json")
    r = api.post("/api/progress/reset/", {"confirm": True}, format="json")
    assert r.status_code == 403
