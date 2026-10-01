from datetime import datetime, timedelta

import pytest
from django.core import mail
from django.core.management import call_command
from django.utils import timezone

from progress.models import ProgressLog
from users.models import Profile, User
from users.reminders import send_due, unsubscribe_token

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db


def _at(hour):
    today = timezone.localdate()
    return timezone.make_aware(datetime(today.year, today.month, today.day, hour, 5))


def _learner(email="dana@mail.kz", studied_days_ago=(1, 2), **profile):
    user = User.objects.create_user(email=email, password=PASSWORD, name="Дана", email_verified=True)
    Profile.objects.filter(user=user).update(onboarded=True, **profile)
    today = timezone.localdate()
    for days in studied_days_ago:
        ProgressLog.objects.create(user=user, date=today - timedelta(days=days), reviews=5)
    return user


def test_a_learner_who_has_not_studied_today_gets_one_reminder_at_their_hour():
    _learner()
    assert send_due(_at(18)) == 0  # 19:00 by default
    assert send_due(_at(19)) == 1
    email = mail.outbox[0]
    assert email.to == ["dana@mail.kz"]
    assert "2 күн қатарынан" in email.body and "/words" in email.body
    assert "List-Unsubscribe" in email.extra_headers
    assert send_due(_at(21)) == 0  # once a day


def test_no_reminder_after_studying_today_or_for_learners_who_left():
    studied = _learner("a@mail.kz")
    ProgressLog.objects.create(user=studied, date=timezone.localdate(), trainer_total=3)
    _learner("b@mail.kz", studied_days_ago=(10,))  # gone for over a week
    _learner("c@mail.kz", reminder_enabled=False)
    _learner("d@mail.kz", reminder_hour=21)
    assert send_due(_at(20)) == 0
    assert send_due(_at(21)) == 1 and mail.outbox[0].to == ["d@mail.kz"]


def test_the_command_sends_the_due_reminders(capsys):
    _learner()
    call_command("send_reminders")
    out = capsys.readouterr().out
    assert out.startswith("Reminders sent:")


def test_one_click_unsubscribe(anon):
    user = _learner()
    r = anon.get(f"/api/auth/reminders/unsubscribe/?token={unsubscribe_token(user)}")
    assert r.status_code == 200 and "өшірілді" in r.content.decode()
    assert not Profile.objects.get(user=user).reminder_enabled
    assert anon.post("/api/auth/reminders/unsubscribe/?token=forged").status_code == 400


def test_the_learner_chooses_the_hour_or_turns_reminders_off(client, user):
    r = client.patch("/api/auth/profile/", {"reminder_hour": 8, "reminder_enabled": False}, format="json")
    assert r.status_code == 200
    assert r.json()["profile"]["reminder_hour"] == 8 and r.json()["profile"]["reminder_enabled"] is False
    assert client.patch("/api/auth/profile/", {"reminder_hour": 3}, format="json").status_code == 400
