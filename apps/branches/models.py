from django.db import models
from core.models.base import BaseModel
from core.models.timestamped import TimeStampedModel
from core.models.soft_delete import SoftDeleteModel


class Branch(BaseModel, TimeStampedModel, SoftDeleteModel):
    """
    Branch / Spa Model
    """

    spa_name = models.CharField(max_length=255)

    # REPLACED PositiveIntegerField with CharField as per recommendation
    code = models.CharField(max_length=20, unique=True)

    state = models.CharField(max_length=100, db_index=True)
    city = models.CharField(max_length=100, db_index=True)
    area = models.CharField(max_length=100, blank=True)

    postal_code = models.PositiveIntegerField()

    address = models.TextField()

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "branches"
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["state", "city"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.spa_name} ({self.code})"
