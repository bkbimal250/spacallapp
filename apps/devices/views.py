"""
Views for the Devices app.

Endpoints:
    GET /devices/                -> List devices (filtered by role).
    POST /devices/               -> Create device record (admin/super_admin only).
    PUT/PATCH /devices/<id>/     -> Update device (admin/super_admin only).
    DELETE /devices/<id>/        -> Delete device (super_admin only).
    POST /devices/claim/         -> Android app claims a device using registration token.

Access Control:
    super_admin -> Full CRUD on all devices.
    admin       -> Full CRUD on all devices.
    spa_manager -> Read-only, see only devices in their assigned branch.

Android Flow:
    1. Admin creates Device -> registration_token generated.
    2. Android app calls POST /devices/claim/ with the token.
    3. System verifies token, assigns device_id + secret_key.
    4. App uses device_id + secret_key for every sync.
"""

import logging
import secrets

from django.db import IntegrityError, transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsAdminOrSuperAdmin
from apps.common.utils import apply_branch_filter
from core.authentication import DeviceAuthentication
from core.permissions import IsDevice
from .filters import DeviceFilter
from .models import Device
from .serializers import (
    ClaimRegistrationSerializer,
    DeviceSerializer,
    RestoreRegistrationSerializer,
)


logger = logging.getLogger(__name__)


def _request_context(request):
    return {
        "remote_addr": request.META.get("REMOTE_ADDR"),
        "user_agent": request.META.get("HTTP_USER_AGENT", "")[:255],
    }


def _registration_payload(device):
    branch = device.branch
    return {
        "status": "success",
        "device_id": device.device_id,
        "secret_key": device.secret_key,
        "branch_name": branch.spa_name if branch else "Unknown Branch",
        "branch_id": str(branch.id) if branch else None,
        "branch": {
            "id": str(branch.id),
            "spa_name": branch.spa_name,
            "code": branch.code,
            "city": branch.city,
            "state": branch.state,
            "is_active": branch.is_active,
        } if branch else None,
    }


