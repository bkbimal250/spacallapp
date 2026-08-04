"""
Device model for the CallLog SPA Management System.

Relationship:
    Device → (FK) → Branch   : Every device belongs to exactly one branch.
    Device ← (FK) ← CallLog  : A device generates many call logs.

Flow:
    1. Admin creates a Device record in the dashboard (branch assigned here).
    2. A registration_token is auto-generated (e.g. 'ABC123').
    3. The Android app on-site uses the token to 'claim' the device.
    4. After claim, device_id and secret_key are assigned — used for API auth.
    5. The Android app uses (device_id + secret_key) for HMAC auth on each sync.
"""

import secrets
from django.db import models
from core.models import BaseModel, TimeStampedModel, SoftDeleteModel


class Device(BaseModel, TimeStampedModel, SoftDeleteModel):
    """
    Android Device installed at a Branch.

    Registration Flow:
        - Admin creates Device → registration_token auto-generated.
        - Android app calls /devices/claim-registration/ with the token.
        - System assigns device_id (e.g. SPA-ABC123-DEF456) and secret_key.
        - App stores these and uses them for authenticating call log syncs.

    Authentication:
        - Each sync request must include device_id + HMAC signature using secret_key.
        - Blocked devices (is_blocked=True) are rejected at the API level.
    """

    # Linked branch — where this physical device is installed
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="devices",
        null=True,
        blank=True,
        help_text="The branch this device is physically installed at."
    )

    # Assigned after claim process (e.g. 'SPA-ABC123-DEF456')
    device_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique device identifier assigned after successful registration."
    )

    # Stable Android OS identifier used only to restore credentials for an
    # already-registered device. Nullable keeps all deployed devices compatible.
    android_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Stable Android identifier used for self-healing credential recovery."
    )

    # HMAC secret key for request signing — only known to the device
    secret_key = models.CharField(
        max_length=64,
        editable=False,
        null=True,
        blank=True,
        help_text="Secret key for HMAC signing. Never expose in API responses."
    )

    # One-time registration token — shown to admin, entered on Android device
    registration_token = models.CharField(
        max_length=32,
        unique=True,
        null=True,
        blank=True,
        help_text="Short token displayed to admin for Android app registration."
    )

    # True once the Android app has claimed this device with the registration_token
    is_registered = models.BooleanField(
        default=False,
        help_text="Whether the device has been claimed by the Android app."
    )

    # SIM card numbers for the device (used to identify receiver in call logs)
    sim_1_number = models.CharField(max_length=20, blank=True, null=True)
    sim_2_number = models.CharField(max_length=20, blank=True, null=True)

    # Human-readable name for the device
    phone_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="Custom name for the phone (e.g. 'Reception Desk')."
    )

    # Firebase Cloud Messaging token for push notifications
    fcm_token = models.TextField(
        null=True, 
        blank=True, 
        help_text="Registration token for Firebase Cloud Messaging."
    )

    # Sync & heartbeat timestamps for monitoring
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time this device successfully synced call logs."
    )
    last_heartbeat = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last heartbeat ping received from this device."
    )

    # Status flags
    is_active = models.BooleanField(default=True, help_text="Active devices can sync data.")
    is_blocked = models.BooleanField(
        default=False,
        help_text="Blocked devices are rejected at API auth level."
    )

    @property
    def is_authenticated(self):
        """Always True for an actual Device instance (used for request.user compatibility)."""
        return True

    @property
    def is_online(self):

        """Returns True if the device has sent a heartbeat within the monitoring threshold."""
        if not self.last_heartbeat:
            return False
        from django.utils import timezone
        from datetime import timedelta
        from django.conf import settings
        threshold_minutes = getattr(settings, "MONITORING_OFFLINE_AFTER_MINUTES", 20)
        return self.last_heartbeat >= (timezone.now() - timedelta(minutes=threshold_minutes))

    @property
    def status(self):
        """Returns string status for display."""
        if not self.is_active:
             return "Inactive"
        if self.is_blocked:
             return "Blocked"
        return "Online" if self.is_online else "Offline"

    class Meta:
        db_table = "devices"
        indexes = [
            models.Index(fields=["device_id"]),
            models.Index(fields=["android_id"], name="devices_android_id_idx"),
            models.Index(fields=["branch"]),
            models.Index(fields=["branch", "last_heartbeat"], name="devices_branch_heartbeat_idx"),
            models.Index(fields=["branch", "last_sync"], name="devices_branch_sync_idx"),
            models.Index(fields=["last_heartbeat"], name="devices_last_heartbeat_idx"),
            models.Index(fields=["last_sync"], name="devices_last_sync_idx"),
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_registered"]),
            models.Index(fields=["registration_token"]),
        ]
        verbose_name = "Device"
        verbose_name_plural = "Devices"

    def save(self, *args, **kwargs):
        # Treat empty string device_id as NULL for unique constraint compatibility
        if self.device_id == "":
            self.device_id = None
        if self.android_id == "":
            self.android_id = None

        # Auto-generate a human-readable registration token (12 hex chars, uppercased)
        # This is shown to the admin and entered into the Android app manually or via QR
        if not self.registration_token and not self.is_registered:
            self.registration_token = secrets.token_hex(6).upper()  # e.g. "A3F9C2B1D0E4"

        super().save(*args, **kwargs)

    def __str__(self):
        spa_name = self.branch.spa_name if self.branch else "Unassigned Branch"
        identifier = self.device_id or f"Unregistered (Token: {self.registration_token})"
        return f"{identifier} — {spa_name}"


