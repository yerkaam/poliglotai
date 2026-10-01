import re
from io import StringIO

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from classroom.models import Membership
from users.models import User

pytestmark = pytest.mark.django_db


def _run() -> dict:
    out = StringIO()
    call_command("create_demo_accounts", stdout=out)
    text = out.getvalue()
    return dict(re.findall(r"(\S+@\S+)\s+password: (\S+)", text))


def test_demo_learner_and_teacher_can_log_in_and_are_linked():
    passwords = _run()
    student = User.objects.get(email="student@poliglot.test")
    teacher = User.objects.get(email="teacher@poliglot.test")
    assert student.email_verified and student.profile.onboarded and not student.is_teacher
    assert teacher.is_teacher and teacher.email_verified
    assert Membership.objects.filter(student=student, group__teacher=teacher).exists()
    for email, password in passwords.items():
        r = APIClient().post("/api/auth/login/", {"email": email, "password": password}, format="json")
        assert r.status_code == 200, email
    assert (
        APIClient()
        .post(
            "/api/auth/login/",
            {"email": "teacher@poliglot.test", "password": passwords["teacher@poliglot.test"]},
            format="json",
        )
        .json()["is_teacher"]
    )


def test_running_again_sets_new_passwords_without_duplicates():
    first = _run()
    second = _run()
    assert first != second
    assert User.objects.filter(email__endswith="@poliglot.test").count() == 2
    assert Membership.objects.count() == 1
