from django.core.management.base import BaseCommand
from django.db import transaction, DatabaseError, OperationalError
import time

from apps.doubletick.models import (
    DoubleTickWebhookLog,
    DoubleTickCustomer,
    DoubleTickConversation,
    DoubleTickLead,
    DoubleTickMessage,
    DoubleTickLeadVisibility,
    DoubleTickLeadAssignment,
    DoubleTickDistributionAudit,
    DoubleTickActivity,
    DoubleTickLeadActivity,
)


class Command(BaseCommand):
    help = "Safely reset runtime DoubleTick fetched data (dry-run default)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Actually perform deletion. Without this the command is a dry-run.",
        )
        parser.add_argument(
            "--backup-warning-confirmed",
            action="store_true",
            help="A required extra confirmation flag to proceed with commit.",
        )
        parser.add_argument(
            "--keep-webhook-logs",
            action="store_true",
            help="When committing, keep DoubleTickWebhookLog rows.",
        )

    def _counts(self):
        return {
            "DoubleTickWebhookLog": DoubleTickWebhookLog.objects.count(),
            "DoubleTickCustomer": DoubleTickCustomer.objects.count(),
            "DoubleTickConversation": DoubleTickConversation.objects.count(),
            "DoubleTickLead": DoubleTickLead.objects.count(),
            "DoubleTickMessage": DoubleTickMessage.objects.count(),
            "DoubleTickLeadVisibility": DoubleTickLeadVisibility.objects.count(),
            "DoubleTickLeadAssignment": DoubleTickLeadAssignment.objects.count(),
            "DoubleTickDistributionAudit": DoubleTickDistributionAudit.objects.count(),
            "DoubleTickActivity": DoubleTickActivity.objects.count(),
            "DoubleTickLeadActivity": DoubleTickLeadActivity.objects.count(),
        }

    def _print_counts(self, header, counts):
        self.stdout.write(header)
        self.stdout.write("-" * 60)
        for k, v in counts.items():
            self.stdout.write(f"{k:<30} {v}")
        self.stdout.write("")

    def _batch_delete_queryset(self, name, queryset, batch_size=1000, max_retries=5):
        """Delete queryset in batches to avoid long-running locks. Returns total deleted."""
        total_deleted = 0
        while True:
            pks = list(queryset.values_list("pk", flat=True)[:batch_size])
            if not pks:
                break
            attempt = 0
            while True:
                try:
                    with transaction.atomic():
                        qs = queryset.model.objects.filter(pk__in=pks)
                        deleted_count, _ = qs.delete()
                        total_deleted += deleted_count
                    break
                except (OperationalError, DatabaseError) as exc:
                    attempt += 1
                    if attempt > max_retries:
                        raise
                    wait = 0.5 * attempt
                    self.stdout.write(self.style.WARNING(f"Deadlock or DB error deleting {name} batch; retry {attempt}/{max_retries} after {wait}s"))
                    time.sleep(wait)
        return total_deleted

    def handle(self, *args, **options):
        commit = bool(options.get("commit"))
        confirm = bool(options.get("backup_warning_confirmed"))
        keep_webhook = bool(options.get("keep_webhook_logs"))

        self.stdout.write(self.style.WARNING("This command will remove runtime DoubleTick data."))
        self.stdout.write("It will NOT delete channels, areas, aliases, branch mappings, users, devices or locations.")
        self.stdout.write("")

        before = self._counts()
        self._print_counts("Counts before deletion:", before)

        if not commit:
            self.stdout.write(self.style.SUCCESS("Dry-run: no data will be deleted. Run with --commit and --backup-warning-confirmed to apply."))
            self.stdout.write("Note: old webhook events will not replay automatically unless you import them separately.")
            return

        if not confirm:
            self.stdout.write(self.style.ERROR("Refusing to run commit without --backup-warning-confirmed. This protects accidental data loss."))
            return

        # Proceed with deletion inside a transaction to ensure atomicity.
        try:
            # Delete in safe child-first order using batched deletes to reduce deadlocks.
            deleted = {}

            deleted["DoubleTickLeadVisibility"] = self._batch_delete_queryset("DoubleTickLeadVisibility", DoubleTickLeadVisibility.objects.all())
            deleted["DoubleTickLeadAssignment"] = self._batch_delete_queryset("DoubleTickLeadAssignment", DoubleTickLeadAssignment.objects.all())
            deleted["DoubleTickLeadActivity"] = self._batch_delete_queryset("DoubleTickLeadActivity", DoubleTickLeadActivity.objects.all())
            deleted["DoubleTickDistributionAudit"] = self._batch_delete_queryset("DoubleTickDistributionAudit", DoubleTickDistributionAudit.objects.all())
            deleted["DoubleTickActivity"] = self._batch_delete_queryset("DoubleTickActivity", DoubleTickActivity.objects.all())
            deleted["DoubleTickMessage"] = self._batch_delete_queryset("DoubleTickMessage", DoubleTickMessage.objects.all())
            deleted["DoubleTickLead"] = self._batch_delete_queryset("DoubleTickLead", DoubleTickLead.objects.all())
            deleted["DoubleTickConversation"] = self._batch_delete_queryset("DoubleTickConversation", DoubleTickConversation.objects.all())
            deleted["DoubleTickCustomer"] = self._batch_delete_queryset("DoubleTickCustomer", DoubleTickCustomer.objects.all())

            if not keep_webhook:
                deleted["DoubleTickWebhookLog"] = self._batch_delete_queryset("DoubleTickWebhookLog", DoubleTickWebhookLog.objects.all())
            else:
                deleted["DoubleTickWebhookLog"] = 0

            # Print summary of deletions
            self._print_counts("Deleted counts:", deleted)

        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Deletion failed: {exc}"))
            raise

        after = self._counts()
        self._print_counts("Counts after deletion:", after)

        self.stdout.write(self.style.SUCCESS("Runtime DoubleTick data reset completed."))
        self.stdout.write("Preserved models: DoubleTickChannel, DoubleTickLeadArea, DoubleTickAreaAlias, DoubleTickLeadAreaBranch, DoubleTickTeamMemberMapping, locations, branches, users, devices.")
        self.stdout.write("Warning: webhook events will not be reprocessed automatically; use an import/backfill if needed.")
