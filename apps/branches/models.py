"""
Branch model for the CallLog SPA Management System.

Relationship Summary:
    Branch  ← (FK) ← Device       : A branch has many devices (Android phones).
    Branch  ← (FK) ← CallLog      : Each call log belongs to a branch (via device).
    Branch  ← (FK) ← LeadManagement : Each lead belongs to a branch.
    Branch  ← (FK) ← User         : A user (branch_manager) is assigned to one branch.
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
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
    spa_name = models.CharField(max_length=255, db_index=True, help_text="Full name of the Spa location.")

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

    # Google Maps shared link for the branch.
    shared_link = models.URLField(
        blank=True,
        null=True,
        help_text="Google Maps shared link for this branch."
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

    # --- Normalized location FK links (Phase 2 migration) ---
    # These are nullable FKs that link to the structured location hierarchy.
    # Legacy text fields (state, city, area) above are preserved as fallback.
    location_state = models.ForeignKey(
        "locations.State",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="branches",
        help_text="Normalized state (FK). Maps to locations.State."
    )
    location_city = models.ForeignKey(
        "locations.City",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="branches",
        help_text="Normalized city (FK). Maps to locations.City."
    )
    location_group = models.ForeignKey(
        "locations.LocationGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="branches",
        help_text="Location group/zone for this branch (FK). Maps to locations.LocationGroup."
    )
    location_area = models.ForeignKey(
        "locations.Area",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="branches",
        help_text="Primary area for this branch (FK). Maps to locations.Area."
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


class BranchOperatingHours(BaseModel, TimeStampedModel, SoftDeleteModel):
    """
    Weekly operating hours for a branch.

    Hours belong to the Branch master data. A missing active row means the
    branch is treated as closed by routing/eligibility services.
    """

    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="operating_hours",
        help_text="Branch these weekly operating hours belong to.",
    )
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices, db_index=True)
    is_closed = models.BooleanField(default=False, db_index=True)
    is_24_hours = models.BooleanField(default=False)
    opens_at = models.TimeField(null=True, blank=True)
    closes_at = models.TimeField(null=True, blank=True)
    timezone = models.CharField(
        max_length=64,
        default=settings.TIME_ZONE,
        help_text="IANA timezone used to evaluate these branch hours.",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "branch_operating_hours"
        ordering = ["branch__spa_name", "weekday", "opens_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "weekday"],
                condition=models.Q(is_deleted=False, is_active=True),
                name="unique_active_branch_hours_weekday",
            ),
        ]
        indexes = [
            models.Index(fields=["branch", "weekday"], name="branch_hours_branch_day_idx"),
            models.Index(fields=["branch", "is_active"], name="branch_hours_branch_active_idx"),
            models.Index(fields=["weekday", "is_active"], name="branch_hours_day_active_idx"),
        ]
        verbose_name = "Branch Operating Hours"
        verbose_name_plural = "Branch Operating Hours"

    def clean(self):
        super().clean()
        if self.is_closed or self.is_24_hours:
            return
        if not self.opens_at or not self.closes_at:
            raise ValidationError("opens_at and closes_at are required unless closed or 24 hours.")

    @property
    def is_overnight(self):
        return bool(
            not self.is_closed
            and not self.is_24_hours
            and self.opens_at
            and self.closes_at
            and self.opens_at > self.closes_at
        )

    def __str__(self):
        return f"{self.branch} - {self.get_weekday_display()}"
