import secrets
from django.db import models
from core.models.base import BaseModel
from core.models.timestamped import TimeStampedModel
from core.models.soft_delete import SoftDeleteModel


class Device(BaseModel, TimeStampedModel, SoftDeleteModel):
    """
    Android Device installed at branch
    """

    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="devices",
        null=True,
        blank=True,
    )

    device_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    secret_key = models.CharField(max_length=64, editable=False, null=True, blank=True)

    registration_token = models.CharField(max_length=32, unique=True, null=True, blank=True)
    is_registered = models.BooleanField(default=False)

    sim_1_number = models.CharField(max_length=20, blank=True, null=True)
    sim_2_number = models.CharField(max_length=20, blank=True, null=True)

    last_sync = models.DateTimeField(null=True, blank=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)

    class Meta:
        db_table = "devices"
        indexes = [
            models.Index(fields=["device_id"]),
            models.Index(fields=["branch"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["registration_token"]),
        ]

    def save(self, *args, **kwargs):
        if not self.registration_token and not self.is_registered:
            # Generate a clean 12-character token for easier manual entry if needed, 
            # or use secrets.token_hex for higher security.
            self.registration_token = secrets.token_hex(6).upper()
        
        super().save(*args, **kwargs)

    def __str__(self):
        spa_name = self.branch.spa_name if self.branch else "Unknown Branch"
        identifier = self.device_id or f"Unregistered ({self.registration_token})"
        return f"{identifier} - {spa_name}"

