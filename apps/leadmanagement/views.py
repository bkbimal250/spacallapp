"""
Views for the Lead Management app.

Endpoints:
    GET  /leads/                  → List leads (filtered by role/branch).
    POST /leads/                  → Create a manual lead (branch_manager/admin).
    PATCH /leads/<id>/            → Update lead status, remarks, booking_date.
    DELETE /leads/<id>/           → Delete lead (super_admin only).
    GET  /leads/branch_summary/   → Per-branch lead statistics.
    POST /leads/sync/ (device)    → Android device syncs manual leads.

Access Control:
    super_admin   → See and manage all leads.
    admin         → See and manage all leads.
    branch_manager → See and update only leads for their assigned branch.

Lead Status Flow:
    Auto-created as 'pending' when call log is synced from Android.
    Branch manager follows up: ringing → coming → interested / not_interested.

Note:
    Leads are auto-created by DeviceSyncView in the calllogs app.
    This viewset handles manual creation and status updates.
"""

from rest_framework import viewsets, permissions, filters, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q

from .models import LeadManagement
from .serializers import LeadManagementSerializer, LeadManagementListSerializer
from .filters import LeadFilter
from apps.calllogs.models import CallLog
from apps.contacts.models import Contact
from apps.common.permissions import IsSuperAdmin
from core.authentication import DeviceAuthentication
from core.permissions import IsDevice


class LeadManagementViewSet(viewsets.ModelViewSet):
    """
    Lead Management viewset for the web dashboard.

    Auto-created leads (from call log sync) are listed here.
    Branch managers update lead status as they follow up with customers.

    Filtering:
        ?status=pending|ringing|coming|interested|not_interested
        ?search=<phone_number_or_remarks>
        ?branch=<uuid>   (admin only)
        ?ordering=created_at|booking_date|status
    """
    serializer_class = LeadManagementSerializer
    
    def get_serializer_class(self):
        """Use a lightweight serializer for the dashboard list view."""
        if self.action == "list":
            return LeadManagementListSerializer
        return LeadManagementSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LeadFilter
    search_fields = ["calllog__phone_number", "remarks", "contact__name"]
    ordering_fields = ["created_at", "booking_date", "status"]
    ordering = ["-created_at"]

    def get_permissions(self):
        """
        Delete is super_admin only.
        All other operations require simple authentication.
        """
        if self.action in ["destroy", "bulk_delete"]:
            return [permissions.IsAuthenticated(), IsSuperAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """
        Return leads filtered by the user's role.

        super_admin / admin → All leads across all branches.
        branch_manager      → Only leads for their assigned branch.
        """
        if getattr(self, "swagger_fake_view", False):
            return LeadManagement.objects.none()

        user = self.request.user
        qs = LeadManagement.objects.select_related(
            "branch", "contact", "calllog"
        ).all()

        # Optimization: prune columns for the list view
        if self.action == "list":
            qs = qs.only(
                "id", "status", "booking_date", "created_at",
                "branch__id", "branch__spa_name",
                "contact__id", "contact__name",
                "calllog__id", "calllog__phone_number", "calllog__call_type"
            )
        else:
            # For detail views, include audit trail related fields
            qs = qs.select_related("created_by", "updated_by")

        # Branch manager: strict filter to their single assigned branch
        if user.is_authenticated and hasattr(user, 'role') and user.role == "branch_manager":
            if user.branch:
                qs = qs.filter(branch=user.branch)
            else:
                # No branch assigned → return nothing (prevent data leak)
                return qs.none()

        return qs

    def perform_create(self, serializer):
        """
        Create a manual lead.

        If a calllog is specified, auto-fill contact from the call log.
        Sets created_by to the current user.
        For branch_manager, auto-assigns their branch if not specified.
        """
        user = self.request.user
        extra_data = {}

        # Auto-fill contact from the linked call log
        calllog_id = self.request.data.get("calllog")
        if calllog_id:
            try:
                cl = CallLog.objects.select_related("contact", "branch").get(id=calllog_id)
                if cl.contact and not self.request.data.get("contact"):
                    extra_data["contact"] = cl.contact
                # Also auto-fill branch from call log
                if not self.request.data.get("branch"):
                    extra_data["branch"] = cl.branch
            except CallLog.DoesNotExist:
                pass

        # Branch manager: auto-assign their branch
        if user.role == "branch_manager" and user.branch and "branch" not in extra_data:
            if not self.request.data.get("branch"):
                extra_data["branch"] = user.branch

        serializer.save(**extra_data)

    @extend_schema(
        summary="List Leads",
        description="List all leads in the user's scope. Supports filtering and search."
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create Lead",
        description="Manually create a lead. Branch and contact can be auto-filled if calllog is provided."
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Retrieve Lead")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Update Lead")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partial Update Lead")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete Lead (Admin Only)")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def perform_update(self, serializer):
        """Track who last updated this lead."""
        serializer.save(updated_by=self.request.user)

    @extend_schema(
        summary="Branch Lead Summary",
        description="Returns per-branch lead statistics (total vs status counts).",
        parameters=[
            OpenApiParameter("branch_search", type=str, description="Search by branch name or code"),
            OpenApiParameter("city", type=str, description="Filter by branch city"),
            OpenApiParameter("branch_status", type=str, description="Filter by branch status (active/inactive)"),
        ],
        responses={200: inline_serializer(
            name="BranchLeadSummary",
            many=True,
            fields={
                "branch_id": serializers.UUIDField(),
                "branch_name": serializers.CharField(),
                "city": serializers.CharField(),
                "area": serializers.CharField(),
                "total_leads": serializers.IntegerField(),
                "total_pending": serializers.IntegerField(),
                "total_ringing": serializers.IntegerField(),
                "total_coming": serializers.IntegerField(),
                "total_interested": serializers.IntegerField(),
                "total_not_interested": serializers.IntegerField(),
            }
        )}
    )
    @action(detail=False, methods=["get"])
    def branch_summary(self, request):
        """
        Returns per-branch lead statistics.

        Respects role-based access control:
            admin/super_admin → all branches
            branch_manager → only their branch

        Additional filters:
            ?branch_search=<name_or_code>
            ?city=<city>
            ?branch_status=active|inactive (branch active status)
        """
        qs = self.get_queryset()

        # Use the filterset to apply filters (branch_search, city, branch_status)
        filtered_qs = self.filter_queryset(qs)

        summary = filtered_qs.values(
            "branch__id",
            "branch__spa_name",
            "branch__city",
            "branch__area",
        ).annotate(
            total_leads=Count("id"),
            total_pending=Count("id", filter=Q(status="pending")),
            total_ringing=Count("id", filter=Q(status="ringing")),
            total_coming=Count("id", filter=Q(status="coming")),
            total_interested=Count("id", filter=Q(status="interested")),
            total_not_interested=Count("id", filter=Q(status="not_interested")),
        ).order_by("branch__spa_name")

        page = self.paginate_queryset(summary)
        result = self._format_branch_summary(page if page is not None else summary)

        if page is not None:
            return self.get_paginated_response(result)
        return Response(result, status=status.HTTP_200_OK)

    def _format_branch_summary(self, summary):
        """Helper to format branch summary queryset into clean response dicts."""
        return [
            {
                "branch_id": s["branch__id"],
                "branch_name": s["branch__spa_name"] or "Unknown Branch",
                "city": s["branch__city"] or "N/A",
                "area": s["branch__area"] or "N/A",
                "total_leads": s["total_leads"],
                "total_pending": s["total_pending"],
                "total_ringing": s["total_ringing"],
                "total_coming": s["total_coming"],
                "total_interested": s["total_interested"],
                "total_not_interested": s["total_not_interested"],
            }
            for s in summary
        ]


