from django.db import models
from core.models.timestamped import TimeStampedModel
from apps.devices.models import Device

class DeviceHealth(TimeStampedModel):
    device = models.OneToOneField(
        Device,
        on_delete=models.CASCADE,
        related_name="health",
    )

    is_online = models.BooleanField(default=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    
    # Device Stats
    battery_level = models.IntegerField(null=True, blank=True)
    signal_strength = models.IntegerField(null=True, blank=True) # dBm
    storage_used_mb = models.FloatField(default=0.0)
    app_version = models.CharField(max_length=20, default="1.0.0")
    device_model = models.CharField(max_length=255, blank=True, null=True)
    manufacturer = models.CharField(max_length=120, blank=True, null=True)
    device_reported_at = models.DateTimeField(null=True, blank=True)
    device_time_skew_seconds = models.IntegerField(null=True, blank=True)

    sim_1_number = models.CharField(max_length=20, blank=True, null=True)
    sim_2_number = models.CharField(max_length=20, blank=True, null=True)

    sync_failures = models.IntegerField(default=0)
    pending_call_count = models.IntegerField(default=0)
    last_sync_error = models.TextField(blank=True, default="")
    network_type = models.CharField(max_length=32, blank=True, default="")
    is_metered = models.BooleanField(default=False)
    is_data_saver_on = models.BooleanField(default=False)
    is_background_restricted = models.BooleanField(default=False)
    is_battery_optimized = models.BooleanField(default=False)
    is_vpn_active = models.BooleanField(default=False)
    is_proxy_configured = models.BooleanField(default=False)
    is_airplane_mode_on = models.BooleanField(default=False)
    last_network_error = models.TextField(blank=True, default="")
    
    # Notification flags to avoid duplicates
    notified_2h = models.BooleanField(default=False)
    notified_24h = models.BooleanField(default=False)

    class Meta:
        db_table = "device_health"

class DeviceEvent(TimeStampedModel):
    EVENT_TYPES = (
        ("offline", "Device Offline"),
        ("sim_change", "SIM Card Changed"),
        ("sync_failure", "Sync Failure"),
        ("battery_low", "Battery Low"),
        ("storage_full", "Storage Full"),
        ("network_weak", "Weak Network Signal"),
        ("permission_denied", "Permission Denied"),
        ("app_crash", "App Crash"),
        ("app_uninstall_suspected", "Possible App Uninstall"),
    )
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=32, choices=EVENT_TYPES)
    description = models.TextField(blank=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "device_events"
        indexes = [
            models.Index(fields=["event_type", "resolved"]),
            models.Index(fields=["device", "created_at"]),
        ]


class DeviceComplianceState(TimeStampedModel):
    STATUS_CHOICES = (
        ("OK", "OK"),
        ("MISSING_ANDROID_ID", "Missing Android ID"),
        ("MISSING_FCM_TOKEN", "Missing FCM Token"),
        ("OUTDATED_APP", "Outdated App"),
        ("HEARTBEAT_MISSING", "Heartbeat Missing"),
        ("SUSPECTED_UNINSTALLED", "Suspected Uninstalled"),
        ("AUTH_BROKEN", "Auth Broken"),
        ("DEVICE_TIME_WRONG", "Device Time Wrong"),
    )

    device = models.OneToOneField(
        Device,
        on_delete=models.CASCADE,
        related_name="compliance_state",
    )
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="OK", db_index=True)
    reason = models.TextField(blank=True)
    fcm_invalid = models.BooleanField(default=False, db_index=True)
    device_time_wrong = models.BooleanField(default=False, db_index=True)
    last_phone_notification_at = models.DateTimeField(null=True, blank=True)
    last_admin_alert_at = models.DateTimeField(null=True, blank=True)
    last_admin_email_at = models.DateTimeField(null=True, blank=True)
    followed_up_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "device_compliance_states"
        indexes = [
            models.Index(fields=["status", "updated_at"], name="device_comp_status__idx"),
            models.Index(fields=["fcm_invalid"], name="device_comp_fcm_inv_idx"),
        ]
