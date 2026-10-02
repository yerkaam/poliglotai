import json
import urllib.error
from io import BytesIO

import pytest
from django.core.mail import EmailMessage, get_connection

from users import email_backends


class FakeResponse(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _backend(settings):
    settings.BREVO_API_KEY = "test-key"
    return get_connection("users.email_backends.BrevoEmailBackend")


def test_brevo_sends_the_message_as_json(settings, monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return FakeResponse(b'{"messageId": "1"}')

    monkeypatch.setattr(email_backends.urllib.request, "urlopen", fake_urlopen)
    message = EmailMessage(
        "Код: 123456", "Сәлем!", "PoliglotAi <school@mail.kz>", ["learner@mail.kz"], headers={"List-Unsubscribe": "<x>"}
    )
    assert _backend(settings).send_messages([message]) == 1
    request, timeout = calls[0]
    body = json.loads(request.data)
    assert request.full_url == email_backends.BREVO_URL and request.get_header("Api-key") == "test-key"
    assert body["sender"] == {"name": "PoliglotAi", "email": "school@mail.kz"}
    assert body["to"] == [{"email": "learner@mail.kz"}]
    assert body["subject"] == "Код: 123456" and body["textContent"] == "Сәлем!"
    assert body["headers"] == {"List-Unsubscribe": "<x>"}
    assert timeout == settings.EMAIL_TIMEOUT


def test_brevo_error_is_raised_with_its_explanation(settings, monkeypatch):
    def fake_urlopen(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 400, "Bad", {}, BytesIO(b'{"message":"sender not valid"}'))

    monkeypatch.setattr(email_backends.urllib.request, "urlopen", fake_urlopen)
    message = EmailMessage("s", "b", "a@b.kz", ["c@d.kz"])
    with pytest.raises(RuntimeError, match="sender not valid"):
        _backend(settings).send_messages([message])


def test_gmail_script_posts_the_message_with_the_secret(settings, monkeypatch):
    settings.GMAIL_SCRIPT_URL = "https://script.google.com/macros/s/x/exec"
    settings.GMAIL_SCRIPT_SECRET = "s3cret"
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request)
        return FakeResponse(b'{"ok": true, "left_today": 99}')

    monkeypatch.setattr(email_backends.urllib.request, "urlopen", fake_urlopen)
    message = EmailMessage("Код: 123456", "Сәлем!", "PoliglotAi <me@gmail.com>", ["learner@mail.kz"])
    assert get_connection("users.email_backends.AppsScriptEmailBackend").send_messages([message]) == 1
    body = json.loads(calls[0].data)
    assert body == {
        "secret": "s3cret",
        "to": "learner@mail.kz",
        "subject": "Код: 123456",
        "body": "Сәлем!",
        "name": "PoliglotAi",
    }


def test_gmail_script_refusal_is_an_error(settings, monkeypatch):
    settings.GMAIL_SCRIPT_URL = "https://script.google.com/macros/s/x/exec"
    monkeypatch.setattr(
        email_backends.urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse(b'{"ok": false, "error": "wrong secret"}'),
    )
    with pytest.raises(RuntimeError, match="wrong secret"):
        get_connection("users.email_backends.AppsScriptEmailBackend").send_messages(
            [EmailMessage("s", "b", "a@b.kz", ["c@d.kz"])]
        )
