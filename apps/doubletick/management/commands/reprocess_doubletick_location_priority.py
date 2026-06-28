import json

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Prefetch

from apps.doubletick.models import DoubleTickConversation, DoubleTickMessage
from apps.doubletick.services import DoubleTickLocationPriorityService


class Command(BaseCommand):
    help = "Reprocess DoubleTick location routing from inbound customer messages using priority rules."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show changes without saving.")
        parser.add_argument("--commit", action="store_true", help="Persist corrected routing.")
        parser.add_argument("--batch-size", type=int, default=200)
        parser.add_argument("--max-findings", type=int, default=100, help="Maximum detailed change rows to print.")
        parser.add_argument("--limit", type=int, default=0, help="Limit conversations for a quick spot-check.")

    def handle(self, *args, **options):
        commit = bool(options["commit"])
        dry_run = options["dry_run"] or not commit
        batch_size = int(options["batch_size"] or 200)
        max_findings = int(options["max_findings"] or 0)
        limit = int(options["limit"] or 0)
        printed = 0

        def report(message):
            nonlocal printed
            if max_findings <= 0 or printed < max_findings:
                self.stdout.write(message)
                printed += 1

        counts = {
            "inspected": 0,
            "would_change": 0,
            "changed": 0,
            "unchanged": 0,
            "manual_review": 0,
            "errors": 0,
        }

        queryset = DoubleTickConversation.objects.select_related(
            "channel",
            "matched_area",
            "current_lead",
            "current_lead__matched_area",
            "current_lead__current_branch",
            "current_lead__assigned_branch",
        ).prefetch_related(
            Prefetch(
                "messages",
                queryset=DoubleTickMessage.objects.filter(
                    direction=DoubleTickMessage.Direction.INBOUND,
                    origin=DoubleTickMessage.Origin.CUSTOMER,
                ).order_by("message_timestamp", "received_at", "created_at"),
                to_attr="inbound_customer_message_list",
            )
        ).order_by("id")
        if limit:
            queryset = queryset[:limit]

        for conversation in queryset.iterator(chunk_size=batch_size):
            counts["inspected"] += 1
            try:
                best = DoubleTickLocationPriorityService.best_match_for_conversation(conversation, allow_fuzzy=False)
                before = DoubleTickLocationPriorityService.current_route_snapshot(conversation)
                manual_review = bool(best.get("needs_manual_review"))
                low_priority = int(best.get("match_priority") or 0) < 40
                preserve_existing_area = manual_review or (
                    best.get("classification") in ["city", "location_group"]
                    and bool(before["matched_area_id"])
                ) or (
                    int(best.get("match_priority") or 0) < 80
                    and bool(before["matched_area_id"])
                )
                expected = {
                    "raw_city": before["raw_city"] if low_priority else best.get("raw_city") or conversation.raw_city or "",
                    "raw_area": before["raw_area"] if preserve_existing_area or low_priority else best.get("raw_area") or "",
                    "matched_area_id": before["matched_area_id"] if preserve_existing_area or low_priority else str(best["matched_area"].id) if best.get("matched_area") else "",
                    "lead_current_branch_id": before["lead_current_branch_id"] if manual_review else str(best["current_branch"].id) if best.get("current_branch") else before["lead_current_branch_id"],
                }
                route_changes = {
                    key: {"from": before.get(key, ""), "to": value}
                    for key, value in expected.items()
                    if before.get(key, "") != value
                }
                if not route_changes and not manual_review:
                    counts["unchanged"] += 1
                    continue

                if manual_review:
                    counts["manual_review"] += 1
                else:
                    counts["would_change"] += 1
                safe_changes = json.dumps(route_changes, ensure_ascii=True, default=str)
                selected_branch = best["current_branch"].spa_name if best.get("current_branch") else ""
                selected_branch_city = best.get("selected_branch_city") or getattr(best.get("current_branch"), "city", "") or ""
                selected_branch_area = best.get("selected_branch_area") or getattr(best.get("current_branch"), "area", "") or ""
                selected_area = best["matched_area"].name if best.get("matched_area") else ""
                selected_city = best.get("raw_city") or ""
                selected_group = best.get("raw_group") or ""
                detected_area_token = best.get("detected_area_token") or best.get("raw_area") or ""
                source_text = best.get("input") or ""
                decision = "manual_review" if manual_review else "accepted"
                report(
                    f"{'manual_review' if manual_review else 'change' if commit else 'would_change'} conversation={conversation.id} "
                    f"lead={before.get('lead_id', '')} classification={best.get('classification')} "
                    f"message={source_text!a} detected_city={selected_city!a} "
                    f"detected_group={selected_group!a} detected_area={detected_area_token!a} "
                    f"priority={best.get('match_priority')} branch={selected_branch!a} "
                    f"branch_city={selected_branch_city!a} branch_area={selected_branch_area!a} "
                    f"area={selected_area!a} city={selected_city!a} group={selected_group!a} "
                    f"confidence={best.get('confidence', 0)} method={best.get('method') or best.get('area_method') or ''} "
                    f"reason={best.get('reason', '')!a} decision={decision} changes={safe_changes}"
                )
                if commit and not manual_review:
                    with transaction.atomic():
                        lead, _, after = DoubleTickLocationPriorityService.apply_best_match(
                            conversation,
                            best,
                            distribute=bool(best.get("matched_area")),
                        )
                    counts["changed"] += 1
                    report(
                        f"changed lead={lead.id} raw_city={after['raw_city']!r} "
                        f"raw_area={after['raw_area']!r} matched_area={after['matched_area_id']} "
                        f"branch={after['lead_current_branch_id']}"
                    )
            except Exception as exc:
                counts["errors"] += 1
                self.stderr.write(f"error conversation={conversation.id}: {exc}")
            if dry_run and max_findings > 0 and printed >= max_findings:
                break

        if max_findings > 0 and printed >= max_findings:
            self.stdout.write(f"finding output capped at {max_findings}; dry-run stopped after inspected rows shown in summary")
        self.stdout.write(("dry_run=True " if dry_run else "dry_run=False ") + " ".join(
            f"{key}={value}" for key, value in counts.items()
        ))
