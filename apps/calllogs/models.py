"""
CallLog model for the CallLog SPA Management System.

Relationship:
    CallLog → (FK) → Branch  : Which branch this call belongs to (via device).
    CallLog → (FK) → Device  : Which Android device captured this call.
    CallLog → (FK) → Contact : Optional link to a known contact in the system.
    CallLog ← (OneToOne) ← LeadManagement : Every call log auto-generates one lead.

Data Flow:
    1. Android device captures call via CallReceiver.
    2. App syncs call log batch to /calllogs/sync/ API.
    3. Backend creates CallLog records (deduped by call_hash).
    4. For each new CallLog, a LeadManagement record is auto-created with status='pending'.
    5. Branch manager reviews leads, updates status (ringing, coming, interested, etc.)
"""

from django.db import models
from core.models import TimeStampedModel, BaseModel
from core.constants import CALL_TYPES


class CallLog(BaseModel, TimeStampedModel):
    """
    Raw call log entry synced from an Android device at a Spa branch.

    Each call log is associated with:
        - A Branch (for access control and reporting)
        - A Device (the physical phone that captured the call)
        - Optionally a Contact (if the phone number is a known customer)

    Deduplication is handled via call_hash (SHA-256 of phone+time+type+device).
    Partitioned by call_time (monthly) for performance at scale.
    """

    # Branch that owns this call log — inherited from the device's branch
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="call_logs",
        null=True,
        blank=True,
        db_index=True,
        help_text="The branch where this call was captured. Inherited from device.branch."
    )

    # The Android device that captured this call
    device = models.ForeignKey(
        "devices.Device",
        on_delete=models.CASCADE,
        related_name="call_logs",
        help_text="The device that captured this call log."
    )

    # Optional: linked to a Contact if the number is a known customer
    contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.SET_NULL,
        related_name="call_logs",
        null=True,
        blank=True,
        help_text="Known contact linked by phone number (auto-matched by last 10 digits)."
    )

    # The external phone number (caller or callee depending on call_type)
    phone_number = models.CharField(
        max_length=20,
        db_index=True,
        help_text="Phone number of the external party (caller or callee)."
    )

    # Type of call: incoming, outgoing, missed, rejected
    call_type = models.CharField(
        max_length=20,
        choices=CALL_TYPES,
        db_index=True,
        help_text="Type of call: incoming, outgoing, missed, or rejected."
    )

    # Duration in seconds (0 for missed/rejected)
    duration = models.IntegerField(
        help_text="Call duration in seconds. 0 for missed or rejected calls."
    )

    # SIM slot used (1 or 2) — normalized from Android's 0-indexed slots
    sim_slot = models.IntegerField(
        help_text="SIM slot that handled this call: 1 or 2."
    )

    # Exact timestamp of the call (device local time, stored as UTC)
    call_time = models.DateTimeField(
        help_text="Exact date and time of the call."
    )
    device_reported_call_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Original device-reported call time when the server had to use a safe timestamp."
    )
    is_time_invalid = models.BooleanField(default=False, db_index=True)
    invalid_time_reason = models.CharField(max_length=64, blank=True, default="")

    # Unique hash to prevent duplicate submissions from the Android app
    # SHA-256 or MD5 of combination: phone_number + call_time + call_type + device_id
    call_hash = models.CharField(
        max_length=64,
        unique=True,
        help_text="Unique hash for deduplication. Prevents duplicate call log entries."
    )

    # Normalized phone number (last 10 digits) for robust matching
    phone_normalized = models.CharField(
        max_length=10, 
        db_index=True, 
        null=True, 
        blank=True,
        help_text="Stores the last 10 digits only for robust cross-format matching."
    )

    def save(self, *args, **kwargs):
        """
        Normalize phone number and auto-match contact if possible.
        """
        # Store last 10 digits for fast lookup
        if self.phone_number:
            import re
            clean_digits = re.sub(r'\D', '', self.phone_number)
            self.phone_normalized = clean_digits[-10:] if len(clean_digits) >= 10 else clean_digits

        if not self.contact and self.phone_normalized:
            from apps.contacts.models import Contact
            contact = Contact.objects.filter(phone_normalized=self.phone_normalized).first()
            if contact:
                self.contact = contact
        
        super().save(*args, **kwargs)

    class Meta:
        db_table = "call_logs"
        indexes = [
            models.Index(fields=["branch", "call_time"]),  # Primary query pattern
            models.Index(fields=["call_time"]),             # Time-range filtering
            models.Index(fields=["branch"]),                # Branch-based filtering
            models.Index(fields=["device"]),                # Device-based filtering
            models.Index(fields=["phone_number"]),          # Search by number
            models.Index(fields=["phone_normalized"]),      # Faster matching logic
            models.Index(fields=["call_hash"]),             # Dedup lookups
        ]
        ordering = ["-call_time"]
        verbose_name = "Call Log"
        verbose_name_plural = "Call Logs"

    def __str__(self):
        branch_name = self.branch.spa_name if self.branch else "Unknown Branch"
        return f"{self.phone_number} ({self.call_type}) — {branch_name} — {self.call_time}"


class MissedCallFollowUp(BaseModel, TimeStampedModel):
    """
    Tracking for missed calls that require a follow-up outgoing call.
    Categorizes performance based on SLA windows (10m, 30m, 1h).
    """

    SLA_STATUS = (
        ("GOOD", "Within 10 mins"),
        ("OK", "Within 30 mins"),
        ("LATE", "Within 1 hour"),
        ("MISSED", "No follow-up / > 1 hour"),
        ("CUSTOMER_RECALL", "Customer recalled"),
    )

    # The missed call log being tracked
    missed_call = models.OneToOneField(
        "CallLog",
        on_delete=models.CASCADE,
        related_name="followup_status",
        limit_choices_to={"call_type": "missed"},
    )

    # Branch and manager at the time of missed call (denormalized for query performance)
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="missed_call_followups",
    )

    # The call that served as the follow-up
    followup_call = models.ForeignKey(
        "CallLog",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="serves_as_followup",
        limit_choices_to={"call_type__in": ["outgoing", "incoming"]},
    )

    is_followed_up = models.BooleanField(default=False, db_index=True)
    first_followup_time = models.DateTimeField(null=True, blank=True)
    followup_attempt_count = models.IntegerField(default=0)

    # SLA categorization
    sla_status = models.CharField(
        max_length=20, 
        choices=SLA_STATUS, 
        default="MISSED", 
        db_index=True
    )

    # Notification tracking (steps: 0=none, 1=10m, 2=30m, 3=1h)
    notification_step = models.IntegerField(default=0, db_index=True)

    class Meta:
        db_table = "missed_call_followups"
        indexes = [
            models.Index(fields=["branch", "is_followed_up"]),
            models.Index(fields=["sla_status"]),
            models.Index(fields=["created_at"]),
        ]
        verbose_name = "Missed Call Follow-Up"
        verbose_name_plural = "Missed Call Follow-Ups"

    def __str__(self):
        return f"Follow-up for {self.missed_call.phone_number} - {self.sla_status}"
