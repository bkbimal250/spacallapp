"""
Dashboard views for the CallLog SPA Management System.

The legacy dashboard endpoints stay backward compatible. New modular endpoints
reuse the same service layer so React can migrate one panel at a time.
"""

import logging

from django.db.models import Count, Q
from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserDeviceSession
from apps.calllogs.filters import CallLogFilter
from apps.calllogs.models import CallLog
from apps.common.feature_flags import device_sessions_enabled
from apps.common.utils import get_branch_filter_ids
from apps.dashboard.services import (
    DashboardAnalyticsService,
    DashboardBranchService,
    DashboardContactService,
    DashboardDeviceService,
    DashboardExportService,
    DashboardSummaryService,
    DashboardTrendService,
    DashboardUserService,
)
from core.authentication import DeviceAuthentication
from apps.dashboard.services.instrumentation import profile_segment
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

logger = logging.getLogger(__name__)


def _authenticated_dashboard_device(request):
    """
    Resolve the registered Android device for a dashboard request.

    JWT sessions are preferred when they carry a server-recorded device_id. If
    the deployed app has not bound the JWT session to a device, validate the
    existing X-Device-ID/X-Device-Secret headers instead. Query params are not
    used for access control.
    """
    auth = getattr(request, "auth", None)
    if auth and hasattr(auth, "device_id"):
        return auth

    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return None

    if device_sessions_enabled():
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            session = UserDeviceSession.objects.filter(
                user=user,
                access_token_hash=UserDeviceSession.hash_token(parts[1]),
                is_active=True,
                status=UserDeviceSession.STATUS_ACTIVE,
            ).order_by("-last_activity", "-last_login").first()
            if session and session.device_id:
                from apps.devices.models import Device

                return Device.objects.filter(
                    device_id=session.device_id,
                    branch_id=getattr(user, "branch_id", None),
                    is_registered=True,
                ).only("id", "device_id", "branch_id").first()

    if request.headers.get("X-Device-ID") or request.headers.get("X-Device-Secret"):
        try:
            authenticated = DeviceAuthentication().authenticate(request)
        except exceptions.AuthenticationFailed:
            raise
        if authenticated:
            device, _ = authenticated
            if getattr(device, "branch_id", None) == getattr(user, "branch_id", None):
                return device

    return None


class DashboardOverviewView(APIView):
    """
    Returns call type counts for the dashboard overview.

    Android SPA-manager requests are scoped to the authenticated registered
    device before aggregation. Admin/area-manager branch-level behavior is
    unchanged.
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
        authenticated_device = None

        if getattr(user, "role", None) == "spa_manager":
            authenticated_device = _authenticated_dashboard_device(request)
            if authenticated_device:
                queryset = queryset.filter(device=authenticated_device)
            else:
                queryset = queryset.none()

        if not authenticated_device and branch_ids and branch_ids != ["NONE"]:
            queryset = queryset.filter(branch_id__in=branch_ids)
        elif not authenticated_device and branch_ids == ["NONE"]:
            queryset = queryset.none()

        with profile_segment("dashboard.overview", request):
            filtered_qs = CallLogFilter(request.query_params, queryset=queryset).qs
            final_record_count = filtered_qs.count()

            stats = filtered_qs.aggregate(
                total=Count("id"),
                incoming=Count("id", filter=Q(call_type="incoming")),
                outgoing=Count("id", filter=Q(call_type="outgoing")),
                missed=Count("id", filter=Q(call_type="missed")),
                rejected=Count("id", filter=Q(call_type="rejected")),
            )

        quick_date = request.query_params.get("quick_date")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        branch_id = request.query_params.get("branch")

        logger.info(
            "Dashboard Analytics",
            extra={
                "branch_id": getattr(authenticated_device, "branch_id", None) or branch_id or branch_ids or None,
                "device_uid": getattr(authenticated_device, "device_id", None),
                "date_filter": quick_date or {"start_date": start_date, "end_date": end_date},
                "final_record_count": final_record_count,
            },
        )

        return Response(
            {
                "total": stats["total"] or 0,
                "incoming": stats["incoming"] or 0,
                "outgoing": stats["outgoing"] or 0,
                "missed": stats["missed"] or 0,
                "rejected": stats["rejected"] or 0,
            }
        )


class DashboardStatsView(APIView):
    """
    Legacy dashboard KPI endpoint.

    Keep /api/v1/dashboard/stats/ response fields unchanged for the deployed
    React dashboard and Android clients.
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
    )
    def get(self, request):
        return Response(
            DashboardAnalyticsService.legacy_stats(
                request.user,
                params=request.query_params,
                request=request,
            )
        )


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(DashboardSummaryService.get(request.user, request.query_params, request=request))


class DashboardDevicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(DashboardDeviceService.get(request.user, request.query_params, request=request))


class DashboardBranchesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"branch_performance": DashboardBranchService.get(request.user, request.query_params, request=request)})


class DashboardTrendsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"call_volume_trends": DashboardTrendService.get(request.user, request.query_params, request=request)})


class DashboardUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(DashboardUserService.get(request.user, request.query_params, request=request))


class DashboardContactsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(DashboardContactService.get(request.user, request.query_params, request=request))


class DashboardExportsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(DashboardExportService.get(request.user, request.query_params, request=request))
