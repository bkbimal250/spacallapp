from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from apps.doubletick.models import DoubleTickLead


class Command(BaseCommand):
    help = "Backfill DoubleTick lead duplicates based on normalized_phone."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Do not persist changes; just report")
        parser.add_argument("--limit", type=int, default=0, help="Limit number of phone groups to process (0 = all)")
        parser.add_argument("--older-than-days", type=int, default=0, help="Only consider leads older than given days")

    def handle(self, *args, **options):
        dry_run = options.get("dry_run")
        limit = options.get("limit") or 0
        older_days = options.get("older_than_days") or 0

        cutoff = None
        if older_days > 0:
            cutoff = timezone.now() - timedelta(days=older_days)

        qs = DoubleTickLead.objects.values("normalized_phone").exclude(normalized_phone="").order_by("normalized_phone")
        if cutoff:
            qs = DoubleTickLead.objects.filter(created_at__lt=cutoff).values("normalized_phone").exclude(normalized_phone="").order_by("normalized_phone")

        phone_groups = []
        last = None
        for row in qs.distinct():
            phone_groups.append(row["normalized_phone"])
            if limit and len(phone_groups) >= limit:
                break

        total_groups = len(phone_groups)
        self.stdout.write(f"Found {total_groups} normalized_phone groups to inspect")

        processed = 0
        duplicates_marked = 0
        for phone in phone_groups:
            leads = DoubleTickLead.objects.filter(normalized_phone=phone).order_by("created_at")
            if leads.count() < 2:
                continue
            canonical = leads.first()
            others = leads.exclude(id=canonical.id)
            processed += 1
            for other in others:
                if other.is_duplicate and other.duplicate_of_id:
                    continue
                duplicates_marked += 1
                if dry_run:
                    self.stdout.write(f"[dry-run] Would mark lead {other.id} duplicate_of {canonical.id} (phone={phone})")
                else:
                    try:
                        with transaction.atomic():
                            other.is_duplicate = True
                            other.duplicate_of = canonical
                            other.save(update_fields=["is_duplicate", "duplicate_of", "updated_at"])
                    except Exception as exc:
                        self.stderr.write(f"Failed to mark lead {other.id} as duplicate: {exc}")

        self.stdout.write(f"Processed groups: {processed}; duplicates flagged: {duplicates_marked}")
