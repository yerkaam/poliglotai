from django.core.management.base import BaseCommand

from users.reminders import send_due


class Command(BaseCommand):
    help = "Sends the daily reminder emails that are due now. Run it every hour (cron)."

    def handle(self, *args, **options):
        self.stdout.write(f"Reminders sent: {send_due()}")
