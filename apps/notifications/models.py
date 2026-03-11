from django.db import models
from core.models import BaseModel, TimeStampedModel


class Notification(BaseModel, TimeStampedModel):
    """
    Log of notifications sent to devices.
    """
    NOTIFICATION_TYPES = (
        ('reminder', 'Reminder'),
        ('alert', 'Alert / Warning'),
        ('system', 'System Announcement'),
        ('sync_issue', 'Device Stopped Syncing'),
    )

    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="The device this notification was sent to."
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES,
        db_index=True
    )
    
    # Tracking
    is_sent = models.BooleanField(default=False)
    firebase_message_id = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.title} - {self.device.device_id}"