class Lastsynchistory(BaseModel):
    """
    Model to track the last synchronization time for each device.

    This is used to monitor device activity and identify devices that haven't
    synced in a while, which may indicate connectivity issues or misconfigurations.
    """

    device = models.OneToOneField(
        Device,
        on_delete=models.CASCADE,
        related_name="last_sync_history",
        help_text="The device this sync history belongs to."
    )
    last_sync_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The timestamp of the last successful synchronization."
    )

    class Meta:
        db_table = "last_sync_history"
        indexes = [
            models.Index(fields=["last_sync_time"], name="lastsync_time_idx"),
        ]
        verbose_name = "Last Sync History"
        verbose_name_plural = "Last Sync Histories"

    def __str__(self):
        return f"Last Sync for {self.device}: {self.last_sync_time}"


class DeviceStorageReport(BaseModel):
    STATUS_NORMAL = "NORMAL"
    STATUS_WARNING = "WARNING"
    STATUS_CRITICAL = "CRITICAL"

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="storage_reports")
    total_app_storage_mb = models.FloatField(default=0)
    db_size_mb = models.FloatField(default=0)
    cache_size_mb = models.FloatField(default=0)
    audio_size_mb = models.FloatField(default=0)
    log_size_mb = models.FloatField(default=0)
    temp_size_mb = models.FloatField(default=0)
    other_size_mb = models.FloatField(default=0)
    unsynced_call_count = models.IntegerField(default=0)
    pending_sync_count = models.IntegerField(default=0)
    failed_sync_count = models.IntegerField(default=0)
    cleanup_deleted_records_count = models.IntegerField(default=0)
    cleanup_deleted_files_count = models.IntegerField(default=0)
    cleanup_freed_mb = models.FloatField(default=0)
    last_cleanup_at = models.DateTimeField(null=True, blank=True)
    reported_at = models.DateTimeField(auto_now_add=True, db_index=True)
    storage_status = models.CharField(max_length=16, default=STATUS_NORMAL, db_index=True)
    raw_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "device_storage_reports"
        indexes = [
            models.Index(fields=["device", "-reported_at"]),
            models.Index(fields=["storage_status", "-reported_at"]),
        ]
