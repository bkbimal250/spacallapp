"""
Dashboard views for the CallLog SPA Management System.

Provides the main KPI summary data for the web dashboard home page.

Access Control:
    super_admin / admin → See stats for all branches (or filter by ?branch=).
    branch_manager      → See stats only for their assigned branch.
"""

import logging
from datetime import timedelta

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncDate

from apps.calllogs.models import CallLog
from apps.calllogs.filters import CallLogFilter
from apps.devices.models import Device
from apps.branches.models import Branch
from apps.common.utils import get_branch_filter_ids
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from rest_framework import serializers

logger = logging.getLogger(__name__)


class DashboardOverviewView(APIView):
    """
    Returns call type counts for the dashboard overview.

    When ?device=<device_uid> is supplied, counts are scoped to that registered
    device before aggregation. Without device, branch-level behavior is unchanged.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get dashboard call overview",
        description="Returns call counts grouped by type for the selected dashboard filters.",
        parameters=[
            OpenApiParameter("quick_date", str, description="Preset date filter: today, yesterday, all"),
            OpenApiParameter("start_date", str, description="Format: YYYY-MM-DD"),
            OpenApiParameter("end_date", str, description="Format: YYYY-MM-DD"),
            OpenApiParameter("branch", str, description="Filter by Branch UUID"),
            OpenApiParameter("device", str, description="Filter by registered device UID"),
            OpenApiParameter("call_type", str, enum=["incoming", "outgoing", "missed", "rejected"]),
            OpenApiParameter("search", str, description="Search by phone number or contact name"),
            OpenApiParameter("ordering", str, description="Ordering parameter retained for compatibility"),
        ],
        responses={
            200: inline_serializer(
                name="DashboardOverviewResponse",
                fields={
                    "total": serializers.IntegerField(),
                    "incoming": serializers.IntegerField(),
                    "outgoing": serializers.IntegerField(),
                    "missed": serializers.IntegerField(),
                    "rejected": serializers.IntegerField(),
                },
            )
        },
    )
    def get(self, request):
        user = request.user
        branch_ids = get_branch_filter_ids(user)
        queryset = CallLog.objects.select_related("branch", "contact", "device")

        if branch_ids and branch_ids != ["NONE"]:
            queryset = queryset.filter(branch_id__in=branch_ids)
        elif branch_ids == ["NONE"]:
            queryset = queryset.none()

        filtered_qs = CallLogFilter(request.query_params, queryset=queryset).qs
        final_record_count = filtered_qs.count()

        stats = filtered_qs.aggregate(
            total=Count("id"),
            incoming=Count("id", filter=Q(call_type="incoming")),
            outgoing=Count("id", filter=Q(call_type="outgoing")),
            missed=Count("id", filter=Q(call_type="missed")),
            rejected=Count("id", filter=Q(call_type="rejected")),
        )

        device_uid = request.query_params.get("device")
        quick_date = request.query_params.get("quick_date")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        branch_id = request.query_params.get("branch")

        logger.info(
            "Dashboard Analytics",
            extra={
                "branch_id": branch_id or branch_ids or None,
                "device_uid": device_uid.strip() if device_uid else None,
                "date_filter": quick_date or {"start_date": start_date, "end_date": end_date},
                "final_record_count": final_record_count,
            },
        )

        return Response({
            "total": stats["total"] or 0,
            "incoming": stats["incoming"] or 0,
            "outgoing": stats["outgoing"] or 0,
            "missed": stats["missed"] or 0,
            "rejected": stats["rejected"] or 0,
        })


class DashboardStatsView(APIView):
    """
    Returns summary KPI data for the main dashboard.

    Response includes:
        - total_calls        : Total call count
        - active_devices     : Number of devices marked online in DeviceHealth
        - missed_calls       : Count of missed calls
        - avg_duration       : Average call duration (formatted as "Xm Ys")
        - call_volume_trends : Last 7 days daily call counts (for chart)
        - branch_performance : Top 10 branches by call volume (for table)

    Access:
        super_admin / admin → All branches (or filtered by ?branch=).
        branch_manager      → Only their assigned branch.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get dashboard KPI metrics",
        description="Returns global or branch-specific statistics for the web dashboard.",
        parameters=[
            OpenApiParameter("branch", str, description="Filter results by Branch UUID"),
            OpenApiParameter("branch_group", str, description="Filter results by Branch Group UUID"),
            OpenApiParameter("lead_source", str, enum=["direct", "manual"], description="Filter by lead creation source"),
        ],
        responses={
            200: inline_serializer(
                name="DashboardStatsResponse",
                fields={
                    "total_calls": serializers.IntegerField(),
                    "active_devices": serializers.IntegerField(),
                    "total_devices": serializers.IntegerField(),
                    "missed_calls": serializers.IntegerField(),
                    "total_leads": serializers.IntegerField(),
                    "total_branches": serializers.IntegerField(),
                    "total_contacts": serializers.IntegerField(),
                    "total_users": serializers.IntegerField(),
                    "total_exports": serializers.IntegerField(),
                    "today_total_calls": serializers.IntegerField(),
                    "avg_duration": serializers.CharField(help_text="Format: 5m 30s"),
                    "call_volume_trends": serializers.ListField(
                        child=inline_serializer(
                            name="TrendPoint",
                            fields={
                                "name": serializers.CharField(help_text="Day of week: Mon, Tue"),
                                "calls": serializers.IntegerField(),
                            }
                        )
                    ),
                    "branch_performance": serializers.ListField(
                        child=inline_serializer(
                            name="BranchPerformance",
                            fields={
                                "id": serializers.UUIDField(),
                                "name": serializers.CharField(),
                                "calls": serializers.IntegerField(),
                                "incoming": serializers.IntegerField(),
                                "outgoing": serializers.IntegerField(),
                                "missed": serializers.IntegerField(),
                                "conversion": serializers.IntegerField(),
                                "status": serializers.CharField(),
                            }
                        )
                    ),
                }
            )
        }
    )
    def get(self, request):
        user = request.user
        from apps.monitoring.models import DeviceHealth
        from apps.leadmanagement.models import LeadManagement
        from apps.contacts.models import Contact
        from apps.exports.models import ExportJob
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Get branch IDs for the current user's role
        branch_ids = get_branch_filter_ids(user)
        # Get filter parameters
        branch_id_param = request.query_params.get("branch")
        branch_group_id_param = request.query_params.get("branch_group")
        lead_source = request.query_params.get("lead_source")
        quick_date = request.query_params.get("quick_date")
        start_date_param = request.query_params.get("start_date")
        end_date_param = request.query_params.get("end_date")

        # Build date filter Q
        date_filter_q = Q()
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if quick_date == 'today':
            date_filter_q = Q(call_time__gte=today_start)
        elif quick_date == 'yesterday':
            yesterday_start = today_start - timedelta(days=1)
            date_filter_q = Q(call_time__gte=yesterday_start, call_time__lt=today_start)
        elif start_date_param or end_date_param:
            if start_date_param:
                date_filter_q &= Q(call_time__date__gte=start_date_param)
            if end_date_param:
                date_filter_q &= Q(call_time__date__lte=end_date_param)

        # Build base querysets
        calls_qs = CallLog.objects.all()
        health_qs = DeviceHealth.objects.all()
        branch_qs = Branch.objects.filter(is_active=True)
        device_qs = Device.objects.filter(is_deleted=False)
        lead_qs = LeadManagement.objects.all()
        contact_qs = Contact.objects.all()
        user_qs = User.objects.filter(is_active=True)
        export_qs = ExportJob.objects.all()

        # Apply date filtering to calls if requested
        # Note: We apply it to calls_qs so the main KPI total_calls reflects the selected range
        if date_filter_q:
            calls_qs = calls_qs.filter(date_filter_q)

        # Apply lead source filtering if requested
        if lead_source == "direct":
            # Only leads that came from a call sync
            lead_qs = lead_qs.filter(calllog__isnull=False)
            calls_qs = calls_qs.filter(lead__isnull=False)
        elif lead_source == "manual":
            # Only leads created manually
            lead_qs = lead_qs.filter(calllog__isnull=True)
            calls_qs = calls_qs.none()

        # Apply role-based branch filtering
        if branch_ids and branch_ids != ["NONE"]:
            # Restricted user: filter to their branch(es)
            calls_qs = calls_qs.filter(branch_id__in=branch_ids)
            health_qs = health_qs.filter(device__branch_id__in=branch_ids)
            branch_qs = branch_qs.filter(id__in=branch_ids)
            device_qs = device_qs.filter(branch_id__in=branch_ids)
            lead_qs = lead_qs.filter(branch_id__in=branch_ids)
            contact_qs = contact_qs.filter(call_logs__branch_id__in=branch_ids).distinct()
            user_qs = user_qs.filter(Q(branch_id__in=branch_ids) | Q(role__in=["admin", "super_admin"]))
            export_qs = export_qs.filter(user__branch_id__in=branch_ids)
        elif branch_id_param and branch_id_param.strip() and branch_id_param not in ("undefined", "null"):
            # Admin manually filtering by a specific branch
            calls_qs = calls_qs.filter(branch_id=branch_id_param)
            health_qs = health_qs.filter(device__branch_id=branch_id_param)
            branch_qs = branch_qs.filter(id=branch_id_param)
            device_qs = device_qs.filter(branch_id=branch_id_param)
            lead_qs = lead_qs.filter(branch_id=branch_id_param)
            contact_qs = contact_qs.filter(call_logs__branch_id=branch_id_param).distinct()
            user_qs = user_qs.filter(branch_id=branch_id_param)
            export_qs = export_qs.filter(user__branch_id=branch_id_param)
        elif branch_group_id_param and branch_group_id_param.strip() and branch_group_id_param not in ("undefined", "null"):
            # Filtering by Branch Group
            calls_qs = calls_qs.filter(branch__branch_group_id=branch_group_id_param)
            health_qs = health_qs.filter(device__branch__branch_group_id=branch_group_id_param)
            branch_qs = branch_qs.filter(branch_group_id=branch_group_id_param)
            device_qs = device_qs.filter(branch__branch_group_id=branch_group_id_param)
            lead_qs = lead_qs.filter(branch__branch_group_id=branch_group_id_param)
            contact_qs = contact_qs.filter(call_logs__branch__branch_group_id=branch_group_id_param).distinct()
            user_qs = user_qs.filter(branch__branch_group_id=branch_group_id_param)
            export_qs = export_qs.filter(user__branch__branch_group_id=branch_group_id_param)
        elif branch_ids == ["NONE"]:
            # Branch manager with no branch assigned — show nothing
            calls_qs = calls_qs.none()
            health_qs = health_qs.none()
            branch_qs = branch_qs.none()
            device_qs = device_qs.none()
            lead_qs = lead_qs.none()
            user_qs = user_qs.none()
            export_qs = export_qs.none()
            contact_qs = contact_qs.none()

        # ── KPI Stats ──────────────────────────────────────────────────────────
        total_calls = calls_qs.count()
        active_devices = health_qs.filter(is_online=True).count()
        missed_calls = calls_qs.filter(call_type="missed").count()
        
        total_devices = device_qs.count()
        total_leads = lead_qs.count()
        total_branches = branch_qs.count()
        total_contacts = contact_qs.count()
        total_users = user_qs.count()
        total_exports = export_qs.count()

        # Today's total calls (should be independent of global quick_date filter)
        today_start_absolute = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # We need a branch-filtered queryset for today's calls
        today_calls_qs = CallLog.objects.all()
        if branch_ids and branch_ids != ["NONE"]:
            today_calls_qs = today_calls_qs.filter(branch_id__in=branch_ids)
        elif branch_id_param and branch_id_param.strip() and branch_id_param not in ("undefined", "null"):
            today_calls_qs = today_calls_qs.filter(branch_id=branch_id_param)
        elif branch_group_id_param and branch_group_id_param.strip() and branch_group_id_param not in ("undefined", "null"):
            today_calls_qs = today_calls_qs.filter(branch__branch_group_id=branch_group_id_param)
        
        today_total_calls = today_calls_qs.filter(call_time__gte=today_start_absolute).count()
        today_incoming_calls = today_calls_qs.filter(call_time__gte=today_start_absolute, call_type="incoming").count()
        today_outgoing_calls = today_calls_qs.filter(call_time__gte=today_start_absolute, call_type="outgoing").count()
        today_missed_calls = today_calls_qs.filter(call_time__gte=today_start_absolute, call_type="missed").count()

        # Average call duration (formatted as "Xm Ys")
        avg_dur = calls_qs.aggregate(Avg("duration"))["duration__avg"]
        if avg_dur:
            minutes = int(avg_dur // 60)
            seconds = int(avg_dur % 60)
            avg_duration_str = f"{minutes}m {seconds}s"
        else:
            avg_duration_str = "0m 0s"

        # ── 7-Day Call Volume Trend Chart ──────────────────────────────────────
        last_7_days = timezone.now() - timedelta(days=7)
        daily_trends = (
            calls_qs.filter(call_time__gte=last_7_days)
            .annotate(date=TruncDate("call_time"))
            .values("date")
            .annotate(calls=Count("id"))
            .order_by("date")
        )
        chart_data = [
            {"name": d["date"].strftime("%a"), "calls": d["calls"]}
            for d in daily_trends
        ]

        # ── Top 10 Branch Performance Table ───────────────────────────────────
        # Define filter Q for the annotations based on lead_source and date
        performance_filter_q = Q()
        
        # 1. Add lead source filter
        if lead_source == "direct":
            performance_filter_q &= Q(call_logs__lead__isnull=False)
        elif lead_source == "manual":
            # Manual source = 0 calls
            performance_filter_q &= Q(call_logs__id__isnull=True)

        # 2. Add date filter (Converting date_filter_q to related path)
        if quick_date == 'today':
            performance_filter_q &= Q(call_logs__call_time__gte=today_start)
        elif quick_date == 'yesterday':
            yesterday_start = today_start - timedelta(days=1)
            performance_filter_q &= Q(call_logs__call_time__gte=yesterday_start, call_logs__call_time__lt=today_start)
        elif start_date_param or end_date_param:
            if start_date_param:
                performance_filter_q &= Q(call_logs__call_time__date__gte=start_date_param)
            if end_date_param:
                performance_filter_q &= Q(call_logs__call_time__date__lte=end_date_param)

        performance_branches = branch_qs.annotate(
            total_calls_count=Count("call_logs", filter=performance_filter_q),
            incoming_count=Count("call_logs", filter=performance_filter_q & Q(call_logs__call_type="incoming")),
            outgoing_count=Count("call_logs", filter=performance_filter_q & Q(call_logs__call_type="outgoing")),
            missed_count=Count("call_logs", filter=performance_filter_q & Q(call_logs__call_type="missed")),
            completed_calls_count=Count(
                "call_logs",
                filter=performance_filter_q & (Q(call_logs__call_type="incoming") | Q(call_logs__call_type="outgoing")),
            ),
        ).order_by("-total_calls_count")[:10]

        branch_data = []
        for b in performance_branches:
            conv_rate = round((b.completed_calls_count / b.total_calls_count * 100) if b.total_calls_count > 0 else 0)
            branch_data.append({
                "id": str(b.id),
                "name": b.spa_name,
                "calls": b.total_calls_count,
                "incoming": b.incoming_count,
                "outgoing": b.outgoing_count,
                "missed": b.missed_count,
                "conversion": conv_rate,
                "status": "Active" if b.is_active else "Inactive",
            })

        return Response({
            "total_calls": total_calls,
            "active_devices": active_devices,
            "total_devices": total_devices,
            "missed_calls": missed_calls,
            "total_leads": total_leads,
            "total_branches": total_branches,
            "total_contacts": total_contacts,
            "total_users": total_users,
            "total_exports": total_exports,
            "today_total_calls": today_total_calls,
            "today_incoming_calls": today_incoming_calls,
            "today_outgoing_calls": today_outgoing_calls,
            "today_missed_calls": today_missed_calls,
            "avg_duration": avg_duration_str,
            "call_volume_trends": chart_data,
            "branch_performance": branch_data,
        })
