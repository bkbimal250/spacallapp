import logging

from django.utils import timezone

from apps.common.feature_flags import device_sessions_enabled

from ..models.device_session import UserDeviceSession

logger = logging.getLogger(__name__)


class UserDeviceSessionService:
    @staticmethod
    def _client_ip(request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    @staticmethod
    def record_login(user, request, access_token, refresh_token):
        if not device_sessions_enabled():
            return None

        data = request.data if hasattr(request, "data") else {}
        device_id = str(data.get("device_id") or "").strip()
        if device_id:
            from apps.devices.models import Device

            device_exists = Device.objects.filter(
                device_id=device_id,
                branch_id=getattr(user, "branch_id", None),
                is_registered=True,
                is_active=True,
                is_blocked=False,
            ).only("id").exists()
            if not device_exists:
                logger.warning(
                    "UserDeviceSession login device binding rejected",
                    extra={
                        "user_id": str(getattr(user, "id", "")),
                        "branch_id": str(getattr(user, "branch_id", "")),
                        "device_id": device_id,
                    },
                )
                device_id = ""
        now = timezone.now()
        return UserDeviceSession.objects.create(
            user=user,
            device_id=device_id,
            device_name=str(data.get("device_name") or ""),
            platform=str(data.get("platform") or data.get("client") or ""),
            manufacturer=str(data.get("manufacturer") or ""),
            model=str(data.get("model") or ""),
            android_version=str(data.get("android_version") or ""),
            app_version=str(data.get("app_version") or ""),
            fcm_token=str(data.get("fcm_token") or ""),
            access_token_hash=UserDeviceSession.hash_token(access_token),
            refresh_token_hash=UserDeviceSession.hash_token(refresh_token),
            ip=UserDeviceSessionService._client_ip(request),
            last_login=now,
            last_activity=now,
        )

    @staticmethod
    def revoke_refresh_token(refresh_token):
        if not device_sessions_enabled():
            return

        token_hash = UserDeviceSession.hash_token(refresh_token)
        UserDeviceSession.objects.filter(refresh_token_hash=token_hash, is_active=True).update(
            status=UserDeviceSession.STATUS_REVOKED,
            is_active=False,
            updated_at=timezone.now(),
        )

    @staticmethod
    def rotate_refresh_token(old_refresh_token, new_refresh_token, new_access_token=None, device_id=None):
        if not device_sessions_enabled():
            return None

        old_hash = UserDeviceSession.hash_token(old_refresh_token)
        session = UserDeviceSession.objects.filter(refresh_token_hash=old_hash, is_active=True).first()
        if not session:
            return None

        session.refresh_token_hash = UserDeviceSession.hash_token(new_refresh_token)
        update_fields = ["refresh_token_hash", "updated_at"]
        if new_access_token:
            session.access_token_hash = UserDeviceSession.hash_token(new_access_token)
            update_fields.append("access_token_hash")
        if device_id and not session.device_id:
            from apps.devices.models import Device

            device = Device.objects.filter(
                device_id=str(device_id).strip(),
                branch_id=getattr(session.user, "branch_id", None),
                is_registered=True,
                is_active=True,
                is_blocked=False,
            ).only("id").first()
            if device:
                session.device_id = str(device_id).strip()
                update_fields.append("device_id")
            else:
                logger.warning(
                    "UserDeviceSession refresh device binding rejected",
                    extra={
                        "user_id": str(getattr(session.user, "id", "")),
                        "branch_id": str(getattr(session.user, "branch_id", "")),
                        "device_id": str(device_id).strip(),
                    },
                )
        session.save(update_fields=update_fields)
        return session
