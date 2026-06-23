from django.core.management.base import BaseCommand

from apps.doubletick.models import DoubleTickLead
from apps.doubletick.services import LeadDistributionService


class Command(BaseCommand):
    help = "Create missing DoubleTickLeadVisibility rows for matched DoubleTick leads without duplicating visibility."

    def handle(self, *args, **options):
        counts = {"scanned": 0, "created": 0, "skipped": 0, "errors": 0}
        queryset = DoubleTickLead.objects.select_related("matched_area", "conversation").filter(matched_area__isnull=False)
        for lead in queryset.iterator():
            counts["scanned"] += 1
            before = lead.visibilities.count()
            try:
                LeadDistributionService.distribute(lead)
                after = lead.visibilities.count()
                if after > before:
                    counts["created"] += after - before
                else:
                    counts["skipped"] += 1
            except Exception as exc:
                counts["errors"] += 1
                self.stderr.write(f"error lead={lead.id}: {exc}")
        self.stdout.write(
            "scanned={scanned} created={created} skipped={skipped} errors={errors}".format(**counts)
        )