class LeadsSyncView(viewsets.ViewSet):
    """
    Android App Lead Sync Endpoint.

    Allows the Android app to manually report leads (contacts who called
    and expressed interest before being captured by the auto-lead system).

    Authentication: Device auth (HMAC using device_id + secret_key).

    Note: This is for MANUAL leads from the app. The primary lead creation
    happens automatically in DeviceSyncView when call logs are synced.

    Payload (array of lead objects):
        [
          {
            "phone_number": "+919876543210",
            "call_hash": "abc...",       (optional — links to existing call log)
            "status": "interested",
            "remarks": "Customer wants massage package",
            "booking_date": "2024-01-20"  (optional)
          }
        ]
    """
    authentication_classes = [DeviceAuthentication]
    permission_classes = [IsDevice]

    @extend_schema(
        summary="Batch Sync Leads (Device)",
        description="Bulk upload leads captured manually on the Android device.",
        request=inline_serializer(
            name="BatchLeadSyncRequest",
            many=True,
            fields={
                "phone_number": serializers.CharField(),
                "call_hash": serializers.CharField(required=False),
                "status": serializers.CharField(required=False),
                "remarks": serializers.CharField(required=False),
                "booking_date": serializers.DateField(required=False),
            }
        ),
        responses={201: inline_serializer(
            name="BatchLeadSyncResponse",
            fields={
                "status": serializers.CharField(),
                "synced_count": serializers.IntegerField()
            }
        )}
    )
    def create(self, request):
        device = request.auth
        payloads = request.data

        if not isinstance(payloads, list):
            return Response(
                {"error": "Payload must be a JSON array of lead objects."},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_count = 0

        for item in payloads:
            phone_number = item.get("phone_number")
            if not phone_number:
                continue  # Skip items without a phone number

            # Try to find the associated call log by hash first
            call_hash = item.get("call_hash")
            calllog = None

            if call_hash:
                calllog = CallLog.objects.filter(call_hash=call_hash).first()

            if not calllog:
                # Fall back: find the most recent call from this number at this branch
                # NOTE: We keep endswith here for phone_number check as it's the external field,
                # but we could add phone_normalized to CallLog too if needed later.
                last_10 = phone_number[-10:] if len(phone_number) >= 10 else phone_number
                calllog = CallLog.objects.filter(
                    phone_number__endswith=last_10,
                    branch_id=device.branch_id,
                ).order_by("-call_time").first()

            if calllog:
                # Upsert lead for this call log — avoid creating duplicates
                obj, created = LeadManagement.objects.get_or_create(
                    calllog=calllog,
                    defaults={
                        "contact": calllog.contact,
                        "branch": calllog.branch,
                        "status": item.get("status", "pending"),
                        "remarks": item.get("remarks", ""),
                        "booking_date": item.get("booking_date"),
                    }
                )
                if created:
                    created_count += 1
            else:
                # Manual lead without a matching call log
                # Try to match contact by phone number using indexed normalization
                last_10 = phone_number[-10:] if len(phone_number) >= 10 else phone_number
                contact = Contact.objects.filter(phone_normalized=last_10).first()

                LeadManagement.objects.create(
                    branch=device.branch,
                    contact=contact,
                    status=item.get("status", "pending"),
                    remarks=f"[Manual from App] {item.get('remarks', '')}",
                    booking_date=item.get("booking_date"),
                )
                created_count += 1

        return Response({
            "status": "success",
            "synced_count": created_count,
        }, status=status.HTTP_201_CREATED)
