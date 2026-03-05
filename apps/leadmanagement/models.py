from django.db import models
from django.conf import settings
from core.models.base import BaseModel
from core.models.timestamped import TimeStampedModel

class LeadManagement(BaseModel, TimeStampedModel):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("ringing", "ringing"),
        ("coming", "Coming"),
        ("interested", "Interested"),
        ("not_interested", "Not Interested"),
    )

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")
    booking_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

    
    contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.SET_NULL,
        related_name="leads",
        null=True,
        blank=True,
    )

    calllog = models.OneToOneField(
        "calllogs.CallLog",
        on_delete=models.SET_NULL,
        related_name="lead",
        null=True,
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_leads",
        null=True,
        blank=True,
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="updated_leads",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "lead_management"
        indexes = [
            models.Index(fields=["calllog"]),
            models.Index(fields=["status"]),
        ]

    def clean(self):
        super().clean()
        # Convert empty strings to None for fields that should be null
        if self.booking_date == '':
            self.booking_date = None
        if self.remarks == '':
            self.remarks = None

        if self.status in ["pending", "ringing", "not_interested"]:
            self.booking_date = None
            if self.status != "not_interested":
                self.remarks = None

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        number = self.calllog.phone_number if self.calllog else "Unknown Number"
        return f"{number} - {self.status}"
