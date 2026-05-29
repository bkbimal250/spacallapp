import hmac
import logging
import uuid

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework import authentication, exceptions


logger = logging.getLogger(__name__)


def _remote_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _request_context(request, device_id=None):
    request_id = request.headers.get("X-Request-ID") or getattr(request, "_device_request_id", None)
    if not request_id:
        request_id = str(uuid.uuid4())
        request._device_request_id = request_id

    return {
        "request_id": request_id,
        "path": getattr(request, "path", ""),
        "remote_ip": _remote_ip(request),
        "device_id": device_id,
    }


def _auth_failed(message, code, context):
    return exceptions.AuthenticationFailed({
        "detail": message,
        "error": message,
        "code": code,
        "request_id": context.get("request_id"),
    })


class DeviceAuthentication(authentication.BaseAuthentication):
    """
    Authenticate Android devices via X-Device-ID and X-Device-Secret headers.

    Backward compatibility: the header contract and returned (device, device)
    tuple are unchanged, so existing sync, heartbeat, and FCM clients keep
    working exactly as before.
    """

    def authenticate(self, request):
        from apps.devices.models import Device

        device_id = request.headers.get("X-Device-ID")
        secret_key = request.headers.get("X-Device-Secret")
        context = _request_context(request, device_id=device_id)

        if not device_id and not secret_key:
            logger.warning(
                "Device auth failed: missing device headers",
                extra={
                    **context,
                    "missing_headers": ["X-Device-ID", "X-Device-Secret"],
                },
            )
            raise _auth_failed("Invalid Device Credentials", "missing_device_headers", context)

        if not device_id or not secret_key:
            missing_headers = []
            if not device_id:
                missing_headers.append("X-Device-ID")
            if not secret_key:
                missing_headers.append("X-Device-Secret")
            logger.warning(
                "Device auth failed: incomplete device headers",
                extra={**context, "missing_headers": missing_headers},
            )
            raise _auth_failed("Invalid Device Credentials", "missing_device_headers", context)

        try:
            device = Device.objects.only(
                "id",
                "device_id",
                "secret_key",
                "is_active",
                "is_blocked",
                "is_registered",
                "branch_id",
            ).get(device_id=device_id)
        except Device.DoesNotExist:
            logger.warning(
                "Device auth failed: unknown device_id",
                extra=context,
            )
            raise _auth_failed("Invalid Device Credentials", "invalid_device_id", context)

        if not device.secret_key or not hmac.compare_digest(device.secret_key, secret_key):
            logger.warning(
                "Device auth failed: invalid secret_key",
                extra={**context, "has_stored_secret": bool(device.secret_key)},
            )
            raise _auth_failed("Invalid Device Credentials", "invalid_secret_key", context)

        if not device.is_registered:
            logger.warning(
                "Device auth failed: stale credentials for unregistered device",
                extra={**context, "is_registered": device.is_registered},
            )
            raise _auth_failed("Invalid Device Credentials", "stale_device_credentials", context)

        if not device.is_active:
            logger.warning(
                "Device auth failed: inactive device",
                extra={**context, "is_active": device.is_active},
            )
            raise _auth_failed("Device is inactive", "device_inactive", context)

        if device.is_blocked:
            logger.warning(
                "Device auth failed: blocked device",
                extra={**context, "is_blocked": device.is_blocked},
            )
            raise _auth_failed("Device is blocked", "device_blocked", context)

        logger.debug("Device auth succeeded", extra=context)
        return (device, device)


class DeviceAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = DeviceAuthentication
    name = 'DeviceAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-Device-ID',
            'description': 'Device Authentication requires X-Device-ID and X-Device-Secret headers.'
        }
