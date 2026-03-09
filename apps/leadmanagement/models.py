"""
LeadManagement model for the CallLog SPA Management System.

Every call log is automatically treated as a lead:
    - When a call log is synced from Android, a LeadManagement record is
      created automatically with status='pending'.
    - Branch managers work the leads: call back, update status, add remarks.
    - Admins and Super Admins can view all leads across all branches.
    - Branch managers can only see leads for their assigned branch.

Relationship:
    LeadManagement → (OneToOne) → CallLog  : One lead per call log.
    LeadManagement → (FK) → Branch         : Which branch this lead belongs to.
    LeadManagement → (FK) → Contact        : Known customer link (optional).
    LeadManagement → (FK) → User (created_by) : Who created/updated the lead.

Status Flow:
    pending → ringing → coming → interested
                     ↘ not_interested
"""

from django.db import models
from django.conf import settings
from core.models.base import BaseModel
from core.models.timestamped import TimeStampedModel


class LeadManagement(BaseModel, TimeStampedModel):
    """
    Lead record derived from a call log.

    Auto-created with status='pending' whenever a new call log is synced.
    Branch managers update the status as they follow up with the customer.
    """

    STATUS_CHOICES = (
        ("pending", "Pending"),               # Newly received, not yet followed up
        ("ringing", "Ringing"),               # Attempted contact, busy/no answer
        ("coming", "Coming"),                 # Customer confirmed they will visit
        ("interested", "Interested"),         # Customer expressed interest, has booking date
        ("not_interested", "Not Interested"), # Customer declined or not a prospect
    )

    # Lead status — updated by branch manager as they follow up
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
        help_text="Current follow-up status of this lead."
    )

    # Optional booking date — only relevant when status is 'interested' or 'coming'
    booking_date = models.DateField(
        null=True,
        blank=True,
        help_text="Scheduled visit/appointment date. Only used for 'coming' or 'interested' leads."
    )

    # Free-text remarks from the branch manager
    remarks = models.TextField(
        null=True,
        blank=True,
        help_text="Notes from branch manager about follow-up conversation."
    )

    # — Relationships —

    # The call log that originated this lead (OneToOne: one lead per call)
    calllog = models.OneToOneField(
        "calllogs.CallLog",
        on_delete=models.CASCADE,      # If call log deleted, lead should also go
        related_name="lead",
        null=True,
        blank=True,
        help_text="The originating call log for this lead."
    )

    # The branch this lead belongs to — inherited from calllog.branch
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.SET_NULL,
        related_name="leads",
        null=True,
        blank=True,
        help_text="The branch this lead belongs to. Auto-set from calllog.branch."
    )

    # Optional contact link — auto-matched from calllog.contact
    contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.SET_NULL,
        related_name="leads",
        null=True,
        blank=True,
        help_text="Known contact for this lead (auto-matched from call log's phone number)."
    )

    # Audit fields — who created and last updated this lead
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_leads",
        null=True,
        blank=True,
        help_text="User who created this lead (system user for auto-created leads)."
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="updated_leads",
        null=True,
        blank=True,
        help_text="User who last updated this lead's status."
    )

    class Meta:
        db_table = "lead_management"
        indexes = [
            models.Index(fields=["calllog"]),   # Fast lookup by call log
            models.Index(fields=["branch"]),    # Branch-based filtering (access control)
            models.Index(fields=["status"]),    # Status-based filtering
            models.Index(fields=["created_at"]), # Time-based sorting
        ]
        ordering = ["-created_at"]
        verbose_name = "Lead"
        verbose_name_plural = "Leads"

    def clean(self):
        """
        Business rule validation:
            - 'pending' and 'ringing' statuses should not have booking dates or remarks.
            - 'not_interested' can have remarks (for notes) but no booking date.
            - 'coming' and 'interested' can have both booking dates and remarks.
        """
        super().clean()

        # Normalize empty strings to NULL for nullable fields
        if self.booking_date == "":
            self.booking_date = None
        if self.remarks == "":
            self.remarks = None

        # Clear booking_date for statuses where scheduling doesn't make sense
        if self.status in ["pending", "ringing", "not_interested"]:
            self.booking_date = None

        # Clear remarks for early-stage statuses (pending, ringing)
        if self.status in ["pending", "ringing"]:
            self.remarks = None

    def save(self, *args, **kwargs):
        """
        Auto-inherit branch from the linked call log when creating the lead.
        This ensures branch data is always consistent.
        """
        # Always inherit branch from the call log (source of truth)
        if self.calllog and not self.branch:
            self.branch = self.calllog.branch

        # Also inherit contact if not explicitly set
        if self.calllog and not self.contact:
            self.contact = self.calllog.contact

        # Run business rule validation
        self.clean()

        super().save(*args, **kwargs)

    def __str__(self):
        number = self.calllog.phone_number if self.calllog else "Unknown Number"
        branch_name = self.branch.spa_name if self.branch else "Unknown Branch"
        return f"Lead: {number} [{self.status}] — {branch_name}"
