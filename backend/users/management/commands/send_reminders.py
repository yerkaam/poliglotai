from django.core.management.base import BaseCommand

from users.reminders import send_due, send_weekly


class Command(BaseCommand):
    help = "Sends the daily reminders and, on Sundays, the weekly summaries that are due now. Run it hourly."

    def handle(self, *args, **options):
        self.stdout.write(f"Reminders sent: {send_due()}, weekly summaries sent: {send_weekly()}")
