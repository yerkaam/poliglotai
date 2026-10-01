import pytest

from users.models import Profile
from vocabulary.placement import QUESTIONS

pytestmark = pytest.mark.django_db


def _answers(right_steps):
    return [q["answer"] if step in right_steps else "" for step, q in QUESTIONS]


def test_the_questions_go_without_answers_easy_to_hard(client):
    questions = client.get("/api/placement/").json()["questions"]
    assert len(questions) >= 20
    assert all("answer" not in q for q in questions)
    steps = [q["step"] for q in questions]
    assert steps == sorted(steps) and steps[0] == 1


def test_a_beginner_stays_a0_and_starts_at_step_1(client, user):
    r = client.post("/api/placement/", {"answers": []}, format="json").json()
    assert (r["level"], r["steps_credited"], r["score"]) == ("A0", [], 0)
    assert [s["status"] for s in client.get("/api/course/").json()[:2]] == ["open", "locked"]


def test_known_steps_are_credited_up_to_the_first_gap(client, user):
    r = client.post("/api/placement/", {"answers": _answers({1, 2, 3, 5})}, format="json").json()
    assert r["level"] == "A1" and r["steps_credited"] == [1, 2, 3]  # step 4 missed: 5 is not credited
    statuses = [s["status"] for s in client.get("/api/course/").json()[:5]]
    assert statuses == ["done", "done", "done", "open", "locked"]
    assert Profile.objects.get(user=user).level == "A1"


def test_a_weaker_retake_never_takes_steps_or_level_away(client, user):
    Profile.objects.filter(user=user).update(onboarded=True)
    client.post("/api/placement/", {"answers": _answers({1, 2})}, format="json")
    client.post("/api/placement/", {"answers": []}, format="json")
    assert [s["status"] for s in client.get("/api/course/").json()[:3]] == ["done", "done", "open"]
    assert Profile.objects.get(user=user).level == "A1"


def test_every_question_has_one_right_option():
    for step, q in QUESTIONS:
        assert q["answer"] in q["options"] and len(set(q["options"])) == len(q["options"]), step
