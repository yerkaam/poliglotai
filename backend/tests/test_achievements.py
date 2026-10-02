from datetime import datetime, timedelta

import pytest
from django.core import mail
from django.utils import timezone

from progress.achievements import best_streak
from progress.models import Achievement, ProgressLog
from srs.models import UserVocabulary
from trainer.models import TrainerAttempt
from users.models import Profile
from users.reminders import send_weekly
from vocabulary.models import Vocabulary

pytestmark = pytest.mark.django_db


def _days_ago(n):
    return timezone.localdate() - timedelta(days=n)


def test_best_streak_counts_the_longest_run_of_days():
    today = timezone.localdate()
    days = {today - timedelta(days=n) for n in (0, 1, 2, 5, 6, 7, 8)}
    assert best_streak(days) == 4
    assert best_streak(set()) == 0


def test_first_word_is_celebrated_once(client, user):
    word = Vocabulary.objects.filter(course_step__number=1).first()
    client.post(f"/api/srs/{word.id}/answer/", {"answer": "start"}, format="json")
    new = client.get("/api/progress/").json()["new_achievements"]
    assert [a["key"] for a in new] == ["first_word"] and new[0]["title_kk"]
    assert client.post("/api/achievements/seen/").status_code == 204
    assert client.get("/api/progress/").json()["new_achievements"] == []


def test_badges_show_progress_toward_the_target(client, user):
    for n in range(3):
        ProgressLog.objects.create(user=user, date=_days_ago(n), reviews=1)
    for _ in range(12):
        TrainerAttempt.objects.create(
            user=user,
            vocabulary=Vocabulary.objects.get(word="go"),
            pronoun="I",
            tense="past",
            form="affirmative",
            answer="I went.",
            expected="I went.",
            correct=True,
        )
    badges = {b["key"]: b for b in client.get("/api/achievements/").json()}
    assert badges["streak_3"]["unlocked_at"] and not badges["streak_7"]["unlocked_at"]
    assert badges["streak_7"]["current"] == 3 and badges["streak_7"]["target"] == 7
    assert badges["trainer_row_10"]["unlocked_at"]
    assert badges["trainer_50"]["current"] == 12


def test_badges_stay_after_a_progress_reset(client, user):
    Achievement.objects.create(user=user, key="first_word", seen=True)
    client.post("/api/progress/reset/", {"confirm": True}, format="json")
    assert Achievement.objects.filter(user=user, key="first_word").exists()


def test_the_week_day_by_day_against_the_week_before(client, user):
    ProgressLog.objects.create(user=user, date=_days_ago(0), reviews=4, trainer_total=6)
    ProgressLog.objects.create(user=user, date=_days_ago(2), new_words=5)
    ProgressLog.objects.create(user=user, date=_days_ago(9), reviews=3)
    week = client.get("/api/progress/week/").json()
    assert len(week["days"]) == 7 and week["days"][-1]["date"] == str(_days_ago(0))
    assert week["days"][-1]["total"] == 10 and week["days"][-3]["total"] == 5
    assert (week["total"], week["previous_total"], week["active_days"]) == (15, 3, 2)
    assert week["days"][-1]["weekday_kk"] in {"Дс", "Сс", "Ср", "Бс", "Жм", "Сб", "Жс"}


def test_the_weekly_summary_goes_out_on_sunday(user):
    Profile.objects.filter(user=user).update(onboarded=True)
    today = timezone.localdate()
    sunday = today + timedelta(days=(6 - today.weekday()))
    ProgressLog.objects.create(user=user, date=sunday - timedelta(days=1), reviews=7)
    UserVocabulary.objects.create(user=user, vocabulary=Vocabulary.objects.get(word="buy"))
    at = timezone.make_aware(datetime(sunday.year, sunday.month, sunday.day, 19, 10))
    assert send_weekly(at - timedelta(days=1)) == 0  # Saturday
    assert send_weekly(at) == 1
    assert send_weekly(at) == 0  # once
    body = mail.outbox[0].body
    assert "Апта қорытындысы" in body and "/progress" in body and "Белсенді күндер" in body


def test_a_reset_restarts_the_course_but_keeps_todays_ai_limit(client, user):
    from vocabulary.models import CourseStep, StepResult

    StepResult.objects.create(user=user, step=CourseStep.objects.get(number=1), passed=True, best_percent=100)
    ProgressLog.objects.create(user=user, date=_days_ago(0), chat_requests=7, reviews=3)
    client.post("/api/progress/reset/", {"confirm": True}, format="json")
    assert not StepResult.objects.filter(user=user).exists()
    log = ProgressLog.objects.get(user=user)
    assert log.chat_requests == 7 and log.reviews == 0
