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

    sim_1_number = models.CharField(max_length=20, blank=True, null=True)
    sim_2_number = models.CharField(max_length=20, blank=True, null=True)

    sync_failures = models.IntegerField(default=0)
    
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
        ("permission_denied", "Permission Denied"),
        ("app_crash", "App Crash"),
    )
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    description = models.TextField(blank=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "device_events"
        indexes = [
            models.Index(fields=["event_type", "resolved"]),
            models.Index(fields=["device", "created_at"]),
        ]
