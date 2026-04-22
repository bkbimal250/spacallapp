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
    phone_number = models.CharField(max_length=20, unique=True)
    phone_normalized = models.CharField(max_length=10, db_index=True, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
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
            models.Index(fields=["phone_normalized"]),
            models.Index(fields=["email"]),
            models.Index(fields=["country"]),
            models.Index(fields=["city"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Normalize phone number (store last 10 digits for fast lookup)
        if self.phone_number:
            import re
            clean_digits = re.sub(r'\D', '', self.phone_number)
            self.phone_normalized = clean_digits[-10:] if len(clean_digits) >= 10 else clean_digits
        
        super().save(*args, **kwargs)
        
        # Link unlinked call logs using normalization
        from apps.calllogs.models import CallLog
        from apps.leadmanagement.models import LeadManagement
        if self.phone_normalized:
            CallLog.objects.filter(phone_number__endswith=self.phone_normalized, contact__isnull=True).update(contact=self)
            LeadManagement.objects.filter(calllog__phone_number__endswith=self.phone_normalized, contact__isnull=True).update(contact=self)