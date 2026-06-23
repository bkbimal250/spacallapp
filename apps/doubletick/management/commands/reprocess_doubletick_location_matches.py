from django.core.management.base import BaseCommand
from django.db import transaction

from apps.doubletick.models import DoubleTickConversation
from apps.doubletick.services import (
    AreaMatchingService,
    AutoLocationRequestService,
    CRMLocationMatchEngine,
    LeadQualificationService,
)


class Command(BaseCommand):
    help = """Reprocess DoubleTick conversations for CRM-backed location matching.

    This command attempts to match each conversation's raw city/area to the
    normalized CRM locations app data, update the conversation state, and
    optionally send a location request to unmatched conversations.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without persisting updates.",
        )
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Persist updates to matched area and conversation state.",
        )
        parser.add_argument(
            "--send-location-request",
            action="store_true",
            help="Send a location request to unmatched conversations after reprocessing.",
        )
        parser.add_argument(
            "--only-unmatched",
            action="store_true",
            help="Process only conversations without an existing matched area.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=200,
            help="Process conversations in batches.",
        )

    def handle(self, *args, **options):
        commit = bool(options["commit"])
        dry_run = options["dry_run"] or not commit
        send_location_request = bool(options["send_location_request"])
        only_unmatched = bool(options["only_unmatched"])
        batch_size = int(options["batch_size"] or 200)

        if send_location_request and not commit:
            self.stdout.write(self.style.WARNING(
                "--send-location-request requires --commit to actually send messages."
            ))

        queryset = DoubleTickConversation.objects.select_related("channel", "matched_area")
        if only_unmatched:
            queryset = queryset.filter(matched_area__isnull=True)

        counts = {
            "inspected": 0,
            "skipped": 0,
            "matched": 0,
            "unmatched": 0,
            "updated": 0,
            "errors": 0,
        }

        for conversation in queryset.iterator(chunk_size=batch_size):
            counts["inspected"] += 1
            if conversation.area_confirmed and conversation.matched_area_id:
                counts["skipped"] += 1
                continue

            try:
                latest_customer = conversation.messages.filter(
                    direction="inbound",
                ).order_by("-received_at", "-created_at").first()
                source_text = conversation.raw_area or (latest_customer.text if latest_customer else "")
                if not source_text:
                    counts["skipped"] += 1
                    continue

                match_result = CRMLocationMatchEngine.classify_message(
                    source_text,
                    raw_city=conversation.raw_city or "",
                    channel=conversation.channel,
                )
                matched = bool(match_result.get("matched_area"))
                if matched:
                    counts["matched"] += 1
                    if commit:
                        with transaction.atomic():
                            AreaMatchingService.apply_match_result(conversation, match_result)
                            LeadQualificationService.ensure_conversation_lead(
                                conversation,
                                matched_area=conversation.matched_area,
                                distribute=True,
                            )
                        counts["updated"] += 1
                else:
                    counts["unmatched"] += 1
                    if commit and send_location_request:
                        AreaMatchingService.apply_match_result(conversation, match_result)
                        LeadQualificationService.ensure_conversation_lead(conversation, distribute=False)
                        AutoLocationRequestService.request_if_needed(conversation, match_result)
                        counts["updated"] += 1
            except Exception as exc:
                counts["errors"] += 1
                self.stderr.write(
                    f"error conversation={conversation.id}: {exc}"
                )

        summary = [
            f"inspected={counts['inspected']}",
            f"matched={counts['matched']}",
            f"unmatched={counts['unmatched']}",
            f"updated={counts['updated']}",
            f"errors={counts['errors']}",
        ]
        if dry_run:
            summary.insert(0, "dry_run=True")
        else:
            summary.insert(0, "dry_run=False")

        self.stdout.write(" ".join(summary))
