"""
Views for the CallLogs app.

Endpoints:
    POST /calllogs/sync/              → Android device syncs call log batch.
    GET  /calllogs/                   → List call logs (filtered by role).
    GET  /calllogs/stats/             → Aggregate stats (total, missed, etc).
    GET  /calllogs/branch_summary/    → Per-branch call log summary.
    GET  /calllogs/export_excel/      → Download call logs as Excel file.
    POST /calllogs/bulk_delete/       → Delete multiple call logs (super_admin only).

Access Control:
    super_admin    → See all call logs across all branches.
    admin          → See all call logs across all branches.
    branch_manager → See only call logs for their assigned branch.

Android Sync Flow:
    1. Android device sends a batch of call log objects to /calllogs/sync/.
    2. Device is authenticated via HMAC (device_id + secret_key).
    3. Each call log is created (duplicate call_hash entries are silently skipped).
    4. For each newly created call log, a LeadManagement record is auto-created
       with status='pending'. This is the core lead generation logic.
    5. Device's last_sync timestamp is updated.
"""

from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count, Q, Sum, Avg
from rest_framework import viewsets, permissions, views, response, status
from rest_framework.decorators import action
import openpyxl
from openpyxl.styles import Font

from .models import CallLog
from .serializers import CallLogSerializer
from core.authentication import DeviceAuthentication
from core.permissions import IsDevice
from apps.common.permissions import IsSuperAdmin


