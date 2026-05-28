import hmac
import logging

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework import authentication, exceptions


logger = logging.getLogger(__name__)


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
        path = getattr(request, "path", "")

        if not device_id and not secret_key:
            logger.debug("Device auth skipped: missing device headers", extra={"path": path})
            return None

        if not device_id or not secret_key:
            logger.warning(
                "Device auth failed: incomplete device headers",
                extra={"device_id": device_id, "path": path},
            )
            raise exceptions.AuthenticationFailed("Invalid Device Credentials")

        try:
            device = Device.objects.only(
                "id",
                "device_id",
                "secret_key",
                "is_active",
                "is_blocked",
                "branch_id",
            ).get(device_id=device_id)
        except Device.DoesNotExist:
            logger.warning(
                "Device auth failed: unknown device_id",
                extra={"device_id": device_id, "path": path},
            )
            raise exceptions.AuthenticationFailed("Invalid Device Credentials")

        if not device.secret_key or not hmac.compare_digest(device.secret_key, secret_key):
            logger.warning(
                "Device auth failed: invalid secret",
                extra={"device_id": device_id, "path": path},
            )
            raise exceptions.AuthenticationFailed("Invalid Device Credentials")

        if not device.is_active:
            logger.warning(
                "Device auth failed: inactive device",
                extra={"device_id": device_id, "path": path},
            )
            raise exceptions.AuthenticationFailed("Device is inactive")

        if device.is_blocked:
            logger.warning(
                "Device auth failed: blocked device",
                extra={"device_id": device_id, "path": path},
            )
            raise exceptions.AuthenticationFailed("Device is blocked")

        logger.debug("Device auth succeeded", extra={"device_id": device_id, "path": path})
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
