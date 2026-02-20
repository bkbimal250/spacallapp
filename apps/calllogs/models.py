from django.db import models
from core.models.timestamped import TimeStampedModel
from core.models.base import BaseModel
from core.constants import CALL_TYPES


class CallLog(BaseModel, TimeStampedModel):
    """
    Raw Call Log Table
    Partitioned by call_time (monthly)
    """

    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="call_logs",
        null=True,
        blank=True,
    )

    device = models.ForeignKey(
        "devices.Device",
        on_delete=models.CASCADE,
        related_name="call_logs",
    )

    phone_number = models.CharField(max_length=20)

    call_type = models.CharField(
        max_length=20,
        choices=CALL_TYPES,
    )

    duration = models.IntegerField(help_text="Duration in seconds")

    sim_slot = models.IntegerField()

    call_time = models.DateTimeField()

    call_hash = models.CharField(max_length=64, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=["branch", "call_time"]),
            models.Index(fields=["call_time"]),
            models.Index(fields=["branch"]),
            models.Index(fields=["device"]),
            models.Index(fields=["phone_number"]),
        ]

        db_table = "call_logs"
