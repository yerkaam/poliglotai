import os
import secrets
import string

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import transaction

from classroom.models import Group, Membership
from users.models import Profile, User

GROUP_NAME = "Демо-топ"


def _password() -> str:
    """Easy to type on a phone: lowercase letters and digits, 12 characters, at least two digits."""
    letters = "".join(secrets.choice(string.ascii_lowercase) for _ in range(9))
    digits = "".join(secrets.choice(string.digits) for _ in range(3))
    return letters + digits


class Command(BaseCommand):
    help = (
        "Creates a ready-to-use learner and teacher (email confirmed, onboarding done, the learner in the "
        "teacher's group) and prints their passwords. Run again to set new passwords: "
        "python manage.py create_demo_accounts. With --from-env (run at every start of the Docker image) the "
        "passwords come from DEMO_STUDENT_PASSWORD and DEMO_TEACHER_PASSWORD and nothing happens if they are unset."
    )

    def add_arguments(self, parser):
        parser.add_argument("--student-email", default="student@poliglot.test")
        parser.add_argument("--teacher-email", default="teacher@poliglot.test")
        parser.add_argument("--from-env", action="store_true")

    def handle(self, student_email, teacher_email, from_env=False, **options):
        if from_env:
            self._from_env()
            return
        self._create(student_email, _password(), teacher_email, _password(), show_passwords=True)

    def _from_env(self):
        """Hosts without a shell (Render's free plan): the owner sets the passwords in the environment."""
        student_password = os.environ.get("DEMO_STUDENT_PASSWORD", "")
        teacher_password = os.environ.get("DEMO_TEACHER_PASSWORD", "")
        if not (student_password and teacher_password):
            return
        for password in (student_password, teacher_password):
            try:
                password_validation.validate_password(password)
            except ValidationError as exc:
                # Never stop the site from starting over a demo account: say why and go on.
                self.stderr.write(f"Demo accounts skipped: {' '.join(exc.messages)}")
                return
        self._create(
            os.environ.get("DEMO_STUDENT_EMAIL", "student@poliglot.test"),
            student_password,
            os.environ.get("DEMO_TEACHER_EMAIL", "teacher@poliglot.test"),
            teacher_password,
            show_passwords=False,  # they are in the environment already; keep them out of the logs
        )

    @transaction.atomic
    def _create(self, student_email, student_password, teacher_email, teacher_password, *, show_passwords):
        student = self._account(student_email, "Оқушы (демо)", student_password, teacher=False)
        teacher = self._account(teacher_email, "Мұғалім (демо)", teacher_password, teacher=True)
        group = Group.objects.filter(teacher=teacher, name=GROUP_NAME).first() or Group.objects.create(
            teacher=teacher, name=GROUP_NAME
        )
        Membership.objects.get_or_create(group=group, student=student)

        if show_passwords:
            self.stdout.write("Demo accounts are ready (passwords are shown only now):")
            self.stdout.write(f"  learner: {student.email}  password: {student_password}")
            self.stdout.write(f"  teacher: {teacher.email}  password: {teacher_password}")
        else:
            self.stdout.write(f"Demo accounts are ready: {student.email}, {teacher.email}")
        self.stdout.write(f"  group «{group.name}», join code: {group.code}")

    def _account(self, email, name, password, *, teacher):
        email = email.lower().strip()
        user = User.objects.filter(email=email).first()
        if user is None:
            user = User.objects.create_user(email=email, password=password, name=name)
        else:
            user.set_password(password)
        user.email_verified = True
        user.is_teacher = teacher or user.is_teacher
        user.save()
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.onboarded = True
        # Demo addresses do not receive mail: no reminders to them.
        profile.reminder_enabled = False
        profile.save()
        return user
