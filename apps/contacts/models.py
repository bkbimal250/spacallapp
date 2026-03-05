# Create your models here.
from django.db import models
from django.conf import settings
from core.models.base import BaseModel
from core.models.timestamped import TimeStampedModel


class Contact(BaseModel, TimeStampedModel):
    """
    Contact Model
    """
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20,unique=True)
    email = models.EmailField(max_length=255,null=True, blank=True)
    country = models.CharField(max_length=255,null=True, blank=True)
    city = models.CharField(max_length=200,null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_contacts",
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="updated_contacts",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "contacts"
        indexes = [
            models.Index(fields=["phone_number"]),
            models.Index(fields=["email"]),
            models.Index(fields=["country"]),
            models.Index(fields=["city"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Always attempt to auto-match and link any existing unlinked CallLogs instantly
        # By matching solely on the last 10 digits.
        from apps.calllogs.models import CallLog
        from apps.leadmanagement.models import LeadManagement
        if self.phone_number:
            last_10 = self.phone_number[-10:] if len(self.phone_number) >= 10 else self.phone_number
            CallLog.objects.filter(phone_number__endswith=last_10, contact__isnull=True).update(contact=self)
            # Also update any unlinked leads for these call logs or leads created manually for this number
            LeadManagement.objects.filter(calllog__phone_number__endswith=last_10, contact__isnull=True).update(contact=self)