"""
Dashboard views for the CallLog SPA Management System.

Provides the main KPI summary data for the web dashboard home page.

Access Control:
    super_admin / admin → See stats for all branches (or filter by ?branch=).
    branch_manager      → See stats only for their assigned branch.
"""

from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncDate

from apps.calllogs.models import CallLog
from apps.devices.models import Device
from apps.branches.models import Branch
from apps.common.utils import apply_branch_filter, get_branch_filter_ids


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
        branch_id_param = request.query_params.get("branch")
        lead_source = request.query_params.get("lead_source")  # New filter: 'direct' or 'manual'

        # Build base querysets
        calls_qs = CallLog.objects.all()
        health_qs = DeviceHealth.objects.all()
        branch_qs = Branch.objects.filter(is_active=True)
        device_qs = Device.objects.filter(is_deleted=False)
        lead_qs = LeadManagement.objects.all()
        contact_qs = Contact.objects.all()
        user_qs = User.objects.filter(is_active=True)
        export_qs = ExportJob.objects.all()

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

        # Today's total calls
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_total_calls = calls_qs.filter(call_time__gte=today_start).count()

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
        # Define filter Q for the annotations based on lead_source
        call_filter_q = Q()
        if lead_source == "direct":
            call_filter_q &= Q(call_logs__lead__isnull=False)
        elif lead_source == "manual":
            # If manual source is selected, call logs will be 0 as they only come from sync
            call_filter_q &= Q(call_logs__id__isnull=True)

        performance_branches = branch_qs.annotate(
            total_calls_count=Count("call_logs", filter=call_filter_q),
            incoming_count=Count("call_logs", filter=call_filter_q & Q(call_logs__call_type="incoming")),
            outgoing_count=Count("call_logs", filter=call_filter_q & Q(call_logs__call_type="outgoing")),
            missed_count=Count("call_logs", filter=call_filter_q & Q(call_logs__call_type="missed")),
            completed_calls_count=Count(
                "call_logs",
                filter=call_filter_q & (Q(call_logs__call_type="incoming") | Q(call_logs__call_type="outgoing")),
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
            "avg_duration": avg_duration_str,
            "call_volume_trends": chart_data,
            "branch_performance": branch_data,
        })
