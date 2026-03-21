"""
Views for the Devices app.

Endpoints:
    GET /devices/                → List devices (filtered by role).
    POST /devices/               → Create device record (admin/super_admin only).
    PUT/PATCH /devices/<id>/     → Update device (admin/super_admin only).
    DELETE /devices/<id>/        → Delete device (super_admin only).
    POST /devices/claim/         → Android app claims a device using registration token.

Access Control:
    super_admin   → Full CRUD on all devices.
    admin         → Full CRUD on all devices.
    branch_manager → Read-only, see only devices in their assigned branch.

Android Flow:
    1. Admin creates Device → registration_token generated.
    2. Android app calls POST /devices/claim/ with the token.
    3. System verifies token, assigns device_id + secret_key.
    4. App uses device_id + secret_key for HMAC auth on every sync.
"""

import secrets
from rest_framework import viewsets, permissions, status, decorators
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import models

from .models import Device
from .serializers import DeviceSerializer, ClaimRegistrationSerializer
from apps.common.permissions import IsAdminOrSuperAdmin
from core.authentication import DeviceAuthentication
from core.permissions import IsDevice


class DeviceViewSet(viewsets.ModelViewSet):
    """
    CRUD for Device management.

    Each device represents one Android phone installed at a branch.
    Devices are pre-registered by admin; Android app claims them via token.
    """
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """
        Write operations are restricted to admin and super_admin.
        """
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsAdminOrSuperAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """
        Return devices filtered by the user's role:
            super_admin / admin → All devices.
            branch_manager      → Only devices in their assigned branch.
        """
        user = self.request.user
        queryset = Device.objects.select_related("branch").all().order_by("-created_at")

        # Branch managers can only see devices in their assigned branch
        if user.role == "branch_manager":
            if user.branch:
                queryset = queryset.filter(branch=user.branch)
            else:
                queryset = queryset.none()

        # Admin and super_admin see all devices

        # ─── Optional Filters ─────────────────────────────────────────────────

        # Search by device_id or registration_token
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                models.Q(device_id__icontains=search) |
                models.Q(registration_token__icontains=search)
            )

        # Filter by branch UUID
        branch = self.request.query_params.get("branch", None)
        if branch:
            queryset = queryset.filter(branch_id=branch)

        # Filter by branch city
        city = self.request.query_params.get("city", None)
        if city:
            queryset = queryset.filter(branch__city__icontains=city)

        # Filter by branch state
        state = self.request.query_params.get("state", None)
        if state:
            queryset = queryset.filter(branch__state__icontains=state)

        # Filter by registration status (accepts 'true' or 'false' string)
        is_registered = self.request.query_params.get("is_registered", None)
        if is_registered is not None:
            queryset = queryset.filter(is_registered=is_registered.lower() == "true")

        return queryset

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """
        Returns aggregate device statistics respecting role-based filters.
        """
        queryset = self.get_queryset()
        
        from django.utils import timezone
        from datetime import timedelta
        five_minutes_ago = timezone.now() - timedelta(minutes=5)

        stats = {
            "total": queryset.count(),
            "registered": queryset.filter(is_registered=True).count(),
            "unregistered": queryset.filter(is_registered=False).count(),
            "online": queryset.filter(
                last_heartbeat__gte=five_minutes_ago, 
                is_active=True, 
                is_blocked=False
            ).count(),
            "offline": queryset.filter(
                is_active=True, 
                is_blocked=False
            ).exclude(last_heartbeat__gte=five_minutes_ago).count(),
            "blocked": queryset.filter(is_blocked=True).count(),
            "inactive": queryset.filter(is_active=False).count(),
        }
        return Response(stats)


class ClaimRegistrationView(APIView):
    """
    Android app uses this to claim a pre-registered device.

    Flow:
        1. Android app sends the registration_token (shown to admin on dashboard).
        2. System verifies the token exists and is unclaimed (is_registered=False).
        3. System assigns a unique device_id and a secure secret_key.
        4. Android app stores device_id + secret_key for use in future sync requests.

    This endpoint is public (no auth required) because the device is not yet registered.
    Security is ensured by the one-time-use registration_token.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ClaimRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data["token"]

        # Look up the device by token — must be unclaimed
        try:
            device = Device.objects.select_related("branch").get(
                registration_token=token,
                is_registered=False
            )
        except Device.DoesNotExist:
            return Response(
                {"error": "Invalid or already used registration token."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate unique device credentials
        # device_id format: SPA-<6chars>-<6chars> (e.g. SPA-A1B2C3-D4E5F6)
        device_id = f"SPA-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}"
        secret_key = secrets.token_hex(32)  # 64-character hex secret for HMAC signing

        # Update device with credentials and mark as registered
        device.device_id = device_id
        device.secret_key = secret_key
        device.is_registered = True
        device.registration_token = None  # Invalidate token after use
        device.save(update_fields=["device_id", "secret_key", "is_registered", "registration_token"])

        return Response({
            "status": "success",
            "device_id": device_id,
            "secret_key": secret_key,
            "branch_name": device.branch.spa_name if device.branch else "Unknown Branch",
            "branch_id": str(device.branch.id) if device.branch else None,
        }, status=status.HTTP_200_OK)


class UpdateFCMTokenView(APIView):
    """
    Android app uses this to update its FCM registration token.
    Authenticated via DeviceAuthentication (X-Device-ID + X-Device-Secret).
    """
    authentication_classes = [DeviceAuthentication]
    permission_classes = [IsDevice]

    def post(self, request):
        token = request.data.get("fcm_token")
        if not token:
            return Response({"error": "fcm_token is required"}, status=status.HTTP_400_BAD_REQUEST)

        device = request.user  # The authenticated Device object
        device.fcm_token = token
        device.save(update_fields=["fcm_token"])

        return Response({"status": "success", "message": "FCM token updated successfully"})
