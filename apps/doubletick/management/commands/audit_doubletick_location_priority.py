from django.core.management.base import BaseCommand

from apps.doubletick.models import DoubleTickConversation, DoubleTickLead
from apps.doubletick.services import (
    CRMLocationMatchEngine,
    DoubleTickLocationPriorityService,
    location_match_priority,
)
from apps.locations.models import City


class Command(BaseCommand):
    help = "Read-only audit for DoubleTick location priority and branch routing issues."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Read-only; included for operator clarity.")
        parser.add_argument("--batch-size", type=int, default=200)
        parser.add_argument("--max-findings", type=int, default=100, help="Maximum detailed rows to print.")
        parser.add_argument("--limit", type=int, default=0, help="Limit rows for a quick spot-check.")

    def handle(self, *args, **options):
        batch_size = int(options["batch_size"] or 200)
        max_findings = int(options["max_findings"] or 0)
        limit = int(options["limit"] or 0)
        printed = 0

        def report(message):
            nonlocal printed
            if max_findings <= 0 or printed < max_findings:
                self.stdout.write(message)
                printed += 1

        city_names = set(City.objects.filter(is_deleted=False, is_active=True).values_list("normalized_name", flat=True))
        counts = {
            "leads_raw_area_equals_city": 0,
            "city_only_saved_as_area": 0,
            "branch_text_current_branch_differs": 0,
            "group_text_matched_area_wrong": 0,
            "service_action_overwrote_location": 0,
        }

        self.stdout.write("dry_run=True")

        lead_queryset = DoubleTickLead.objects.select_related(
            "conversation", "current_branch", "assigned_branch", "matched_area"
        ).order_by("id")
        if limit:
            lead_queryset = lead_queryset[:limit]
        for lead in lead_queryset.iterator(chunk_size=batch_size):
            normalized_area = CRMLocationMatchEngine.normalize_text(lead.raw_area or lead.area)
            if normalized_area and normalized_area in city_names:
                counts["leads_raw_area_equals_city"] += 1
                report(f"raw_area_equals_city lead={lead.id} raw_area={lead.raw_area or lead.area!r}")

        conversations = DoubleTickConversation.objects.select_related(
            "channel", "matched_area", "current_lead", "current_lead__current_branch"
        ).prefetch_related("messages").order_by("id")
        if limit:
            conversations = conversations[:limit]
        for conversation in conversations.iterator(chunk_size=batch_size):
            best = DoubleTickLocationPriorityService.best_match_for_conversation(conversation)
            best_priority = best.get("match_priority", location_match_priority(best.get("classification")))
            lead = conversation.current_lead

            normalized_raw_area = CRMLocationMatchEngine.normalize_text(conversation.raw_area)
            if normalized_raw_area and normalized_raw_area in city_names:
                counts["city_only_saved_as_area"] += 1
                report(f"city_only_saved_as_area conversation={conversation.id} raw_area={conversation.raw_area!r}")

            if best.get("classification") == "branch" and best.get("current_branch") and lead:
                expected_branch = best["current_branch"]
                if lead.current_branch_id and lead.current_branch_id != expected_branch.id:
                    counts["branch_text_current_branch_differs"] += 1
                    report(
                        f"branch_text_current_branch_differs conversation={conversation.id} "
                        f"lead={lead.id} expected={expected_branch.spa_name!r} current={lead.current_branch.spa_name!r}"
                    )

            has_group_message = any(item["classification"] == "location_group" for item in best.get("matched_messages", []))
            if has_group_message and conversation.raw_area and not conversation.area_confirmed:
                counts["group_text_matched_area_wrong"] += 1
                report(
                    f"group_text_matched_area_wrong conversation={conversation.id} raw_group_present=True raw_area={conversation.raw_area!r}"
                )

            has_service_message = any(item["classification"] == "service_action" for item in best.get("matched_messages", []))
            if has_service_message and best_priority >= location_match_priority("area"):
                metadata = conversation.raw_payload if isinstance(conversation.raw_payload, dict) else {}
                saved_classification = (metadata.get("location_match") or {}).get("classification")
                if saved_classification == "service_action" or not conversation.matched_area_id:
                    counts["service_action_overwrote_location"] += 1
                    report(f"service_action_overwrote_location conversation={conversation.id}")

        if max_findings > 0 and printed >= max_findings:
            self.stdout.write(f"finding output capped at {max_findings}; summary counts include all inspected rows")
        self.stdout.write(
            "summary "
            + " ".join(f"{key}={value}" for key, value in counts.items())
        )
