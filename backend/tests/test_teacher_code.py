import pytest

pytestmark = pytest.mark.django_db

URL = "/api/auth/become-teacher/"


def test_the_right_code_opens_the_teachers_cabinet(client, user, settings):
    settings.TEACHER_INVITE_CODE = "MUGALIM-2026"
    r = client.post(URL, {"code": " mugalim-2026 "}, format="json")
    assert r.status_code == 200 and r.json()["is_teacher"] is True
    assert client.get("/api/teacher/groups/").status_code == 200


def test_a_wrong_code_is_refused_and_tries_are_limited(client, user, settings):
    settings.TEACHER_INVITE_CODE = "MUGALIM-2026"
    for _ in range(5):
        assert client.post(URL, {"code": "GUESS"}, format="json").status_code == 400
    assert client.post(URL, {"code": "MUGALIM-2026"}, format="json").status_code == 429
    user.refresh_from_db()
    assert not user.is_teacher


def test_without_a_configured_code_nobody_becomes_a_teacher(client, user, settings):
    settings.TEACHER_INVITE_CODE = ""
    assert client.post(URL, {"code": ""}, format="json").status_code == 400
    user.refresh_from_db()
    assert not user.is_teacher


def test_anonymous_cannot_use_it(anon, settings):
    settings.TEACHER_INVITE_CODE = "X"
    assert anon.post(URL, {"code": "X"}, format="json").status_code == 401
