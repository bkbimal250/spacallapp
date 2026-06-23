from django.core.management.base import BaseCommand

from apps.doubletick.models import DoubleTickWebhookLog
from apps.doubletick.services import create_or_update_lead_from_webhook


class Command(BaseCommand):
    help = "Safely reprocess stored DoubleTick webhook logs."

    def add_arguments(self, parser):
        parser.add_argument("--only-unlinked", action="store_true", help="Only process logs without a linked conversation, lead, or message.")

    def handle(self, *args, **options):
        counts = {"scanned": 0, "created": 0, "skipped": 0, "errors": 0}
        queryset = DoubleTickWebhookLog.objects.order_by("created_at")
        if options["only_unlinked"]:
            queryset = queryset.filter(conversation__isnull=True, lead__isnull=True, message__isnull=True)

        for log in queryset.iterator():
            counts["scanned"] += 1
            if not log.payload:
                counts["skipped"] += 1
                continue
            try:
                lead, new_log = create_or_update_lead_from_webhook(log.payload)
                log.processed = True
                log.error_message = ""
                log.lead = lead or log.lead
                log.conversation = new_log.conversation or log.conversation
                log.message = new_log.message or log.message
                log.save(update_fields=["processed", "error_message", "lead", "conversation", "message", "updated_at"])
                counts["created"] += 1
            except Exception as exc:
                counts["errors"] += 1
                log.error_message = str(exc)
                log.save(update_fields=["error_message", "updated_at"])
                self.stderr.write(f"error log={log.id}: {exc}")
        self.stdout.write(
            "scanned={scanned} created={created} skipped={skipped} errors={errors}".format(**counts)
        )