class DeviceSyncView(views.APIView):
    """
    Android device batch sync endpoint.

    Authenticated via DeviceAuthentication (HMAC using device_id + secret_key).
    Accepts a JSON array of call log objects.
    Each unique call (by call_hash) is created exactly once.
    For each new call log, a Lead is auto-created with status='pending'.

    Expected payload (array of objects):
        [
          {
            "phone_number": "+919876543210",
            "call_type": "incoming",
            "duration": 120,
            "sim_slot": 0,
            "call_time": "2024-01-15T10:30:00Z",
            "call_hash": "abc123def456..."
          },
          ...
        ]
    """
    authentication_classes = [DeviceAuthentication]
    permission_classes = [IsDevice]

    def post(self, request):
        device = request.auth  # The authenticated Device object

        payloads = request.data
        if not isinstance(payloads, list):
            return response.Response(
                {"error": "Payload must be a JSON array of call log objects."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ── Step 1: Pre-fetch contacts for all phone numbers in this batch ──
        # We match by last 10 digits to handle variations like +91, 0, etc.
        phone_numbers = {item.get("phone_number") for item in payloads if item.get("phone_number")}

        from apps.contacts.models import Contact
        contact_map = {}  # Maps last_10_digits → Contact object

        if phone_numbers:
            # Build a dynamic OR query to match all phone numbers at once
            contact_query = Q()
            for pn in phone_numbers:
                last_10 = pn[-10:] if len(pn) >= 10 else pn
                contact_query |= Q(phone_number__endswith=last_10)

            contacts = Contact.objects.filter(contact_query)
            for c in contacts:
                c_last_10 = c.phone_number[-10:] if len(c.phone_number) >= 10 else c.phone_number
                contact_map[c_last_10] = c

        # ── Step 2: Build CallLog objects for bulk insert ──
        logs_to_create = []
        for item in payloads:
            # Normalize sim_slot: Android uses 0-indexed (0, 1) → we use 1-indexed (1, 2)
            raw_slot = item.get("sim_slot", 1)
            try:
                raw_slot = int(raw_slot)
                # Android slot 0 → SIM 1, slot 1 → SIM 2 (odd/even fallback for unusual values)
                normalized_slot = 1 if raw_slot % 2 == 0 else 2
            except (ValueError, TypeError):
                normalized_slot = 1

            phone_num = item.get("phone_number")
            log_last_10 = phone_num[-10:] if phone_num and len(phone_num) >= 10 else phone_num

            logs_to_create.append(
                CallLog(
                    branch_id=device.branch_id,     # Inherited from device's assigned branch
                    device_id=device.id,            # The device that captured this call
                    contact=contact_map.get(log_last_10),  # Auto-link if known contact
                    phone_number=phone_num,
                    call_type=item.get("call_type"),
                    duration=item.get("duration", 0),
                    sim_slot=normalized_slot,
                    call_time=item.get("call_time"),
                    call_hash=item.get("call_hash"),
                )
            )

        # ── Step 3: Bulk insert — ignore duplicates (by call_hash unique constraint) ──
        if logs_to_create:
            CallLog.objects.bulk_create(logs_to_create, ignore_conflicts=True)

        # ── Step 4: Auto-create Leads for newly created call logs ──
        # We query the database to find which hashes actually got inserted.
        # This avoids creating duplicate leads for already-existing call logs.
        from apps.leadmanagement.models import LeadManagement

        submitted_hashes = [log.call_hash for log in logs_to_create]

        # Find the real IDs of inserted call logs (only the ones that are new)
        existing_lead_calllog_ids = set(
            LeadManagement.objects.filter(
                calllog__call_hash__in=submitted_hashes
            ).values_list("calllog_id", flat=True)
        )

        # Fetch newly created call logs that don't yet have a lead
        new_logs = CallLog.objects.filter(
            call_hash__in=submitted_hashes
        ).exclude(
            id__in=existing_lead_calllog_ids
        ).values("id", "contact_id", "branch_id")

        # Build lead records for bulk insert
        leads_to_create = [
            LeadManagement(
                calllog_id=log["id"],
                contact_id=log["contact_id"],
                branch_id=log["branch_id"],
                status="pending",  # All new call logs start as pending leads
            )
            for log in new_logs
        ]

        if leads_to_create:
            LeadManagement.objects.bulk_create(leads_to_create, ignore_conflicts=True)

        # ── Step 5: Update sync timestamp ──
        device.last_sync = timezone.now()
        device.save(update_fields=["last_sync"])

        return response.Response({
            "status": "success",
            "synced_count": len(logs_to_create),
            "leads_created": len(leads_to_create),
        }, status=status.HTTP_201_CREATED)


class CallLogViewSet(viewsets.ModelViewSet):
    """
    Call Log CRUD and analytics viewset.

    Used by the web dashboard to view, filter, and analyze call logs.
    Access is filtered by role — branch_managers only see their branch.

    Key custom actions:
        stats          → Aggregate counts and durations.
        branch_summary → Per-branch breakdown of call types.
        export_excel   → Download all filtered logs as an Excel file.
        bulk_delete    → Delete multiple logs (super_admin only).
    """
    serializer_class = CallLogSerializer

    def get_permissions(self):
        """
        Delete operations require super_admin.
        All other operations require simple authentication.
        """
        if self.action in ["destroy", "bulk_delete"]:
            return [permissions.IsAuthenticated(), IsSuperAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """
        Return call logs filtered by the user's role and branch access.

        super_admin / admin → See ALL call logs.
        branch_manager      → See ONLY call logs for their assigned branch.
        """
        user = self.request.user
        queryset = CallLog.objects.select_related(
            "branch", "device", "contact"
        ).all().order_by("-call_time")

        # Branch manager: strict filter to single assigned branch
        if user.role == "branch_manager":
            if user.branch:
                queryset = queryset.filter(branch=user.branch)
            else:
                # No branch assigned → return nothing (prevent data leak)
                return queryset.none()

        # super_admin and admin see all — no filter

        # Apply URL query filters (for list/export actions only)
        if self.action not in ["stats", "branch_summary"]:
            queryset = self._apply_filters(queryset)

        return queryset

    def _apply_filters(self, queryset):
        """
        Apply query parameter filters to the call log queryset.

        Available filters:
            ?search=<number>        → Filter by phone number (partial match).
            ?call_type=<type>       → Filter by call type (incoming/outgoing/missed/rejected).
            ?branch=<uuid>          → Filter by branch UUID (admin/super_admin only).
            ?device=<device_id>     → Filter by device_id string.
            ?start_date=YYYY-MM-DD  → Filter calls on or after this date.
            ?end_date=YYYY-MM-DD    → Filter calls on or before this date.
        """
        params = self.request.query_params

        call_type = params.get("call_type", None)
        if call_type:
            queryset = queryset.filter(call_type=call_type)

        # Branch filter (only meaningful for admin/super_admin — managers are already filtered)
        branch = params.get("branch", None)
        if branch:
            if branch == "null":
                queryset = queryset.filter(branch__isnull=True)
            elif branch.strip() and branch not in ("undefined", ""):
                queryset = queryset.filter(branch_id=branch)

        # Filter by device_id string (the human-readable ID, not UUID)
        device = params.get("device", None)
        if device:
            if device == "null":
                queryset = queryset.filter(device__isnull=True)
            elif device.strip() and device not in ("undefined", ""):
                queryset = queryset.filter(device__device_id=device)

        # Search by phone number (partial / contains)
        search = params.get("search", None)
        if search:
            queryset = queryset.filter(
                Q(phone_number__icontains=search) |
                Q(contact__name__icontains=search)
            )

        # Date range filters
        start_date = params.get("start_date", None)
        if start_date:
            queryset = queryset.filter(call_time__date__gte=start_date)

        end_date = params.get("end_date", None)
        if end_date:
            queryset = queryset.filter(call_time__date__lte=end_date)

        return queryset

    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        """
        Bulk delete call logs by IDs. Restricted to super_admin.
        Expects: {"ids": ["uuid1", "uuid2", ...]}
        """
        ids = request.data.get("ids", [])
        if not ids:
            return response.Response(
                {"error": "No IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted_count, _ = CallLog.objects.filter(id__in=ids).delete()
        return response.Response({
            "status": "success",
            "message": f"Successfully deleted {deleted_count} call log(s)."
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """
        Returns aggregate statistics for the filtered call log queryset.
        Respects role-based branch filtering.

        Response:
            total, incoming, outgoing, missed, rejected, total_duration, avg_duration
        """
        queryset = self._apply_filters(self.get_queryset())
        stats = queryset.aggregate(
            total=Count("id"),
            incoming=Count("id", filter=Q(call_type="incoming")),
            outgoing=Count("id", filter=Q(call_type="outgoing")),
            missed=Count("id", filter=Q(call_type="missed")),
            rejected=Count("id", filter=Q(call_type="rejected")),
            total_duration=Sum("duration"),
            avg_duration=Avg("duration"),
        )
        return response.Response(stats)

    @action(detail=False, methods=["get"])
    def branch_summary(self, request):
        """
        Returns per-branch call log summary.
        Admins see all branches; branch managers see only their branch.

        Filters (in addition to role-based filtering):
            ?branch_search=<name_or_code>  → Search branches by name or code.
            ?city=<city>                   → Filter branches by city.
            ?status=active|inactive        → Filter by branch active status.
        """
        queryset = self.get_queryset()

        # Additional summary-specific filters
        branch_search = request.query_params.get("branch_search", None)
        city = request.query_params.get("city", None)
        active_status = request.query_params.get("status", None)

        if branch_search:
            queryset = queryset.filter(
                Q(branch__spa_name__icontains=branch_search) |
                Q(branch__code__icontains=branch_search)
            )
        if city:
            queryset = queryset.filter(branch__city__icontains=city)
        if active_status == "active":
            queryset = queryset.filter(branch__is_active=True)
        elif active_status == "inactive":
            queryset = queryset.filter(branch__is_active=False)

        summary = queryset.values(
            "branch__id",
            "branch__spa_name",
            "branch__city",
            "branch__area",
        ).annotate(
            total_calls=Count("id"),
            total_missed=Count("id", filter=Q(call_type="missed")),
            total_outgoing=Count("id", filter=Q(call_type="outgoing")),
            total_incoming=Count("id", filter=Q(call_type="incoming")),
        ).order_by("branch__spa_name")

        page = self.paginate_queryset(summary)
        result = self._format_branch_summary(page if page is not None else summary)

        if page is not None:
            return self.get_paginated_response(result)
        return response.Response(result, status=status.HTTP_200_OK)

    def _format_branch_summary(self, summary):
        """Helper to format branch summary queryset into clean response dicts."""
        return [
            {
                "branch_id": s["branch__id"],
                "branch_name": s["branch__spa_name"] or "Unknown Branch",
                "city": s["branch__city"] or "N/A",
                "area": s["branch__area"] or "N/A",
                "total_calls": s["total_calls"],
                "total_missed": s["total_missed"],
                "total_outgoing": s["total_outgoing"],
                "total_incoming": s["total_incoming"],
            }
            for s in summary
        ]

    @action(detail=False, methods=["get"])
    def export_excel(self, request):
        """
        Export call logs as an Excel (.xlsx) file.
        Applies same role-based and filter-based queryset restrictions.
        Uses .iterator() for memory efficiency with large datasets.
        """
        queryset = self.get_queryset().select_related("branch", "device").iterator()

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "Call Logs"

        # Column headers
        headers = [
            "Type", "Number", "Duration (s)", "SIM Slot",
            "Receiver Number", "Branch", "Device ID", "Time"
        ]
        header_font = Font(bold=True)
        for col_num, header_title in enumerate(headers, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.value = header_title
            cell.font = header_font

        # Data rows — using iterator() for memory efficiency (no full queryset load)
        for row_num, log in enumerate(queryset, 2):
            # Determine the receiver's SIM number based on which SIM handled the call
            receiver = "N/A"
            if log.device:
                if log.sim_slot == 1:
                    receiver = log.device.sim_1_number or "N/A"
                elif log.sim_slot == 2:
                    receiver = log.device.sim_2_number or "N/A"

            worksheet.cell(row=row_num, column=1).value = log.call_type
            worksheet.cell(row=row_num, column=2).value = log.phone_number
            worksheet.cell(row=row_num, column=3).value = log.duration
            worksheet.cell(row=row_num, column=4).value = f"SIM {log.sim_slot}"
            worksheet.cell(row=row_num, column=5).value = receiver
            worksheet.cell(row=row_num, column=6).value = log.branch.spa_name if log.branch else "N/A"
            worksheet.cell(row=row_num, column=7).value = log.device.device_id if log.device else "N/A"
            worksheet.cell(row=row_num, column=8).value = (
                log.call_time.strftime("%Y-%m-%d %H:%M:%S") if log.call_time else "N/A"
            )

        # Build HTTP response with Excel content type
        http_response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        http_response["Content-Disposition"] = f'attachment; filename="call_logs_{timestamp}.xlsx"'
        workbook.save(http_response)
        return http_response
