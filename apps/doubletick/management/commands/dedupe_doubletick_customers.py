from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Count

from apps.doubletick.models import (
    DoubleTickConversation,
    DoubleTickCustomer,
    DoubleTickLead,
    DoubleTickMessage,
)


class Command(BaseCommand):
    help = "Merge duplicate DoubleTick customers after reviewing with --dry-run."

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument("--dry-run", action="store_true", help="Report duplicate groups without changing data.")
        mode.add_argument("--commit", action="store_true", help="Merge duplicate customers and reassign related rows.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        groups = self._duplicate_groups()
        if not groups:
            self.stdout.write(self.style.SUCCESS("No duplicate DoubleTickCustomer groups found."))
            return

        report = defaultdict(int)
        processed_duplicates = set()
        errors = []

        self.stdout.write("DoubleTickCustomer duplicate report")
        self.stdout.write("=" * 72)

        for reason, ids in groups:
            active_ids = [customer_id for customer_id in ids if customer_id not in processed_duplicates]
            if len(active_ids) < 2:
                continue
            try:
                result = self._merge_group(reason, active_ids, dry_run)
            except Exception as exc:
                errors.append(f"{reason}: {exc}")
                continue

            report["duplicate_groups"] += 1
            report["customers_merged"] += result["customers_merged"]
            report["conversations_reassigned"] += result["conversations_reassigned"]
            report["leads_reassigned"] += result["leads_reassigned"]
            report["messages_reassigned"] += result["messages_reassigned"]
            processed_duplicates.update(result["duplicate_ids"])

        report["errors"] = len(errors)
        for key in [
            "duplicate_groups",
            "customers_merged",
            "conversations_reassigned",
            "leads_reassigned",
            "messages_reassigned",
            "errors",
        ]:
            self.stdout.write(f"{key.replace('_', ' ').title():35s} {report[key]}")
        for error in errors:
            self.stdout.write(self.style.ERROR(error))

        if errors and options["commit"]:
            raise CommandError("Some duplicate groups failed to merge.")
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run only. No database rows were changed."))
        else:
            self.stdout.write(self.style.SUCCESS("Duplicate DoubleTick customers merged."))

    def _duplicate_groups(self):
        groups = []
        seen = set()

        phone_groups = (
            DoubleTickCustomer.objects.exclude(normalized_phone="")
            .values("channel_id", "normalized_phone")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
        )
        for group in phone_groups:
            ids = tuple(
                DoubleTickCustomer.objects.filter(
                    channel_id=group["channel_id"],
                    normalized_phone=group["normalized_phone"],
                )
                .order_by("created_at")
                .values_list("id", flat=True)
            )
            if ids and ids not in seen:
                seen.add(ids)
                groups.append((f"channel+normalized_phone:{group['channel_id']}:{group['normalized_phone']}", ids))

        provider_groups = (
            DoubleTickCustomer.objects.exclude(dt_customer_id="")
            .values("dt_customer_id")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
        )
        for group in provider_groups:
            ids = tuple(
                DoubleTickCustomer.objects.filter(dt_customer_id=group["dt_customer_id"])
                .order_by("created_at")
                .values_list("id", flat=True)
            )
            if ids and ids not in seen:
                seen.add(ids)
                groups.append((f"dt_customer_id:{group['dt_customer_id']}", ids))

        return groups

    def _canonical_customer(self, customers):
        def score(customer):
            return sum(
                1
                for value in [
                    customer.customer_name,
                    customer.whatsapp_name,
                    customer.dt_customer_id,
                    customer.normalized_phone,
                    customer.phone_number,
                    customer.channel_id,
                ]
                if value
            )

        return sorted(customers, key=lambda customer: (-score(customer), customer.created_at))[0]

    def _merge_group(self, reason, ids, dry_run):
        customers = list(DoubleTickCustomer.objects.filter(id__in=ids).order_by("created_at"))
        if len(customers) < 2:
            return defaultdict(int)

        canonical = self._canonical_customer(customers)
        duplicates = [customer for customer in customers if customer.id != canonical.id]
        duplicate_ids = [customer.id for customer in duplicates]

        result = {
            "customers_merged": len(duplicates),
            "conversations_reassigned": DoubleTickConversation.objects.filter(customer_id__in=duplicate_ids).count(),
            "leads_reassigned": DoubleTickLead.objects.filter(customer_id__in=duplicate_ids).count(),
            "messages_reassigned": DoubleTickMessage.objects.filter(customer_id__in=duplicate_ids).count(),
            "duplicate_ids": duplicate_ids,
        }
        self.stdout.write(
            f"{reason}: canonical={canonical.id} duplicates={len(duplicates)} "
            f"conversations={result['conversations_reassigned']} "
            f"leads={result['leads_reassigned']} messages={result['messages_reassigned']}"
        )

        if dry_run:
            return result

        with transaction.atomic():
            locked = list(DoubleTickCustomer.objects.select_for_update().filter(id__in=ids).order_by("created_at"))
            canonical = self._canonical_customer(locked)
            duplicate_ids = [customer.id for customer in locked if customer.id != canonical.id]

            DoubleTickConversation.objects.filter(customer_id__in=duplicate_ids).update(customer=canonical)
            DoubleTickLead.objects.filter(customer_id__in=duplicate_ids).update(customer=canonical)
            DoubleTickMessage.objects.filter(customer_id__in=duplicate_ids).update(customer=canonical)

            for duplicate in locked:
                if duplicate.id == canonical.id:
                    continue
                self._copy_missing_fields(canonical, duplicate)
            canonical.save()
            DoubleTickCustomer.objects.filter(id__in=duplicate_ids).delete()

        return result

    def _copy_missing_fields(self, canonical, duplicate):
        for field in ["dt_customer_id", "phone_number", "normalized_phone", "customer_name", "whatsapp_name"]:
            if not getattr(canonical, field) and getattr(duplicate, field):
                setattr(canonical, field, getattr(duplicate, field))
        if not canonical.channel_id and duplicate.channel_id:
            canonical.channel = duplicate.channel
        if not canonical.first_seen_at or (duplicate.first_seen_at and duplicate.first_seen_at < canonical.first_seen_at):
            canonical.first_seen_at = duplicate.first_seen_at
        if not canonical.last_seen_at or (duplicate.last_seen_at and duplicate.last_seen_at > canonical.last_seen_at):
            canonical.last_seen_at = duplicate.last_seen_at
        if not canonical.raw_profile and duplicate.raw_profile:
            canonical.raw_profile = duplicate.raw_profile
