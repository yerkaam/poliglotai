import os

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from users.models import Profile, User


class Command(BaseCommand):
    help = (
        "Creates (or updates the password of) the site administrator from ADMIN_EMAIL and ADMIN_PASSWORD, "
        "for hosts without a shell. Runs at every start of the Docker image; does nothing if they are unset."
    )

    def handle(self, **options):
        email = os.environ.get("ADMIN_EMAIL", "").lower().strip()
        password = os.environ.get("ADMIN_PASSWORD", "")
        if not (email and password):
            return
        try:
            password_validation.validate_password(password)
        except ValidationError as exc:
            # Never stop the site from starting over this: say why and go on.
            self.stderr.write(f"Admin account skipped: {' '.join(exc.messages)}")
            return
        user = User.objects.filter(email=email).first()
        if user is None:
            user = User.objects.create_superuser(email=email, password=password, name="Admin")
        else:
            user.set_password(password)
            user.is_staff = user.is_superuser = True
        user.email_verified = True
        user.save()
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.onboarded = True
        profile.reminder_enabled = False
        profile.save()
        self.stdout.write(f"Admin account is ready: {email} (log in at /admin/)")