class DeviceViewSet(viewsets.ModelViewSet):
    """
    CRUD for Device management.

    Each device represents one Android phone installed at a branch.
    Devices are pre-registered by admin; Android app claims them via token.
    """
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DeviceFilter

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
            super_admin / admin -> All devices.
            spa_manager         -> Only devices in their assigned branch.
        """
        user = self.request.user

        if not user or not user.is_authenticated or getattr(self, "swagger_fake_view", False):
            if getattr(self, "swagger_fake_view", False):
                return Device.objects.all()
            return Device.objects.none()

        queryset = Device.objects.select_related("branch").all().order_by("-created_at")

        queryset = apply_branch_filter(queryset, "branch_id", user)

        return queryset

    @extend_schema(
        summary="Get aggregate device stats",
        description="Returns counts of total, registered, online/offline, and blocked devices.",
        responses={
            200: inline_serializer(
                name="DeviceStatsResponse",
                fields={
                    "total": serializers.IntegerField(),
                    "registered": serializers.IntegerField(),
                    "unregistered": serializers.IntegerField(),
                    "online": serializers.IntegerField(),
                    "offline": serializers.IntegerField(),
                    "blocked": serializers.IntegerField(),
                    "inactive": serializers.IntegerField(),
                }
            )
        }
    )
    @action(detail=False, methods=["get"])
    def stats(self, request):
        """
        Returns aggregate device statistics respecting role-based filters.
        """
        queryset = self.filter_queryset(self.get_queryset())

        from datetime import timedelta
        from django.utils import timezone

        five_minutes_ago = timezone.now() - timedelta(minutes=5)

        stats = {
            "total": queryset.count(),
            "registered": queryset.filter(is_registered=True).count(),
            "unregistered": queryset.filter(is_registered=False).count(),
            "online": queryset.filter(
                last_heartbeat__gte=five_minutes_ago,
                is_active=True,
                is_blocked=False,
            ).count(),
            "offline": queryset.filter(
                is_active=True,
                is_blocked=False,
            ).exclude(last_heartbeat__gte=five_minutes_ago).count(),
            "blocked": queryset.filter(is_blocked=True).count(),
            "inactive": queryset.filter(is_active=False).count(),
        }
        return Response(stats)

    @extend_schema(
        summary="Regenerate Registration Token",
        description="Invalidates current registration and generates a new token. Use this if a device needs to be re-setup.",
        responses={200: inline_serializer(
            name="RegenerateTokenResponse",
            fields={
                "status": serializers.CharField(),
                "new_token": serializers.CharField()
            }
        )}
    )
    @action(detail=True, methods=["post"])
    def regenerate_token(self, request, pk=None):
        """
        Invalidates current device credentials and generates a new registration token.
        Allows a device to be claimed again by an Android phone.
        """
        device = self.get_object()
        new_token = secrets.token_hex(6).upper()

        device.registration_token = new_token
        device.is_registered = False
        device.device_id = None
        device.android_id = None
        device.secret_key = None
        device.fcm_token = None

        device.save(update_fields=[
            "registration_token", "is_registered", "device_id", "android_id",
            "secret_key", "fcm_token"
        ])

        return Response({
            "status": "success",
            "new_token": new_token
        })


class ClaimRegistrationView(APIView):
    """
    Android app uses this to claim a pre-registered device.

    android_id is optional for backward compatibility. Existing deployed app
    versions can continue claiming with only the one-time registration token.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Claim a device (Android)",
        description="Android app registers itself using a one-time token. Returns device credentials.",
        request=ClaimRegistrationSerializer,
        responses={
            200: inline_serializer(
                name="ClaimRegistrationResponse",
                fields={
                    "status": serializers.CharField(),
                    "device_id": serializers.CharField(),
                    "secret_key": serializers.CharField(),
                    "branch_name": serializers.CharField(),
                    "branch_id": serializers.UUIDField(allow_null=True),
                    "branch": inline_serializer(
                        name="ClaimRegistrationBranchResponse",
                        fields={
                            "id": serializers.UUIDField(),
                            "spa_name": serializers.CharField(),
                            "code": serializers.CharField(allow_null=True),
                            "city": serializers.CharField(allow_null=True),
                            "state": serializers.CharField(allow_null=True),
                            "is_active": serializers.BooleanField(),
                        },
                        allow_null=True,
                    ),
                }
            ),
            404: inline_serializer(
                name="ClaimErrorResponse",
                fields={"error": serializers.CharField()}
            )
        }
    )
    def post(self, request):
        serializer = ClaimRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data["token"]
        android_id = serializer.validated_data.get("android_id")

        try:
            with transaction.atomic():
                device = Device.objects.select_related("branch").select_for_update().get(
                    registration_token=token,
                    is_registered=False,
                )

                if android_id and Device.objects.filter(
                    android_id=android_id,
                    is_registered=True,
                ).exclude(pk=device.pk).exists():
                    logger.warning(
                        "Device claim rejected: android_id already registered",
                        extra={"android_id": android_id, **_request_context(request)},
                    )
                    return Response(
                        {"error": "This Android device is already registered. Use restore-registration."},
                        status=status.HTTP_409_CONFLICT,
                    )

                device_id = f"SPA-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}"
                while Device.objects.filter(device_id=device_id).exists():
                    device_id = f"SPA-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}"

                device.device_id = device_id
                device.secret_key = secrets.token_hex(32)
                device.android_id = android_id or device.android_id
                device.is_registered = True
                device.registration_token = None

                update_fields = ["device_id", "secret_key", "is_registered", "registration_token"]
                if android_id:
                    update_fields.append("android_id")
                device.save(update_fields=update_fields)
        except Device.DoesNotExist:
            logger.warning(
                "Device claim failed: invalid or already used registration token",
                extra={"token_present": bool(token), **_request_context(request)},
            )
            return Response(
                {"error": "Invalid or already used registration token."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except IntegrityError:
            logger.exception(
                "Device claim failed: credential or android_id uniqueness conflict",
                extra={"android_id": android_id, **_request_context(request)},
            )
            return Response(
                {"error": "Registration could not be completed. Please retry."},
                status=status.HTTP_409_CONFLICT,
            )

        logger.info(
            "Device claim succeeded",
            extra={"device_id": device.device_id, "android_id": android_id, **_request_context(request)},
        )
        return Response(_registration_payload(device), status=status.HTTP_200_OK)


class RestoreRegistrationView(APIView):
    """
    Restore credentials for an already registered Android device.

    This self-healing path only returns existing credentials. It never creates a
    Device and does not alter the X-Device-ID/X-Device-Secret auth flow used by
    sync, heartbeat, and FCM endpoints.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Restore existing device registration",
        description="Returns existing credentials for a registered device identified by android_id. Never creates devices.",
        request=RestoreRegistrationSerializer,
        responses={
            200: inline_serializer(
                name="RestoreRegistrationResponse",
                fields={
                    "status": serializers.CharField(),
                    "device_id": serializers.CharField(),
                    "secret_key": serializers.CharField(),
                    "branch_name": serializers.CharField(),
                    "branch_id": serializers.UUIDField(allow_null=True),
                    "branch": inline_serializer(
                        name="RestoreRegistrationBranchResponse",
                        fields={
                            "id": serializers.UUIDField(),
                            "spa_name": serializers.CharField(),
                            "code": serializers.CharField(allow_null=True),
                            "city": serializers.CharField(allow_null=True),
                            "state": serializers.CharField(allow_null=True),
                            "is_active": serializers.BooleanField(),
                        },
                        allow_null=True,
                    ),
                }
            ),
            403: inline_serializer(
                name="RestoreForbiddenResponse",
                fields={"error": serializers.CharField()}
            ),
            404: inline_serializer(
                name="RestoreNotFoundResponse",
                fields={"error": serializers.CharField()}
            ),
        }
    )
    def post(self, request):
        serializer = RestoreRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(
                "Device restore failed: invalid request payload",
                extra=_request_context(request),
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        android_id = serializer.validated_data["android_id"]

        try:
            device = Device.objects.select_related("branch").get(
                android_id=android_id,
                is_registered=True,
            )
        except Device.DoesNotExist:
            logger.warning(
                "Device restore failed: android_id not registered",
                extra={"android_id": android_id, **_request_context(request)},
            )
            return Response(
                {"error": "No registered device found for this android_id."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not device.device_id or not device.secret_key:
            logger.error(
                "Device restore failed: registered device missing credentials",
                extra={"device_pk": str(device.pk), "android_id": android_id, **_request_context(request)},
            )
            return Response(
                {"error": "Device registration is incomplete. Please contact support."},
                status=status.HTTP_409_CONFLICT,
            )

        if not device.is_active or device.is_blocked:
            logger.warning(
                "Device restore rejected: device inactive or blocked",
                extra={
                    "device_id": device.device_id,
                    "android_id": android_id,
                    "is_active": device.is_active,
                    "is_blocked": device.is_blocked,
                    **_request_context(request),
                },
            )
            return Response(
                {"error": "Device is not allowed to restore registration."},
                status=status.HTTP_403_FORBIDDEN,
            )

        logger.info(
            "Device restore succeeded",
            extra={"device_id": device.device_id, "android_id": android_id, **_request_context(request)},
        )
        return Response(_registration_payload(device), status=status.HTTP_200_OK)


class UpdateFCMTokenView(APIView):
    """
    Android app uses this to update its FCM registration token.
    Authenticated via DeviceAuthentication (X-Device-ID + X-Device-Secret).
    """
    authentication_classes = [DeviceAuthentication]
    permission_classes = [IsDevice]

    @extend_schema(
        summary="Update Device FCM Token",
        description="Updates the push notification token for the authenticated device.",
        request=inline_serializer(
            name="UpdateFCMTokenRequest",
            fields={"fcm_token": serializers.CharField()}
        ),
        responses={
            200: inline_serializer(
                name="UpdateFCMTokenResponse",
                fields={
                    "status": serializers.CharField(),
                    "message": serializers.CharField()
                }
            )
        }
    )
    def post(self, request):
        token = request.data.get("fcm_token")
        if not token:
            return Response({"error": "fcm_token is required"}, status=status.HTTP_400_BAD_REQUEST)

        device = request.user
        device.fcm_token = token
        device.save(update_fields=["fcm_token"])

        return Response({"status": "success", "message": "FCM token updated successfully"})
