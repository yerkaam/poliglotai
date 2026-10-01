import secrets
import string

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
        "python manage.py create_demo_accounts"
    )

    def add_arguments(self, parser):
        parser.add_argument("--student-email", default="student@poliglot.test")
        parser.add_argument("--teacher-email", default="teacher@poliglot.test")

    @transaction.atomic
    def handle(self, student_email, teacher_email, **options):
        student, student_password = self._account(student_email, "Оқушы (демо)", teacher=False)
        teacher, teacher_password = self._account(teacher_email, "Мұғалім (демо)", teacher=True)
        group = Group.objects.filter(teacher=teacher, name=GROUP_NAME).first() or Group.objects.create(
            teacher=teacher, name=GROUP_NAME
        )
        Membership.objects.get_or_create(group=group, student=student)

        self.stdout.write("Demo accounts are ready (passwords are shown only now):")
        self.stdout.write(f"  learner: {student.email}  password: {student_password}")
        self.stdout.write(f"  teacher: {teacher.email}  password: {teacher_password}")
        self.stdout.write(f"  group «{group.name}», join code: {group.code}")

    def _account(self, email, name, *, teacher):
        email = email.lower().strip()
        password = _password()
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
        return user, password
