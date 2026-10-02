import pytest

from config import monitoring


def test_before_send_drops_personal_data():
    event = {
        "request": {
            "url": "https://x/api/auth/login/",
            "data": {"email": "a@b.kz", "password": "secret"},
            "cookies": {"access": "jwt"},
            "query_string": "token=abc",
            "headers": {"Cookie": "access=jwt", "X-CSRFToken": "t", "User-Agent": "UA"},
        },
        "user": {"id": 7, "email": "a@b.kz", "ip_address": "1.2.3.4"},
        "extra": {"payload": {"text": "my chat message", "password": "p", "step": 3}},
    }
    out = monitoring.before_send(event, {})
    assert "data" not in out["request"] and "cookies" not in out["request"]
    assert out["request"]["query_string"] == monitoring.REDACTED
    assert out["request"]["headers"]["Cookie"] == monitoring.REDACTED
    assert out["request"]["headers"]["X-CSRFToken"] == monitoring.REDACTED
    assert out["request"]["headers"]["User-Agent"] == "UA"
    assert out["user"] == {"id": 7}
    assert out["extra"]["payload"] == {"text": monitoring.REDACTED, "password": monitoring.REDACTED, "step": 3}


def test_init_is_off_without_dsn():
    assert monitoring.init("", "test") is False


def test_release_prefers_explicit_value(monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "0123456789abcdef")
    monkeypatch.delenv("SENTRY_RELEASE", raising=False)
    assert monitoring.release() == "0123456789ab"
    monkeypatch.setenv("SENTRY_RELEASE", "v1")
    assert monitoring.release() == "v1"


@pytest.mark.django_db
def test_client_config(client, settings):
    settings.SENTRY_FRONTEND_DSN = "https://key@o1.ingest.sentry.io/2"
    settings.SENTRY_ENVIRONMENT = "production"
    data = client.get("/api/config/").json()
    assert data["sentry_dsn"] == "https://key@o1.ingest.sentry.io/2"
    assert data["environment"] == "production"
    settings.SENTRY_FRONTEND_DSN = ""
    assert client.get("/api/config/").json()["sentry_dsn"] == ""
