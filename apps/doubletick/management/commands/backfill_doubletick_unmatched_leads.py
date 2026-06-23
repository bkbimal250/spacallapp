from django.core.management.base import BaseCommand

from apps.doubletick.models import DoubleTickConversation
from apps.doubletick.services import LeadQualificationService


class Command(BaseCommand):
    help = "Create missing DoubleTickLead rows for existing inbound conversations, including unmatched or awaiting-location conversations."

    def handle(self, *args, **options):
        counts = {"scanned": 0, "created": 0, "skipped": 0, "errors": 0}
        queryset = DoubleTickConversation.objects.select_related("customer", "channel", "matched_area", "current_lead").prefetch_related("messages")
        queryset = queryset.filter(current_lead__isnull=True, messages__direction="inbound").distinct()
        for conversation in queryset.iterator():
            counts["scanned"] += 1
            try:
                before_id = conversation.current_lead_id
                lead = LeadQualificationService.ensure_conversation_lead(conversation, distribute=False)
                counts["created" if lead and not before_id else "skipped"] += 1
            except Exception as exc:
                counts["errors"] += 1
                self.stderr.write(f"error conversation={conversation.id}: {exc}")
        self.stdout.write(
            "scanned={scanned} created={created} skipped={skipped} errors={errors}".format(**counts)
        )
