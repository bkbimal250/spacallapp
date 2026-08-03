import hashlib

from django.conf import settings
from django.db import models

from core.models.timestamped import TimeStampedModel


class UserDeviceSession(TimeStampedModel):
    STATUS_ACTIVE = "active"
    STATUS_REVOKED = "revoked"
    STATUS_EXPIRED = "expired"

    STATUS_CHOICES = (
        (STATUS_ACTIVE, "Active"),
        (STATUS_REVOKED, "Revoked"),
        (STATUS_EXPIRED, "Expired"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="device_sessions",
    )
    device_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    device_name = models.CharField(max_length=255, blank=True, default="")
    platform = models.CharField(max_length=50, blank=True, default="")
    manufacturer = models.CharField(max_length=120, blank=True, default="")
    model = models.CharField(max_length=120, blank=True, default="")
    android_version = models.CharField(max_length=50, blank=True, default="")
    app_version = models.CharField(max_length=50, blank=True, default="")
    refresh_token_hash = models.CharField(max_length=64, db_index=True)
    access_token_hash = models.CharField(max_length=64, blank=True, default="", db_index=True)
    fcm_token = models.TextField(blank=True, default="")
    ip = models.GenericIPAddressField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    last_refresh = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "user_device_sessions"
        indexes = [
            models.Index(fields=["user", "is_active", "status"], name="user_session_active_idx"),
            models.Index(fields=["refresh_token_hash"], name="user_session_refresh_idx"),
            models.Index(fields=["device_id", "user"], name="user_session_device_idx"),
        ]

    @staticmethod
    def hash_token(token):
        return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()

    def revoke(self):
        self.status = self.STATUS_REVOKED
        self.is_active = False
        self.save(update_fields=["status", "is_active", "updated_at"])
