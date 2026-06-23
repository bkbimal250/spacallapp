import csv
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.doubletick.models import DoubleTickLead


class Command(BaseCommand):
    help = "Export DoubleTick leads flagged as duplicates to CSV."

    def add_arguments(self, parser):
        parser.add_argument("--output", type=str, default="tmp/doubletick_duplicates.csv", help="Output CSV path")
        parser.add_argument("--limit", type=int, default=0, help="Limit number of rows (0 = all)")

    def handle(self, *args, **options):
        output = options.get("output")
        limit = options.get("limit") or 0

        qs = DoubleTickLead.objects.filter(is_duplicate=True).order_by("created_at")
        if limit:
            qs = qs[:limit]

        rows = []
        for lead in qs:
            rows.append({
                "id": str(lead.id),
                "customer_name": lead.customer_name,
                "phone": lead.phone_number,
                "normalized_phone": lead.normalized_phone,
                "duplicate_of": str(lead.duplicate_of_id) if lead.duplicate_of_id else "",
                "created_at": lead.created_at.isoformat() if lead.created_at else "",
                "matched_area": str(lead.matched_area_id) if lead.matched_area_id else "",
                "status": lead.status,
            })

        # Ensure output dir exists
        import os
        os.makedirs(os.path.dirname(output), exist_ok=True)

        with open(output, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["id", "customer_name", "phone", "normalized_phone", "duplicate_of", "created_at", "matched_area", "status"])
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

        self.stdout.write(f"Wrote {len(rows)} duplicate leads to {output}")
