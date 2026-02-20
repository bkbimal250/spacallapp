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

    device_id = models.CharField(max_length=255, unique=True)

    secret_key = models.CharField(max_length=64, editable=False)

    sim_1_number = models.CharField(max_length=20)
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
        ]

    def save(self, *args, **kwargs):
        if not self.secret_key:
            self.secret_key = secrets.token_hex(32)
        super().save(*args, **kwargs)

    def __str__(self):
        # Handle potential None for branch or spa_name during incomplete saves or tests
        spa_name = self.branch.spa_name if self.branch else "Unknown Branch"
        return f"{self.device_id} - {spa_name}"
