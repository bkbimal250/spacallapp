"""
Analytics views for the CallLog SPA Management System.

Provides time-series analytics, peak hours, and conversion rate data
for call logs — filtered by role and branch access.

Access Control:
    super_admin / admin → See all branch data (or filter by ?branch=).
    branch_manager      → See only their assigned branch data.

Time filter options (via ?time_filter=):
    today, yesterday, last_7_days, last_30_days, this_month, custom
"""

from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.functions import ExtractHour
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.calllogs.models import CallLog
from apps.common.utils import apply_branch_filter
from .services import AnalyticsService
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from rest_framework import serializers


def get_date_range(request):
    """
    Parse time_filter query parameter into (start_date, end_date) datetime range.

    time_filter values:
        today       → Current day (midnight to now)
        yesterday   → Previous day
        last_7_days → Past 7 days (default)
        last_30_days→ Past 30 days
        this_month  → 1st of current month to now
        custom      → Requires ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    """
    time_filter = request.query_params.get("time_filter", "last_7_days")
    now = timezone.localtime(timezone.now())

    if time_filter == "custom":
        start_str = request.query_params.get("start_date")
        end_str = request.query_params.get("end_date")
        try:
            start_date = timezone.make_aware(datetime.strptime(start_str, "%Y-%m-%d")) if start_str else now - timedelta(days=7)
            end_date = timezone.make_aware(datetime.strptime(end_str, "%Y-%m-%d")).replace(
                hour=23, minute=59, second=59
            ) if end_str else now
            return start_date, end_date
        except (ValueError, TypeError):
            return now - timedelta(days=7), now

    if time_filter == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_filter == "yesterday":
        yesterday = now - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_filter == "last_30_days":
        start_date = now - timedelta(days=30)
        end_date = now
    elif time_filter == "this_month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    else:  # default: last_7_days
        start_date = now - timedelta(days=7)
        end_date = now

    return start_date, end_date


