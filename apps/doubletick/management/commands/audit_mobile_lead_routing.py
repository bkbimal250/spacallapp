from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from apps.accounts.models import User
from apps.devices.models import Device
from apps.locations.models import Area

from apps.doubletick.models import (
    DoubleTickDistributionAudit,
    DoubleTickLead,
    DoubleTickLeadArea,
    DoubleTickLeadAreaBranch,
    DoubleTickLeadVisibility,
)


class Command(BaseCommand):
    help = "Audit DoubleTick routing profiles, branch mappings, and Android lead visibility."

    def _line(self, label, value):
        self.stdout.write(f"{label:<58} {value}")

    def handle(self, *args, **options):
        matched_leads = DoubleTickLead.objects.filter(
            is_deleted=False,
            matched_area__isnull=False,
        )
        android_visible = matched_leads.filter(
            visibilities__is_visible=True,
            visibilities__device__isnull=False,
        ).distinct()
        no_visibility = matched_leads.exclude(
            visibilities__is_visible=True,
        ).distinct()

        active_mapping_filter = Q(
            matched_area__branch_mappings__is_active=True,
            matched_area__branch_mappings__receives_leads=True,
            matched_area__branch_mappings__branch__is_active=True,
            matched_area__branch_mappings__branch__is_deleted=False,
        )
        leads_missing_mappings = matched_leads.annotate(
            active_mapping_count=Count(
                "matched_area__branch_mappings",
                filter=active_mapping_filter,
                distinct=True,
            )
        ).filter(active_mapping_count=0)

        areas_without_profile = Area.objects.filter(
            is_deleted=False,
            is_active=True,
        ).exclude(
            doubletick_routing_profiles__is_deleted=False,
            doubletick_routing_profiles__is_active=True,
        )
        profiles_without_area = DoubleTickLeadArea.objects.filter(
            is_deleted=False,
            location_area__isnull=True,
        )

        users_without_visible_leads = User.objects.filter(
            is_active=True,
            role__in=["spa_manager", "area_manager"],
        ).exclude(
            doubletickleadvisibility__is_visible=True,
        )
        devices_without_visible_leads = Device.objects.filter(
            is_deleted=False,
            is_active=True,
            is_registered=True,
        ).exclude(
            doubletickleadvisibility__is_visible=True,
        )

        stuck_after_manual_correction = matched_leads.filter(
            conversation__area_confirmed=True,
            conversation__requires_manual_attention=False,
            status__in=[
                DoubleTickLead.Status.QUALIFIED,
                DoubleTickLead.Status.AREA_MATCHED,
                DoubleTickLead.Status.UNASSIGNED,
                DoubleTickLead.Status.FAILED,
            ],
        ).exclude(visibilities__is_visible=True).distinct()

        duplicate_visibility_groups = (
            DoubleTickLeadVisibility.objects.values(
                "lead_id",
                "branch_id",
                "user_id",
                "device_id",
            )
            .annotate(total=Count("id"))
            .filter(total__gt=1)
        )

        self.stdout.write(self.style.SUCCESS("Mobile Lead Routing Audit"))
        self.stdout.write("=" * 78)
        self._line("Total matched leads", matched_leads.count())
        self._line("Leads visible to Android devices", android_visible.count())
        self._line("Matched leads with no active visibility", no_visibility.count())
        self._line("Matched leads with missing branch mappings", leads_missing_mappings.count())
        self._line("Active locations.Area without routing profile", areas_without_profile.count())
        self._line("DoubleTickLeadArea without locations.Area link", profiles_without_area.count())
        self._line("Active users with no visible leads", users_without_visible_leads.count())
        self._line("Registered devices with no visible leads", devices_without_visible_leads.count())
        self._line("Leads stuck after manual correction", stuck_after_manual_correction.count())
        self._line("Duplicate visibility row groups", duplicate_visibility_groups.count())
        self._line(
            "Failed distribution audits",
            DoubleTickDistributionAudit.objects.filter(
                status=DoubleTickDistributionAudit.Status.FAILED
            ).count(),
        )
        self._line(
            "Active routing profiles without branch mapping",
            DoubleTickLeadArea.objects.filter(
                is_deleted=False,
                is_active=True,
            ).exclude(
                branch_mappings__is_active=True,
                branch_mappings__receives_leads=True,
                branch_mappings__branch__is_active=True,
                branch_mappings__branch__is_deleted=False,
            ).distinct().count(),
        )
        self._line(
            "Active area-branch mappings",
            DoubleTickLeadAreaBranch.objects.filter(
                lead_area__is_deleted=False,
                lead_area__is_active=True,
                is_active=True,
                receives_leads=True,
                branch__is_active=True,
                branch__is_deleted=False,
            ).count(),
        )
