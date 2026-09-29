from pathlib import Path

from django.core.management.base import BaseCommand

from vocabulary.models import Vocabulary
from vocabulary.wiktionary import DATA_FILE, load


class Command(BaseCommand):
    help = "Loads English–Kazakh words from the Wiktionary extract into the vocabulary table."

    def add_arguments(self, parser):
        parser.add_argument("--file", type=Path, default=DATA_FILE)
        parser.add_argument("--limit", type=int, default=None, help="Only the N most frequent words")

    def handle(self, *args, file, limit, **options):
        result = load(Vocabulary, file, limit)
        self.stdout.write(self.style.SUCCESS(f"Wiktionary: {result}"))
