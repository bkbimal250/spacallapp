from django.db import models

from core.models import BaseModel, TimeStampedModel


class RoutingRule(BaseModel, TimeStampedModel):
    """Configuration for call-routing behavior."""

    class RoutingType(models.TextChoices):
        NIGHT = "night", "Night"
        CLOSED_SPA = "closed_spa", "Closed Spa"
        OTHER = "other", "Other"

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    routing_type = models.CharField(
        max_length=30,
        choices=RoutingType.choices,
        default=RoutingType.NIGHT,
        db_index=True,
    )
    enabled = models.BooleanField(default=True, db_index=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    max_recommendations = models.PositiveSmallIntegerField(default=3)
    cooldown_minutes = models.PositiveIntegerField(default=60)
    whatsapp_enabled = models.BooleanField(default=True)
    dry_run = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, db_index=True)
    template_name = models.CharField(max_length=150, blank=True)
    template_language = models.CharField(max_length=20, blank=True, default="en")
    template_version = models.CharField(max_length=50, blank=True)
    active_from = models.DateTimeField(null=True, blank=True)
    active_until = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "callrouting_rules"
        ordering = ["priority", "name"]
        indexes = [
            models.Index(fields=["enabled", "routing_type", "priority"], name="cr_rule_enabled_type_pri_idx"),
            models.Index(fields=["active_from", "active_until"], name="cr_rule_active_window_idx"),
        ]
        verbose_name = "Routing Rule"
        verbose_name_plural = "Routing Rules"

    def __str__(self):
        return self.name


