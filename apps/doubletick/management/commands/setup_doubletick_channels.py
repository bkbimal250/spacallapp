from django.core.management.base import BaseCommand

from apps.doubletick.channel_setup import setup_default_channels


class Command(BaseCommand):
    help = "Create or update default DoubleTick WABA channels safely."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show changes without writing to the database.")
        parser.add_argument("--only-missing", action="store_true", help="Create missing channels only; do not update existing records.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        only_missing = options["only_missing"]

        stats, actions = setup_default_channels(dry_run=dry_run, only_missing=only_missing)

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: no database changes were written."))

        for action, waba_number, detail in actions:
            style = self.style.SUCCESS if action == "created" else self.style.WARNING if action == "updated" else (lambda value: value)
            self.stdout.write(style(f"{action.upper():8} {waba_number} {detail}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"DoubleTick channels: created={stats['created']} updated={stats['updated']} skipped={stats['skipped']}"
        ))
