"""
Branch model for the CallLog SPA Management System.

Relationship Summary:
    Branch  ← (FK) ← Device       : A branch has many devices (Android phones).
    Branch  ← (FK) ← CallLog      : Each call log belongs to a branch (via device).
    Branch  ← (FK) ← LeadManagement : Each lead belongs to a branch.
    Branch  ← (FK) ← User         : A user (branch_manager) is assigned to one branch.
"""

from django.db import models
from core.models.base import BaseModel
from core.models.timestamped import TimeStampedModel
from core.models.soft_delete import SoftDeleteModel


class Branch(BaseModel, TimeStampedModel, SoftDeleteModel):
    """
    Represents a Spa / Branch location.

    Each branch has one or more Android devices installed.
    Call logs are captured per-device and attributed to this branch.
    A branch_manager user is assigned to manage this branch.

    Soft-delete is supported (is_deleted flag via SoftDeleteModel).
    """

    # Human-readable name of the spa / branch
    spa_name = models.CharField(max_length=255, help_text="Full name of the Spa location.")

    # Unique short code for the branch, e.g. 'SPA-001'
    code = models.CharField(
        max_length=20,
        help_text="Unique short code identifying this branch (e.g. 'SPA-001')."
    )

    # Location details
    state = models.CharField(max_length=100, db_index=True)
    city = models.CharField(max_length=100, db_index=True)
    area = models.CharField(max_length=100, blank=True)
    postal_code = models.PositiveIntegerField()
    address = models.TextField()

    # Contact info for the branch
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Branch contact phone number."
    )

    # Active flag — inactive branches won't receive new call logs
    is_active = models.BooleanField(default=True)

    # ✅ IMPORTANT: One branch → one group
    branch_group = models.ForeignKey(
        "BranchGroups",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="branches",
        help_text="Each branch belongs to only one group"
    )

    class Meta:
        db_table = "branches"
        constraints = [
            models.UniqueConstraint(
                fields=['code'], 
                condition=models.Q(is_deleted=False),
                name='unique_code_if_not_deleted'
            )
        ]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["state", "city"]),
            models.Index(fields=["is_active"]),
        ]
        verbose_name = "Branch"
        verbose_name_plural = "Branches"

    def __str__(self):
        return f"{self.spa_name} ({self.code})"



class BranchGroups(BaseModel, TimeStampedModel, SoftDeleteModel):
    """
    Represents a group of branches.

    One group can have multiple branches,
    but each branch belongs to only one group.
    """

    name = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "branch_groups"
        constraints = [
            models.UniqueConstraint(
                fields=['name'], 
                condition=models.Q(is_deleted=False),
                name='unique_name_if_not_deleted'
            )
        ]
        verbose_name = "Branch Group"
        verbose_name_plural = "Branch Groups"

    def __str__(self):
        return self.name