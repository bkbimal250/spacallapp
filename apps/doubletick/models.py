from django.conf import settings
from django.db import models

from core.models import BaseModel, SoftDeleteModel, TimeStampedModel


class DoubleTickLead(BaseModel, TimeStampedModel, SoftDeleteModel):
    """
    WhatsApp lead received from DoubleTick.

    This model is intentionally separate from the existing call-log based
    LeadManagement model so WhatsApp leads can evolve without changing the
    current CRM lead flow.
    """

    class Status(models.TextChoices):
        NEW = "new", "New"
        ASSIGNED = "assigned", "Assigned"
        OPENED = "opened", "Opened"
        CONTACTED = "contacted", "Contacted"
        FOLLOW_UP = "follow_up", "Follow Up"
        BOOKED = "booked", "Booked"
        LOST = "lost", "Lost"
        UNASSIGNED = "unassigned", "Unassigned"
        FAILED = "failed", "Failed"

    customer_name = models.CharField(max_length=255, blank=True)
    whatsapp_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=30, db_index=True)
    normalized_phone = models.CharField(max_length=15, blank=True, db_index=True)
    message = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    area = models.CharField(max_length=100, blank=True)
    service_name = models.CharField(max_length=255, blank=True)
    source_ad = models.CharField(max_length=255, blank=True)
    doubletick_customer_id = models.CharField(max_length=255, blank=True)
    doubletick_chat_id = models.CharField(max_length=255, blank=True)
    doubletick_message_id = models.CharField(max_length=255, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )

    assigned_branch = models.ForeignKey(
        "branches.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="doubletick_leads",
    )
    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="doubletick_leads",
    )
    assigned_device = models.ForeignKey(
        "devices.Device",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="doubletick_leads",
    )

    assigned_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    contacted_at = models.DateTimeField(null=True, blank=True)
    follow_up_at = models.DateTimeField(null=True, blank=True)
    booked_at = models.DateTimeField(null=True, blank=True)
    lost_reason = models.TextField(blank=True)

    is_duplicate = models.BooleanField(default=False, db_index=True)
    duplicate_of = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="duplicates",
    )

    class Meta:
        db_table = "doubletick_leads"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone_number"], name="dt_lead_phone_idx"),
            models.Index(fields=["normalized_phone"], name="dt_lead_norm_phone_idx"),
            models.Index(fields=["city", "area"], name="dt_lead_city_area_idx"),
            models.Index(fields=["status"], name="dt_lead_status_idx"),
            models.Index(fields=["assigned_branch"], name="dt_lead_branch_idx"),
            models.Index(fields=["assigned_user"], name="dt_lead_user_idx"),
            models.Index(fields=["created_at"], name="dt_lead_created_idx"),
        ]

    def __str__(self):
        name = self.customer_name or self.whatsapp_name or self.phone_number
        return f"{name} - {self.status}"


class DoubleTickLeadActivity(BaseModel, TimeStampedModel):
    """
    Timeline entry for a DoubleTick lead.

    Activities make assignment/status changes auditable without touching the
    existing notification or leadmanagement tables.
    """

    class Action(models.TextChoices):
        CREATED = "created", "Created"
        ASSIGNED = "assigned", "Assigned"
        OPENED = "opened", "Opened"
        CONTACTED = "contacted", "Contacted"
        FOLLOW_UP = "follow_up", "Follow Up"
        BOOKED = "booked", "Booked"
        LOST = "lost", "Lost"
        REASSIGNED = "reassigned", "Reassigned"
        FAILED = "failed", "Failed"
        NOTE = "note", "Note"

    lead = models.ForeignKey(
        DoubleTickLead,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="doubletick_activities",
    )
    device = models.ForeignKey(
        "devices.Device",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="doubletick_activities",
    )
    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    note = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "doubletick_lead_activities"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["lead", "created_at"], name="dt_activity_lead_created_idx"),
            models.Index(fields=["action"], name="dt_activity_action_idx"),
        ]

    def __str__(self):
        return f"{self.lead_id} - {self.action}"


class DoubleTickWebhookLog(BaseModel, TimeStampedModel):
    """
    Raw webhook audit log.

    Every webhook is logged before processing so failed payloads can be traced
    and replayed safely if needed.
    """

    event_type = models.CharField(max_length=100, blank=True)
    doubletick_event_id = models.CharField(max_length=255, null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    processed = models.BooleanField(default=False, db_index=True)
    error_message = models.TextField(null=True, blank=True)
    lead = models.ForeignKey(
        DoubleTickLead,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="webhook_logs",
    )

    class Meta:
        db_table = "doubletick_webhook_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type"], name="dt_webhook_event_idx"),
            models.Index(fields=["doubletick_event_id"], name="dt_webhook_event_id_idx"),
            models.Index(fields=["processed"], name="dt_webhook_processed_idx"),
        ]

    def __str__(self):
        return self.event_type or str(self.id)
