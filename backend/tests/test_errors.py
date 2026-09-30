import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_unexpected_error_is_json(client, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("bug")

    monkeypatch.setattr("progress.views.streak_days", boom)
    client.raise_request_exception = False
    r = client.get("/api/progress/")
    assert r.status_code == 500
    assert r["Content-Type"].startswith("application/json")
    assert r.json()["code"] == "server_error" and "Серверде қате" in r.json()["detail"]


def test_unknown_api_address_is_json_404(settings):
    settings.DEBUG = False
    r = APIClient().get("/api/no-such-thing/")
    assert r.status_code == 404
    assert r.json() == {"detail": "Мұндай бет немесе дерек жоқ.", "code": "not_found"}


def test_errors_carry_a_code(anon, client):
    assert anon.get("/api/verbs/").json()["code"] == "not_authenticated"
    assert client.get("/api/verbs/999999/forms/").json()["code"] == "not_found"
    bad = client.post("/api/trainer/check/", {"verb_id": 1}, format="json").json()
    assert bad["code"] == "invalid" and "pronoun" in bad