class AnalyticsOverviewView(APIView):
    """
    Returns call type distribution (incoming, outgoing, missed, rejected)
    for the selected time range and branch scope.

    Used by the frontend to render conversion rate pie/bar charts.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get call type distribution",
        description="Returns call counts grouped by type (incoming, outgoing, missed, rejected) for the selected range.",
        parameters=[
            OpenApiParameter("time_filter", str, description="Range filter: today, yesterday, last_7_days, last_30_days, this_month, custom"),
            OpenApiParameter("branch", str, description="Filter by branch ID"),
            OpenApiParameter("call_type", str, description="Filter by call type: incoming, outgoing, missed, rejected"),
            OpenApiParameter("start_date", str, description="Format: YYYY-MM-DD"),
            OpenApiParameter("end_date", str, description="Format: YYYY-MM-DD"),
        ],
        responses={
            200: inline_serializer(
                name="AnalyticsOverviewResponse",
                fields={
                    "distribution": serializers.ListField(
                        child=inline_serializer(
                            name="CallTypeStat",
                            fields={
                                "name": serializers.CharField(),
                                "value": serializers.IntegerField(),
                            }
                        )
                    )
                }
            )
        }
    )
    def get(self, request):
        start_date, end_date = get_date_range(request)
        user = request.user

        # Start with time-filtered queryset
        base_qs = CallLog.objects.filter(call_time__gte=start_date, call_time__lte=end_date)

        # Apply role-based branch restriction
        branch_id = request.query_params.get("branch")
        base_qs = apply_branch_filter(base_qs, "branch_id", user, extra_branch_id=branch_id)

        # Optional call type filter
        call_type = request.query_params.get("call_type")
        if call_type:
            base_qs = base_qs.filter(call_type=call_type.lower())

        # Aggregate call type stats
        stats = base_qs.aggregate(
            incoming=Count("id", filter=Q(call_type="incoming")),
            outgoing=Count("id", filter=Q(call_type="outgoing")),
            missed=Count("id", filter=Q(call_type="missed")),
            rejected=Count("id", filter=Q(call_type="rejected")),
        )

        # Format for Recharts-compatible structure
        distribution_data = [
            {"name": "Incoming",  "value": stats["incoming"] or 0},
            {"name": "Outgoing",  "value": stats["outgoing"] or 0},
            {"name": "Missed",    "value": stats["missed"] or 0},
            {"name": "Rejected",  "value": stats["rejected"] or 0},
        ]

        return Response({"distribution": distribution_data})


class PeakHoursView(APIView):
    """
    Returns hourly call volume for the selected time range.
    Useful for identifying peak business hours at the spa.

    Response format: [{hour: "9AM", calls: 42}, ...]
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get hourly call volume",
        description="Returns a 24-hour breakdown of call counts to identify peak hours.",
        parameters=[
            OpenApiParameter("time_filter", str, description="Range filter"),
            OpenApiParameter("branch", str, description="Filter by branch ID"),
            OpenApiParameter("call_type", str, description="Filter by call type"),
            OpenApiParameter("start_date", str, description="YYYY-MM-DD"),
            OpenApiParameter("end_date", str, description="YYYY-MM-DD"),
        ],
        responses={
            200: inline_serializer(
                name="PeakHoursResponse",
                many=True,
                fields={
                    "hour": serializers.CharField(),
                    "calls": serializers.IntegerField(),
                }
            )
        }
    )
    def get(self, request):
        start_date, end_date = get_date_range(request)
        user = request.user

        # Start with time-filtered queryset
        queryset = CallLog.objects.filter(call_time__gte=start_date, call_time__lte=end_date)

        # Apply role-based branch restriction
        branch_id = request.query_params.get("branch")
        queryset = apply_branch_filter(queryset, "branch_id", user, extra_branch_id=branch_id)

        # Optional call type filter
        call_type = request.query_params.get("call_type")
        if call_type:
            queryset = queryset.filter(call_type=call_type.lower())

        # Aggregate calls by hour of day
        hourly_data = (
            queryset
            .annotate(extracted_hour=ExtractHour("call_time"))
            .values("extracted_hour")
            .annotate(calls=Count("id"))
            .order_by("extracted_hour")
        )

        # Build a map of hour → call_count
        calls_by_hour = {
            int(h["extracted_hour"]): h["calls"]
            for h in hourly_data
            if h["extracted_hour"] is not None
        }

        # Build complete 24-hour dataset (fill missing hours with 0)
        result = []
        for hour in range(24):
            if hour == 0:
                hour_str = "12AM"
            elif hour == 12:
                hour_str = "12PM"
            else:
                hour_str = f"{hour % 12}{'AM' if hour < 12 else 'PM'}"

            result.append({
                "hour": hour_str,
                "calls": calls_by_hour.get(hour, 0),
            })

        return Response(result)



class CallAnalyticsView(APIView):
    """
    Returns call volume trends and daily metrics.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get call volume trends",
        description="Returns daily call volume counts and type breakdown over time.",
        parameters=[
            OpenApiParameter("time_filter", str, description="Range filter"),
            OpenApiParameter("branch", str, description="Filter by branch ID"),
            OpenApiParameter("start_date", str, description="YYYY-MM-DD"),
            OpenApiParameter("end_date", str, description="YYYY-MM-DD"),
        ],
        responses={
            200: inline_serializer(
                name="CallAnalyticsResponse",
                fields={
                    "trends": serializers.ListField(
                        child=inline_serializer(
                            name="TrendStat",
                            fields={
                                "date": serializers.DateField(),
                                "count": serializers.IntegerField(),
                            }
                        )
                    ),
                    "daily_breakdown": serializers.ListField(
                        child=inline_serializer(
                            name="DailyBreakdown",
                            fields={
                                "date": serializers.DateField(),
                                "incoming": serializers.IntegerField(),
                                "outgoing": serializers.IntegerField(),
                                "missed": serializers.IntegerField(),
                            }
                        )
                    ),
                }
            )
        }
    )
    def get(self, request):
        start_date, end_date = get_date_range(request)
        user = request.user
        
        from apps.common.utils import get_branch_filter_ids
        branch_ids = get_branch_filter_ids(user)
        
        # Override with specific branch if provided (and allowed)
        requested_branch = request.query_params.get("branch")
        if requested_branch and requested_branch != "null":
            branch_ids = [requested_branch]

        call_type = request.query_params.get("call_type")
        data = AnalyticsService.get_call_analytics(branch_ids, start_date, end_date, call_type=call_type)
        return Response(data)


