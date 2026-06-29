"""
Views for the Devices app.

Endpoints:
    GET /devices/                -> List devices (filtered by role).
    POST /devices/               -> Create device record (admin/super_admin only).
    PUT/PATCH /devices/<id>/     -> Update device (admin/super_admin only).
    DELETE /devices/<id>/        -> Delete device (super_admin only).
    POST /devices/claim-registration/ -> Android app claims a device using registration token.

Access Control:
    super_admin -> Full CRUD on all devices.
    admin       -> Full CRUD on all devices.
    spa_manager -> Read-only, see only devices in their assigned branch.

Android Flow:
    1. Admin creates Device -> registration_token generated.
    2. Android app calls POST /devices/claim-registration/ with the token.
    3. System verifies token, assigns device_id + secret_key.
    4. App uses device_id + secret_key for every sync.
"""

import logging
import secrets
import uuid
import hashlib

from django.db import IntegrityError, transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.exceptions import ParseError
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
    DeviceStorageReportSerializer,
    RestoreRegistrationSerializer,
)


logger = logging.getLogger(__name__)

CLEANUP_CONFIG = {
    "cleanup_enabled": True,
    "delete_synced_call_logs_after_days": 15,
    "delete_uploaded_audio_after_days": 7,
    "delete_cache_after_days": 3,
    "delete_temp_after_days": 2,
    "delete_debug_logs_after_days": 7,
    "failed_sync_retention_days": 30,
    "warn_storage_mb": 1500,
    "critical_storage_mb": 2000,
    "max_cleanup_per_run_mb": 1000,
    "run_cleanup_when_charging_only": False,
    "run_cleanup_on_wifi_only": False,
    "cleanup_requested": False,
}


