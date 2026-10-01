from django.core.management.base import BaseCommand, CommandError

from users.models import User


class Command(BaseCommand):
    help = "Gives (or with --revoke takes away) the teacher role: python manage.py grant_teacher name@mail.kz"

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument("--revoke", action="store_true")

    def handle(self, email, revoke=False, **options):
        updated = User.objects.filter(email=email.lower().strip()).update(is_teacher=not revoke)
        if not updated:
            raise CommandError(f"No user with the email {email}")
        self.stdout.write(f"{email}: {'no longer a teacher' if revoke else 'teacher'}")
