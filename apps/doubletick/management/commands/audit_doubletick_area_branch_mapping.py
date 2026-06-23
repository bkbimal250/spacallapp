from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from apps.doubletick.models import DoubleTickLead, DoubleTickLeadArea, DoubleTickLeadAreaBranch


class Command(BaseCommand):
    help = "Audit DoubleTick area-to-branch mapping coverage and matched area distribution health."

    def _line(self, label, value):
        self.stdout.write(f"{label:<52} {value}")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("DoubleTick Area-Branch Mapping Audit"))
        self.stdout.write("=" * 72)

        active_areas = DoubleTickLeadAreaBranch.objects.filter(
            lead_area__is_active=True,
            lead_area__is_deleted=False,
            is_active=True,
            receives_leads=True,
            branch__is_active=True,
            branch__is_deleted=False,
        ).values_list("lead_area_id", flat=True).distinct()

        total_areas = DoubleTickLeadArea.objects.filter(is_active=True, is_deleted=False).count()
        unmapped_areas = DoubleTickLeadArea.objects.filter(is_active=True, is_deleted=False).exclude(id__in=active_areas)
        self._line("Active lead areas", total_areas)
        self._line("Lead areas without active mappings", unmapped_areas.count())
        self.stdout.write("")

        top_mapping_areas = (
            DoubleTickLeadAreaBranch.objects.filter(
                lead_area__is_active=True,
                lead_area__is_deleted=False,
                is_active=True,
                receives_leads=True,
                branch__is_active=True,
                branch__is_deleted=False,
            )
            .values("lead_area__id", "lead_area__city", "lead_area__name")
            .annotate(mapping_count=Count("id"))
            .order_by("-mapping_count", "lead_area__city", "lead_area__name")[:10]
        )
        if top_mapping_areas:
            self.stdout.write("Top mapped areas:")
            for row in top_mapping_areas:
                self.stdout.write(
                    f"  {row['lead_area__city'] or '[no city]'} / {row['lead_area__name']} : {row['mapping_count']}"
                )
            self.stdout.write("")

        top_lead_areas = (
            DoubleTickLead.objects.filter(matched_area__isnull=False)
            .values("matched_area__id", "matched_area__city", "matched_area__name")
            .annotate(lead_count=Count("id"))
            .order_by("-lead_count", "matched_area__city", "matched_area__name")[:10]
        )
        if top_lead_areas:
            self.stdout.write("Top matched areas by lead count:")
            for row in top_lead_areas:
                self.stdout.write(
                    f"  {row['matched_area__city'] or '[no city]'} / {row['matched_area__name']} : {row['lead_count']}"
                )
            self.stdout.write("")

        areas_without_visibility = (
            DoubleTickLead.objects.filter(matched_area__isnull=False)
            .annotate(visibility_count=Count("visibilities", distinct=True))
            .filter(visibility_count=0)
            .values("matched_area__id", "matched_area__city", "matched_area__name")
            .annotate(lead_count=Count("id"))
            .order_by("-lead_count", "matched_area__city", "matched_area__name")[:10]
        )
        self._line("Matched areas with leads missing visibility", areas_without_visibility.count())
        if areas_without_visibility:
            self.stdout.write("Top areas with leads missing visibility:")
            for row in areas_without_visibility:
                self.stdout.write(
                    f"  {row['matched_area__city'] or '[no city]'} / {row['matched_area__name']} : {row['lead_count']}"
                )
            self.stdout.write("")

        areas_with_no_active_mapping = (
            DoubleTickLead.objects.filter(matched_area__isnull=False)
            .values("matched_area__id", "matched_area__city", "matched_area__name")
            .annotate(
                lead_count=Count("id"),
                active_mapping_count=Count(
                    "matched_area__branch_mappings",
                    filter=Q(
                        matched_area__branch_mappings__is_active=True,
                        matched_area__branch_mappings__receives_leads=True,
                        matched_area__branch_mappings__branch__is_active=True,
                        matched_area__branch_mappings__branch__is_deleted=False,
                        matched_area__branch_mappings__lead_area__is_active=True,
                        matched_area__branch_mappings__lead_area__is_deleted=False,
                    ),
                    distinct=True,
                ),
            )
            .filter(active_mapping_count=0)
            .order_by("-lead_count", "matched_area__city", "matched_area__name")[:10]
        )
        self._line("Matched areas with no active mappings", areas_with_no_active_mapping.count())
        if areas_with_no_active_mapping:
            self.stdout.write("Top matched areas with no active mappings:")
            for row in areas_with_no_active_mapping:
                self.stdout.write(
                    f"  {row['matched_area__city'] or '[no city]'} / {row['matched_area__name']} : {row['lead_count']} leads"
                )
            self.stdout.write("")
