from datetime import timedelta

import pytest
from django.utils import timezone

from chat.llm import build_system_prompt
from srs.models import UserVocabulary
from vocabulary import course, forms
from vocabulary.course_content import STEPS
from vocabulary.models import CourseStep, Vocabulary

pytestmark = pytest.mark.django_db


def _right_answers(number):
    return [course.right_answer(e) for e in CourseStep.objects.get(number=number).exercises]


def _start_words(user, number):
    yesterday = timezone.localdate() - timedelta(days=1)  # started earlier: today's new-word limit stays free
    for vocab in Vocabulary.objects.filter(course_step__number=number):
        UserVocabulary.objects.get_or_create(user=user, vocabulary=vocab, defaults={"started_on": yesterday})


def test_a_new_learner_has_only_the_first_step(client):
    steps = client.get("/api/course/").json()
    assert [s["status"] for s in steps[:3]] == ["open", "locked", "locked"]
    assert all(s["status"] == "locked" for s in steps[1:])
    assert client.get("/api/course/2/").status_code == 403


def test_the_lesson_never_sends_the_answers(client):
    step = client.get("/api/course/1/").json()
    assert step["lesson"] and step["exercises"]
    assert all("answer" not in e and "answers" not in e for e in step["exercises"])
    assert len(step["words"]) == 40


def test_passing_the_check_opens_the_next_step(client):
    r = client.post("/api/course/1/check/", {"answers": _right_answers(1)}, format="json").json()
    assert r["passed"] and r["percent"] == 100
    assert r["opened_step"] == 2
    assert r["step"]["status"] == "done"
    steps = client.get("/api/course/").json()
    assert [s["status"] for s in steps[:3]] == ["done", "open", "locked"]


def test_lessons_are_short_and_each_has_practice(client):
    step = client.get("/api/course/1/").json()
    assert step["intro_kk"] and step["lessons_total"] == len(step["lesson"]) >= 6
    taught = [b for b in step["lesson"] if b["practice"]]
    assert len(taught) >= 6
    assert all(q["answer"] in q["options"] and q["why_kk"] for b in taught for q in b["practice"])


def test_the_learner_resumes_at_the_last_lesson(client):
    assert client.post("/api/course/1/lessons/", {"done": 3}, format="json").json() == {"lessons_done": 3}
    assert client.post("/api/course/1/lessons/", {"done": 1}, format="json").json() == {"lessons_done": 3}
    total = client.get("/api/course/1/").json()["lessons_total"]
    assert client.post("/api/course/1/lessons/", {"done": 99}, format="json").json() == {"lessons_done": total}
    assert client.get("/api/course/").json()[0]["lessons_done"] == total
    assert client.post("/api/course/2/lessons/", {"done": 1}, format="json").status_code == 403


def test_a_failed_check_shows_the_right_answers_and_keeps_the_best_score(client):
    answers = _right_answers(1)
    r = client.post("/api/course/1/check/", {"answers": answers[:4]}, format="json").json()
    assert not r["passed"] and r["percent"] < course.PASS_PERCENT
    assert [i["correct"] for i in r["items"]][4:] == [False] * (len(answers) - 4)
    assert r["items"][-1]["right"] == answers[-1]

    client.post("/api/course/1/check/", {"answers": []}, format="json")
    assert client.get("/api/course/").json()[0]["quiz_best"] == r["percent"]


def test_typed_answers_ignore_case_punctuation_and_contractions(client):
    answers = _right_answers(1)
    answers[4] = "i did not buy a car."  # "I didn't buy a car"
    r = client.post("/api/course/1/check/", {"answers": answers}, format="json").json()
    assert r["items"][4]["correct"]


def test_words_of_the_next_step_come_after_it_opens(client, user):
    _start_words(user, 1)
    assert {w["source"] for w in client.get("/api/srs/today/").json()["new"]} == {"wiktionary"}

    client.post("/api/course/1/check/", {"answers": _right_answers(1)}, format="json")
    new = client.get("/api/srs/today/").json()["new"]
    assert {w["course_step"] for w in new} == {CourseStep.objects.get(number=2).id}


def test_the_tutor_waits_for_continuous_until_step_8():
    prompt = build_system_prompt(level="A0", steps=[], verbs=[], mode="free", done_numbers={1, 2})
    assert "Never use Continuous forms, Perfect forms, the passive voice." in prompt
    prompt = build_system_prompt(
        level="A1", steps=[], verbs=[], mode="free", grammar=["Present Continuous"], done_numbers=set(range(1, 10))
    )
    assert "Never use the passive voice." in prompt and "Present Continuous" in prompt


def test_every_step_has_content_and_valid_checks():
    for number, content in STEPS.items():
        assert content["lesson"] and len(content["exercises"]) >= 5, number
        assert sum(len(b["practice"]) for b in content["lesson"]) >= len(content["lesson"]) - 1, number
        for e in content["exercises"]:
            if e["type"] == "choice":
                assert e["answer"] in e["options"] and len(set(e["options"])) == len(e["options"])
            else:
                assert e["answers"] and all(forms.normalize(a) for a in e["answers"])


def test_irregular_verbs_of_step_6_build_their_past_forms():
    verbs = Vocabulary.objects.filter(course_step__number=6)
    assert verbs.count() >= 40
    for vocab in verbs:
        past = forms.table(vocab, "I")[7]["text"]
        assert past == f"I {vocab.past_form}.", vocab.word