def _request_context(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    request_id = request.headers.get("X-Request-ID") or getattr(request, "_device_request_id", None)
    if not request_id:
        request_id = str(uuid.uuid4())
        request._device_request_id = request_id

    return {
        "request_id": request_id,
        "path": getattr(request, "path", ""),
        "remote_ip": forwarded_for.split(",")[0].strip() if forwarded_for else request.META.get("REMOTE_ADDR"),
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


def _coded_error(message, code, request, extra=None):
    return {
        "error": message,
        "code": code,
        "request_id": _request_context(request)["request_id"],
        **(extra or {}),
    }


def _safe_errors(errors):
    if isinstance(errors, list):
        return [_safe_errors(item) for item in errors]
    if isinstance(errors, dict):
        return {str(key): _safe_errors(value) for key, value in errors.items()}
    return str(errors)


def _token_diagnostics(token):
    if not token:
        return {"token_present": False, "token_length": 0}
    return {
        "token_present": True,
        "token_length": len(token),
        "token_sha256_prefix": hashlib.sha256(token.encode("utf-8")).hexdigest()[:12],
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

        queryset = Device.objects.select_related("branch", "health", "compliance_state").all().order_by("-created_at")

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

    @action(detail=True, methods=["post"])
    def send_update_notification(self, request, pk=None):
        from apps.monitoring.compliance import DeviceComplianceService

        device = self.get_object()
        status_value, reason, state = DeviceComplianceService.check_device(device)
        sent, result = DeviceComplianceService.send_update_notification(device, state=state)
        return Response({
            "sent": sent,
            "result": result,
            "status": status_value,
            "reason": reason,
        })

    @action(detail=True, methods=["post"])
    def mark_followed_up(self, request, pk=None):
        from apps.monitoring.compliance import DeviceComplianceService

        state = DeviceComplianceService.mark_followed_up(self.get_object())
        return Response({"status": "success", "followed_up_at": state.followed_up_at})


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
                device = Device.objects.select_for_update().get(
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
                        _coded_error(
                            "This Android device is already registered. Use restore-registration.",
                            "registration_required",
                            request,
                        ),
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
                _coded_error("Invalid or already used registration token.", "registration_required", request),
                status=status.HTTP_404_NOT_FOUND,
            )
        except IntegrityError:
            logger.exception(
                "Device claim failed: credential or android_id uniqueness conflict",
                extra={"android_id": android_id, **_request_context(request)},
            )
            return Response(
                _coded_error("Registration could not be completed. Please retry.", "registration_required", request),
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
        old_device_id = serializer.validated_data.get("old_device_id") or ""
        fcm_token = serializer.validated_data.get("fcm_token") or ""
        app_version = serializer.validated_data.get("app_version") or ""
        device_model = serializer.validated_data.get("device_model") or ""
        manufacturer = serializer.validated_data.get("manufacturer") or ""

        try:
            with transaction.atomic():
                device = Device.objects.select_for_update().select_related("branch").get(
                    android_id=android_id,
                    is_registered=True,
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
                        _coded_error("Device is not allowed to restore registration.", "inactive_device", request),
                        status=status.HTTP_403_FORBIDDEN,
                    )

                if old_device_id and device.device_id and old_device_id != device.device_id:
                    logger.info(
                        "Device restore replacing stale local device_id",
                        extra={
                            "old_device_id": old_device_id,
                            "device_id": device.device_id,
                            "android_id": android_id,
                            **_request_context(request),
                        },
                    )

                if not device.device_id:
                    device.device_id = f"SPA-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}"
                    while Device.objects.filter(device_id=device.device_id).exclude(pk=device.pk).exists():
                        device.device_id = f"SPA-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}"
                if not device.secret_key:
                    device.secret_key = secrets.token_hex(32)

                update_fields = ["device_id", "secret_key", "updated_at"]
                if fcm_token and device.fcm_token != fcm_token:
                    device.fcm_token = fcm_token
                    update_fields.append("fcm_token")
                device.save(update_fields=update_fields)

                if app_version or device_model or manufacturer:
                    from apps.monitoring.models import DeviceHealth
                    health_defaults = {}
                    if app_version:
                        health_defaults["app_version"] = app_version[:40]
                    if device_model:
                        health_defaults["device_model"] = device_model[:255]
                    if manufacturer:
                        health_defaults["manufacturer"] = manufacturer[:120]
                    if health_defaults:
                        DeviceHealth.objects.update_or_create(device=device, defaults=health_defaults)
                if fcm_token:
                    try:
                        from apps.monitoring.compliance import DeviceComplianceService
                        DeviceComplianceService.mark_fcm_valid(device)
                        DeviceComplianceService.check_device(device)
                    except Exception:
                        logger.exception("Failed to clear device compliance after restore")
        except Device.DoesNotExist:
            logger.warning(
                "Device restore failed: android_id not registered",
                extra={"android_id": android_id, **_request_context(request)},
            )
            return Response(
                _coded_error(
                    "This phone is not registered in CRM. Please contact admin or register again.",
                    "android_id_not_registered",
                    request,
                ),
                status=status.HTTP_404_NOT_FOUND,
            )

        if not device.device_id or not device.secret_key:
            logger.error(
                "Device restore failed: registered device missing credentials",
                extra={"device_pk": str(device.pk), "android_id": android_id, **_request_context(request)},
            )
            return Response(
                _coded_error(
                    "This phone is not registered in CRM. Please contact admin or register again.",
                    "registration_required",
                    request,
                ),
                status=status.HTTP_409_CONFLICT,
            )

        logger.info(
            "Device restore succeeded",
            extra={"device_id": device.device_id, "android_id": android_id, **_request_context(request)},
        )
        return Response(_registration_payload(device), status=status.HTTP_200_OK)


class UpdateFCMTokenSerializer(serializers.Serializer):
    fcm_token = serializers.CharField(allow_blank=False, trim_whitespace=True)


class CurrentDeviceView(APIView):
    """
    Return the CRM identity for the authenticated Android handset.

    SIM values reported by the latest heartbeat take precedence over the
    manager-entered fallback values stored on the Device record.
    """
    authentication_classes = [DeviceAuthentication]
    permission_classes = [IsDevice]

    @extend_schema(
        summary="Get Current Android Device",
        description="Returns the authenticated phone name, branch, and latest known SIM numbers.",
        responses={200: inline_serializer(
            name="CurrentAndroidDeviceResponse",
            fields={
                "device_id": serializers.CharField(),
                "phone_name": serializers.CharField(allow_blank=True),
                "branch_name": serializers.CharField(allow_blank=True),
                "sim_1_number": serializers.CharField(allow_null=True),
                "sim_2_number": serializers.CharField(allow_null=True),
            },
        )},
    )
    def get(self, request):
        device = request.auth
        from apps.monitoring.models import DeviceHealth

        health = DeviceHealth.objects.filter(device=device).first()
        return Response({
            "device_id": device.device_id,
            "phone_name": device.phone_name or "",
            "branch_name": device.branch.spa_name if device.branch else "",
            "sim_1_number": (
                getattr(health, "sim_1_number", None) or device.sim_1_number
            ),
            "sim_2_number": (
                getattr(health, "sim_2_number", None) or device.sim_2_number
            ),
        })


class UpdateFCMTokenView(APIView):
    """
    Android app uses this to update its FCM registration token.
    Authenticated via DeviceAuthentication (X-Device-ID + X-Device-Secret).
    """
    authentication_classes = [DeviceAuthentication]
    permission_classes = [IsDevice]

    def handle_exception(self, exc):
        if isinstance(exc, ParseError):
            context = _request_context(self.request)
            logger.warning(
                "FCM token update rejected: malformed request payload",
                extra=context,
            )
            return Response(
                {
                    "error": "Malformed JSON payload.",
                    "code": "malformed_json",
                    "details": str(exc.detail),
                    "request_id": context["request_id"],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().handle_exception(exc)

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
        context = {
            **_request_context(request),
            "device_id": getattr(request.auth, "device_id", None),
            "has_x_device_id": bool(request.headers.get("X-Device-ID")),
            "has_x_device_secret": bool(request.headers.get("X-Device-Secret")),
            "content_type": request.META.get("CONTENT_TYPE", ""),
        }
        logger.info("FCM token update received", extra=context)

        serializer = UpdateFCMTokenSerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning(
                "FCM token update rejected: invalid payload",
                extra={
                    **context,
                    "invalid_fields": sorted(serializer.errors.keys()),
                    "serializer_errors": _safe_errors(serializer.errors),
                    "payload_type": type(request.data).__name__,
                },
            )
            return Response(
                {
                    "error": "fcm_token is required",
                    "code": "validation_error",
                    "details": serializer.errors,
                    "request_id": context["request_id"],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = serializer.validated_data["fcm_token"]
        device = request.auth
        if not device or not getattr(device, "device_id", None):
            logger.warning(
                "FCM token update rejected: device auth not ready",
                extra={**context, **_token_diagnostics(token)},
            )
            return Response(
                {
                    "error": "Invalid Device Credentials",
                    "code": "device_auth_required",
                    "request_id": context["request_id"],
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            with transaction.atomic():
                locked_device = Device.objects.select_for_update().get(pk=device.pk)
                locked_device.fcm_token = token
                locked_device.save(update_fields=["fcm_token", "updated_at"])
                try:
                    from apps.monitoring.compliance import DeviceComplianceService
                    DeviceComplianceService.mark_fcm_valid(locked_device)
                    DeviceComplianceService.check_device(locked_device)
                except Exception:
                    logger.exception("Failed to clear device FCM compliance flag")
        except Device.DoesNotExist:
            logger.warning(
                "FCM token update rejected: authenticated device disappeared before save",
                extra={**context, **_token_diagnostics(token)},
            )
            return Response(
                {
                    "error": "Invalid Device Credentials",
                    "code": "device_not_found",
                    "request_id": context["request_id"],
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        logger.info("FCM token updated", extra={**context, **_token_diagnostics(token)})
        return Response({"status": "success", "message": "FCM token updated successfully"})


class CleanupConfigView(APIView):
    authentication_classes = [DeviceAuthentication]
    permission_classes = [IsDevice]

    def get(self, request, device_id):
        if request.auth.device_id != device_id:
            return Response({"error": "Device mismatch", "code": "invalid_device"}, status=status.HTTP_403_FORBIDDEN)
        return Response(CLEANUP_CONFIG)


class StorageReportView(APIView):
    authentication_classes = [DeviceAuthentication]
    permission_classes = [IsDevice]

    def post(self, request, device_id):
        device = request.auth
        if device.device_id != device_id:
            return Response({"error": "Device mismatch", "code": "invalid_device"}, status=status.HTTP_403_FORBIDDEN)

        serializer = DeviceStorageReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        status_value = self._storage_status(data)
        report = serializer.save(device=device, storage_status=status_value, raw_payload=request.data)

        if status_value != "NORMAL":
            try:
                from apps.monitoring.services import MonitoringAlertService
                MonitoringAlertService.raise_event(
                    device=device,
                    event_type="sync_failure",
                    description=f"Device {device.device_id} app storage is {status_value.lower()}: {report.total_app_storage_mb:.0f} MB. Do not clear app data.",
                )
            except Exception:
                logger.exception("Failed to raise storage alert")

        return Response({"status": "success", "storage_status": status_value, "cleanup_config": CLEANUP_CONFIG})

    def _storage_status(self, data):
        total = data.get("total_app_storage_mb") or 0
        if total >= CLEANUP_CONFIG["critical_storage_mb"]:
            return "CRITICAL"
        if total >= CLEANUP_CONFIG["warn_storage_mb"]:
            return "WARNING"
        if (data.get("unsynced_call_count") or 0) > 100 or (data.get("pending_sync_count") or 0) > 100:
            return "WARNING"
        return "NORMAL"