class RoutingRequest(BaseModel, TimeStampedModel):
    """One routing process for one CallLog."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        ROUTED = "routed", "Routed"
        SKIPPED = "skipped", "Skipped"
        FAILED = "failed", "Failed"

    class RejectionReason(models.TextChoices):
        NONE = "", "None"
        INVALID_PHONE = "invalid_phone", "Invalid Phone"
        DUPLICATE = "duplicate", "Duplicate"
        CUSTOMER_COOLDOWN = "customer_cooldown", "Customer Cooldown"
        NO_RULE = "no_rule", "No Rule"
        SOURCE_SPA_OPEN = "source_spa_open", "Source Spa Open"
        NO_CANDIDATE = "no_candidate", "No Candidate"
        DRY_RUN = "dry_run", "Dry Run"
        ERROR = "error", "Error"

    call_log = models.OneToOneField(
        "calllogs.CallLog",
        on_delete=models.CASCADE,
        related_name="routing_request",
    )
    lead = models.ForeignKey(
        "leadmanagement.LeadManagement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="routing_requests",
    )
    routing_rule = models.ForeignKey(
        "callrouting.RoutingRule",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="routing_requests",
    )
    source_branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_routing_requests",
        help_text="Branch relation snapshot from the source CallLog for filtering and audit.",
    )
    source_device = models.ForeignKey(
        "devices.Device",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="routing_requests",
        help_text="Device relation snapshot from the source CallLog for filtering and audit.",
    )
    contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="routing_requests",
    )
    routing_type = models.CharField(
        max_length=30,
        choices=RoutingRule.RoutingType.choices,
        default=RoutingRule.RoutingType.NIGHT,
        db_index=True,
    )
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING, db_index=True)
    rejection_reason = models.CharField(
        max_length=50,
        choices=RejectionReason.choices,
        blank=True,
        default=RejectionReason.NONE,
        db_index=True,
    )
    normalized_phone = models.CharField(max_length=15, blank=True, db_index=True)
    source_branch_open = models.BooleanField(null=True, blank=True)
    source_open_checked_at = models.DateTimeField(null=True, blank=True)
    call_time = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Call time snapshot used for routing decisions.",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "callrouting_requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="cr_req_status_created_idx"),
            models.Index(fields=["routing_type", "status"], name="cr_req_type_status_idx"),
            models.Index(fields=["source_branch", "created_at"], name="cr_req_branch_created_idx"),
            models.Index(fields=["routing_rule", "created_at"], name="cr_req_rule_created_idx"),
            models.Index(fields=["normalized_phone", "created_at"], name="cr_req_phone_created_idx"),
            models.Index(fields=["call_time"], name="cr_req_call_time_idx"),
        ]
        verbose_name = "Routing Request"
        verbose_name_plural = "Routing Requests"

    def __str__(self):
        return f"RoutingRequest {self.id} - {self.status}"


class RoutingCandidate(BaseModel, TimeStampedModel):
    """Evaluation of one Branch for one routing request."""

    routing_request = models.ForeignKey(
        "callrouting.RoutingRequest",
        on_delete=models.CASCADE,
        related_name="candidates",
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="routing_candidates",
    )
    rank = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    relevance_score = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_open = models.BooleanField(default=False, db_index=True)
    is_eligible = models.BooleanField(default=False, db_index=True)
    is_selected = models.BooleanField(default=False, db_index=True)
    rejection_reason = models.CharField(max_length=100, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    evaluated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "callrouting_candidates"
        ordering = ["routing_request", "rank", "-relevance_score", "branch__spa_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["routing_request", "branch"],
                name="unique_callrouting_candidate_branch",
            ),
        ]
        indexes = [
            models.Index(fields=["routing_request", "is_selected"], name="cr_cand_request_selected_idx"),
            models.Index(fields=["branch", "is_selected"], name="cr_cand_branch_selected_idx"),
            models.Index(fields=["is_eligible", "is_open"], name="cr_cand_eligible_open_idx"),
        ]
        verbose_name = "Routing Candidate"
        verbose_name_plural = "Routing Candidates"

    def __str__(self):
        return f"{self.routing_request_id} -> {self.branch_id}"


class RoutingAttempt(BaseModel):
    """A single processing attempt for a routing request."""

    class Status(models.TextChoices):
        STARTED = "started", "Started"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    routing_request = models.ForeignKey(
        "callrouting.RoutingRequest",
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    attempt_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.STARTED, db_index=True)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    error_code = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "callrouting_attempts"
        ordering = ["routing_request", "-attempt_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["routing_request", "attempt_number"],
                name="unique_callrouting_attempt_number",
            ),
        ]
        indexes = [
            models.Index(fields=["routing_request", "status"], name="cr_attempt_request_status_idx"),
            models.Index(fields=["started_at"], name="cr_attempt_started_idx"),
        ]
        verbose_name = "Routing Attempt"
        verbose_name_plural = "Routing Attempts"

    def __str__(self):
        return f"{self.routing_request_id} attempt {self.attempt_number}"


class RoutingEvent(BaseModel):
    """Append-oriented audit event for a routing request."""

    class EventType(models.TextChoices):
        RECEIVED = "received", "Received"
        PHONE_VALIDATED = "phone_validated", "Phone Validated"
        INVALID_PHONE = "invalid_phone", "Invalid Phone"
        RULE_MATCHED = "rule_matched", "Rule Matched"
        NO_RULE = "no_rule", "No Rule"
        SOURCE_SPA_OPEN = "source_spa_open", "Source Spa Open"
        SOURCE_SPA_CLOSED = "source_spa_closed", "Source Spa Closed"
        COOLDOWN_BLOCKED = "cooldown_blocked", "Cooldown Blocked"
        CANDIDATES_FOUND = "candidates_found", "Candidates Found"
        CANDIDATE_SELECTED = "candidate_selected", "Candidate Selected"
        NO_CANDIDATE = "no_candidate", "No Candidate"
        WHATSAPP_QUEUED = "whatsapp_queued", "WhatsApp Queued"
        WHATSAPP_SENT = "whatsapp_sent", "WhatsApp Sent"
        WHATSAPP_DELIVERED = "whatsapp_delivered", "WhatsApp Delivered"
        WHATSAPP_READ = "whatsapp_read", "WhatsApp Read"
        WHATSAPP_FAILED = "whatsapp_failed", "WhatsApp Failed"
        ERROR = "error", "Error"

    routing_request = models.ForeignKey(
        "callrouting.RoutingRequest",
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(max_length=50, choices=EventType.choices, db_index=True)
    message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "callrouting_events"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["routing_request", "created_at"], name="cr_event_request_created_idx"),
            models.Index(fields=["event_type", "created_at"], name="cr_event_type_created_idx"),
        ]
        verbose_name = "Routing Event"
        verbose_name_plural = "Routing Events"

    def __str__(self):
        return f"{self.routing_request_id} - {self.event_type}"


class RoutingWhatsAppMessage(BaseModel, TimeStampedModel):
    """WhatsApp message orchestration record for a routing request."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        QUEUED = "queued", "Queued"
        SENDING = "sending", "Sending"
        SENT = "sent", "Sent"
        DELIVERED = "delivered", "Delivered"
        READ = "read", "Read"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    routing_request = models.ForeignKey(
        "callrouting.RoutingRequest",
        on_delete=models.CASCADE,
        related_name="whatsapp_messages",
    )
    doubletick_message = models.OneToOneField(
        "doubletick.DoubleTickMessage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="routing_whatsapp_message",
    )
    recipient_phone = models.CharField(max_length=15, db_index=True)
    template_name = models.CharField(max_length=150)
    template_language = models.CharField(max_length=20, blank=True, default="en")
    template_payload = models.JSONField(default=dict, blank=True)
    provider_message_id = models.CharField(max_length=255, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    idempotency_key = models.CharField(max_length=120, unique=True)
    queued_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    provider_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "callrouting_whatsapp_messages"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["routing_request"],
                name="unique_callrouting_whatsapp_request",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "created_at"], name="cr_wa_status_created_idx"),
            models.Index(fields=["provider_message_id"], name="cr_wa_provider_msg_idx"),
            models.Index(fields=["recipient_phone", "created_at"], name="cr_wa_recipient_created_idx"),
        ]
        verbose_name = "Routing WhatsApp Message"
        verbose_name_plural = "Routing WhatsApp Messages"

    def __str__(self):
        return f"{self.routing_request_id} - {self.status}"
