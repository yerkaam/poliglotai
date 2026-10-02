import pytest
from rest_framework.test import APIClient

from chat.models import Conversation, Message
from classroom.models import Group, Membership
from trainer.models import TrainerAttempt
from users.models import User
from vocabulary.models import Vocabulary

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db


def _login(email, teacher=False):
    user = User.objects.create_user(email=email, password=PASSWORD, name=email.split("@")[0], email_verified=True)
    user.is_teacher = teacher
    user.save()
    api = APIClient()
    api.post("/api/auth/login/", {"email": email, "password": PASSWORD}, format="json")
    return user, api


@pytest.fixture
def teacher():
    return _login("teacher@mail.kz", teacher=True)


def test_only_teachers_have_the_cabinet(client):
    assert client.get("/api/teacher/groups/").status_code == 403
    assert client.post("/api/teacher/groups/", {"name": "7A"}, format="json").status_code == 403


def test_a_learner_joins_with_the_code_and_the_teacher_sees_progress_not_chats(teacher, user, client):
    t_user, t_api = teacher
    group = t_api.post("/api/teacher/groups/", {"name": "7А сынып"}, format="json").json()
    assert len(group["code"]) == 6

    r = client.post("/api/groups/join/", {"code": group["code"].lower()}, format="json")
    assert r.status_code == 201 and r.json()["teacher"] == t_user.name
    assert client.get("/api/groups/").json()[0]["name"] == "7А сынып"

    go = Vocabulary.objects.get(word="go")
    TrainerAttempt.objects.create(
        user=user,
        vocabulary=go,
        pronoun="I",
        tense="past",
        form="negative",
        answer="I didn't went.",
        expected="I didn't go.",
        correct=False,
    )
    conv = Conversation.objects.create(user=user, mode=Conversation.Mode.FREE)
    Message.objects.create(
        conversation=conv,
        role=Message.Role.USER,
        text="My secret text",
        corrections=[{"tense": "past", "form": "negative", "wrong": "went", "right": "go"}],
    )
    detail = t_api.get(f"/api/teacher/groups/{group['id']}/").json()
    assert detail["students"] == 1
    row = detail["rows"][0]
    assert row["name"] == user.name and row["current_step"] == 1 and row["accuracy_30d"] == 0
    assert detail["mistakes"][0]["label_kk"] == "Өткен шақ · болымсыз"
    assert detail["mistakes"][0]["mistakes"] == 2 and detail["mistakes"][0]["learners"] == 1
    assert "secret" not in str(detail)


def test_other_teachers_cannot_see_the_group(teacher):
    _, t_api = teacher
    gid = t_api.post("/api/teacher/groups/", {"name": "A"}, format="json").json()["id"]
    _, other = _login("other@mail.kz", teacher=True)
    assert other.get(f"/api/teacher/groups/{gid}/").status_code == 404


def test_a_new_code_stops_the_old_one(teacher, client):
    _, t_api = teacher
    group = t_api.post("/api/teacher/groups/", {"name": "A"}, format="json").json()
    fresh = t_api.post(f"/api/teacher/groups/{group['id']}/code/").json()["code"]
    assert fresh != group["code"]
    assert client.post("/api/groups/join/", {"code": group["code"]}, format="json").status_code == 400
    assert client.post("/api/groups/join/", {"code": fresh}, format="json").status_code == 201


def test_leaving_and_being_removed(teacher, user, client):
    _, t_api = teacher
    group = t_api.post("/api/teacher/groups/", {"name": "A"}, format="json").json()
    client.post("/api/groups/join/", {"code": group["code"]}, format="json")
    assert client.delete(f"/api/groups/{group['id']}/").status_code == 204
    assert not Membership.objects.exists()
    client.post("/api/groups/join/", {"code": group["code"]}, format="json")
    t_api.delete(f"/api/teacher/groups/{group['id']}/students/{user.id}/")
    assert client.get("/api/groups/").json() == []


def test_guessing_codes_is_limited(client):
    for _ in range(10):
        assert client.post("/api/groups/join/", {"code": "ZZZZZZ"}, format="json").status_code == 400
    assert client.post("/api/groups/join/", {"code": "ZZZZZZ"}, format="json").status_code == 429


def test_me_says_who_is_a_teacher(teacher, client):
    _, t_api = teacher
    assert t_api.get("/api/auth/me/").json()["is_teacher"] is True
    assert client.get("/api/auth/me/").json()["is_teacher"] is False
    assert Group.objects.count() == 0


def test_the_command_grants_and_revokes_the_role(user):
    from django.core.management import call_command

    call_command("grant_teacher", user.email)
    user.refresh_from_db()
    assert user.is_teacher
    call_command("grant_teacher", user.email, "--revoke")
    user.refresh_from_db()
    assert not user.is_teacher
