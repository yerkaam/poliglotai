from io import StringIO

import pytest
from django.core.management import call_command
from django.test import Client

from users.models import User

pytestmark = pytest.mark.django_db


def test_admin_from_the_environment_can_open_the_admin_site(monkeypatch, settings):
    # The admin's CSS is collected at image build time; tests have no manifest.
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    call_command("ensure_admin", stdout=StringIO())
    assert not User.objects.exists()  # nothing configured: nothing happens

    monkeypatch.setenv("ADMIN_EMAIL", "Owner@Mail.kz")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin2026pass")
    out = StringIO()
    call_command("ensure_admin", stdout=out)
    assert "admin2026pass" not in out.getvalue()
    browser = Client()
    assert browser.login(email="owner@mail.kz", password="admin2026pass")
    assert browser.get("/admin/users/user/").status_code == 200

    monkeypatch.setenv("ADMIN_PASSWORD", "newpass2026x")
    call_command("ensure_admin", stdout=StringIO())
    assert User.objects.count() == 1 and User.objects.get().check_password("newpass2026x")


def test_a_weak_admin_password_is_skipped(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "owner@mail.kz")
    monkeypatch.setenv("ADMIN_PASSWORD", "123")
    err = StringIO()
    call_command("ensure_admin", stdout=StringIO(), stderr=err)
    assert "skipped" in err.getvalue() and not User.objects.exists()
