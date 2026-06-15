from django.conf import settings
from django.db import models

from core.models import BaseModel, SoftDeleteModel, TimeStampedModel


class DoubleTickChannel(BaseModel, TimeStampedModel, SoftDeleteModel):
    """
    DoubleTick/WABA channel.

    Channels can narrow regional matching, but final lead distribution always
    uses controlled CRM lead areas and manual area-to-branch mappings.
    """

    name = models.CharField(max_length=255)
    waba_number = models.CharField(max_length=30, unique=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    branch_group = models.ForeignKey(
        "branches.BranchGroups",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="doubletick_channels",
    )
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "doubletick_channels"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.waba_number})"


class DoubleTickCustomer(BaseModel, TimeStampedModel):
    """
    WhatsApp customer identity.

    Identity priority is provider customer id first, normalized phone second.
    One customer may have multiple conversations/inquiries over time.
    """

    dt_customer_id = models.CharField(max_length=255, blank=True, db_index=True)
    phone_number = models.CharField(max_length=30, blank=True)
    normalized_phone = models.CharField(max_length=15, db_index=True)
    customer_name = models.CharField(max_length=255, blank=True)
    whatsapp_name = models.CharField(max_length=255, blank=True)
    channel = models.ForeignKey(
        DoubleTickChannel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="customers",
    )
    raw_profile = models.JSONField(default=dict, blank=True)
    first_seen_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "doubletick_customers"
        ordering = ["-last_seen_at", "-created_at"]
        indexes = [
            models.Index(fields=["dt_customer_id"], name="dt_customer_id_idx"),
            models.Index(fields=["normalized_phone"], name="dt_customer_phone_idx"),
        ]

    def __str__(self):
        return self.customer_name or self.whatsapp_name or self.normalized_phone


class DoubleTickLeadArea(BaseModel, TimeStampedModel, SoftDeleteModel):
    """Controlled CRM area used for WhatsApp lead distribution."""

    class DistributionMode(models.TextChoices):
        BROADCAST_CLAIM = "broadcast_claim", "Broadcast Claim"
        ROUND_ROBIN = "round_robin", "Round Robin"
        MANUAL = "manual", "Manual"

    name = models.CharField(max_length=255)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    normalized_name = models.CharField(max_length=255, db_index=True)
    is_active = models.BooleanField(default=True)
    distribution_mode = models.CharField(
        max_length=30,
        choices=DistributionMode.choices,
        default=DistributionMode.BROADCAST_CLAIM,
    )
    claim_timeout_minutes = models.PositiveIntegerField(default=30)
    contact_start_timeout_minutes = models.PositiveIntegerField(default=10)
    auto_release_enabled = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "doubletick_lead_areas"
        ordering = ["city", "name"]
        indexes = [
            models.Index(fields=["normalized_name"], name="dt_area_norm_idx"),
            models.Index(fields=["city", "is_active"], name="dt_area_city_active_idx"),
        ]

    def __str__(self):
        location = ", ".join(part for part in [self.city, self.name] if part)
        return location or self.normalized_name


class DoubleTickAreaAlias(BaseModel, TimeStampedModel):
    """Search alias for matching raw customer locations to a controlled area."""

    lead_area = models.ForeignKey(
        DoubleTickLeadArea,
        on_delete=models.CASCADE,
        related_name="aliases",
    )
    alias = models.CharField(max_length=255)
    normalized_alias = models.CharField(max_length=255, db_index=True)
    channel = models.ForeignKey(
        DoubleTickChannel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="area_aliases",
    )
    is_active = models.BooleanField(default=True)
    created_from_manual_mapping = models.BooleanField(default=False)

    class Meta:
        db_table = "doubletick_area_aliases"
        indexes = [
            models.Index(fields=["normalized_alias", "is_active"], name="dt_alias_norm_active_idx"),
        ]

    def __str__(self):
        return self.alias


class DoubleTickLeadAreaBranch(BaseModel, TimeStampedModel):
    """Manual mapping between a controlled DoubleTick area and CRM branches."""

    lead_area = models.ForeignKey(
        DoubleTickLeadArea,
        on_delete=models.CASCADE,
        related_name="branch_mappings",
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="doubletick_area_mappings",
    )
    is_active = models.BooleanField(default=True)
    receives_leads = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "doubletick_lead_area_branches"
        unique_together = ("lead_area", "branch")
        ordering = ["priority", "branch__spa_name"]

    def __str__(self):
        return f"{self.lead_area} -> {self.branch}"


class DoubleTickConversation(BaseModel, TimeStampedModel):
    """
    WhatsApp conversation/inquiry.

    A conversation can stay pending forever and does not become a distributable
    lead until a CRM lead area is confirmed.
    """

    class Status(models.TextChoices):
        NEW = "new", "New"
        PENDING = "pending", "Pending"
        AWAITING_CUSTOMER = "awaiting_customer", "Awaiting Customer"
        AWAITING_LOCATION = "awaiting_location", "Awaiting Location"
        AWAITING_SERVICE = "awaiting_service", "Awaiting Service"
        MANUAL_ATTENTION = "manual_attention", "Manual Attention"
        AREA_UNMATCHED = "area_unmatched", "Area Unmatched"
        QUALIFIED = "qualified", "Qualified"
        DISTRIBUTED = "distributed", "Distributed"
        RESOLVED = "resolved", "Resolved"
        INACTIVE = "inactive", "Inactive"
        SPAM = "spam", "Spam"
        CLOSED = "closed", "Closed"

    class PendingReason(models.TextChoices):
        GREETING_ONLY = "greeting_only", "Greeting Only"
        INCOMPLETE_BOT_FLOW = "incomplete_bot_flow", "Incomplete Bot Flow"
        CUSTOMER_STOPPED_REPLYING = "customer_stopped_replying", "Customer Stopped Replying"
        MISSING_LOCATION = "missing_location", "Missing Location"
        INVALID_LOCATION = "invalid_location", "Invalid Location"
        UNMATCHED_LOCATION = "unmatched_location", "Unmatched Location"
        AMBIGUOUS_LOCATION = "ambiguous_location", "Ambiguous Location"
        MANUAL_REPLY_REQUIRED = "manual_reply_required", "Manual Reply Required"
        OTHER = "other", "Other"

    customer = models.ForeignKey(
        DoubleTickCustomer,
        on_delete=models.CASCADE,
        related_name="conversations",
    )
    channel = models.ForeignKey(
        DoubleTickChannel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="conversations",
    )
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.NEW, db_index=True)
    pending_reason = models.CharField(max_length=40, choices=PendingReason.choices, blank=True, db_index=True)
    priority = models.IntegerField(default=0)

    raw_city = models.CharField(max_length=100, blank=True)
    raw_area = models.CharField(max_length=100, blank=True)
    raw_service = models.CharField(max_length=255, blank=True)
    matched_area = models.ForeignKey(
        DoubleTickLeadArea,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="conversations",
    )

    first_message_at = models.DateTimeField(null=True, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    last_customer_message_at = models.DateTimeField(null=True, blank=True)
    last_agent_message_at = models.DateTimeField(null=True, blank=True)
    customer_last_replied_at = models.DateTimeField(null=True, blank=True)
    team_last_replied_at = models.DateTimeField(null=True, blank=True)

    unread_count = models.PositiveIntegerField(default=0)
    requires_manual_attention = models.BooleanField(default=False, db_index=True)
    bot_completed = models.BooleanField(default=False)
    area_confirmed = models.BooleanField(default=False, db_index=True)

    assigned_support_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="doubletick_support_conversations",
    )
    current_lead = models.ForeignKey(
        "doubletick.DoubleTickLead",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="current_for_conversations",
    )
    dt_conversation_id = models.CharField(max_length=255, blank=True, db_index=True)
    raw_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "doubletick_conversations"
        ordering = ["-last_message_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "pending_reason"], name="dt_conv_status_reason_idx"),
            models.Index(fields=["requires_manual_attention"], name="dt_conv_manual_idx"),
            models.Index(fields=["dt_conversation_id"], name="dt_conv_provider_idx"),
            models.Index(fields=["last_message_at"], name="dt_conv_last_msg_idx"),
        ]

    def __str__(self):
        return f"{self.customer} - {self.status}"


class DoubleTickLead(BaseModel, TimeStampedModel, SoftDeleteModel):
    """
    Qualified WhatsApp area lead.

    This remains separate from the existing call-log LeadManagement model. A
    lead is created only after enough area information exists or a CRM user
    manually qualifies the conversation.
    """

    class Status(models.TextChoices):
        QUALIFIED = "qualified", "Qualified"
        AREA_MATCHED = "area_matched", "Area Matched"
        AVAILABLE = "available", "Available"
        CLAIMED = "claimed", "Claimed"
        OPENED = "opened", "Opened"
        CONTACTING = "contacting", "Contacting"
        CONTACTED = "contacted", "Contacted"
        FOLLOW_UP = "follow_up", "Follow Up"
        BOOKED = "booked", "Booked"
        NOT_INTERESTED = "not_interested", "Not Interested"
        RELEASED = "released", "Released"
        EXPIRED = "expired", "Expired"
        LOST = "lost", "Lost"
        CLOSED = "closed", "Closed"
        FAILED = "failed", "Failed"
        # Backward-compatible values from the first DoubleTick implementation.
        NEW = "new", "New"
        ASSIGNED = "assigned", "Assigned"
        UNASSIGNED = "unassigned", "Unassigned"

    conversation = models.ForeignKey(
        DoubleTickConversation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leads",
    )
    customer = models.ForeignKey(
        DoubleTickCustomer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leads",
    )
    channel = models.ForeignKey(
        DoubleTickChannel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leads",
    )

    customer_name = models.CharField(max_length=255, blank=True)
    whatsapp_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=30, db_index=True)
    normalized_phone = models.CharField(max_length=15, blank=True, db_index=True)
    initial_message = models.TextField(blank=True)
    latest_customer_message = models.TextField(blank=True)
    message = models.TextField(blank=True)
    message_type = models.CharField(max_length=50, blank=True, default="text")

    raw_city = models.CharField(max_length=100, blank=True)
    raw_area = models.CharField(max_length=100, blank=True)
    raw_service = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    area = models.CharField(max_length=100, blank=True)
    service_name = models.CharField(max_length=255, blank=True)
    source_ad = models.CharField(max_length=255, blank=True)
    matched_area = models.ForeignKey(
        DoubleTickLeadArea,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leads",
    )

    status = models.CharField(max_length=30, choices=Status.choices, default=Status.QUALIFIED, db_index=True)

    dt_customer_id = models.CharField(max_length=255, blank=True)
    doubletick_customer_id = models.CharField(max_length=255, blank=True)
    doubletick_chat_id = models.CharField(max_length=255, blank=True)
    doubletick_message_id = models.CharField(max_length=255, blank=True)
    dt_first_message_id = models.CharField(max_length=255, blank=True)
    dt_last_message_id = models.CharField(max_length=255, blank=True)

    received_at = models.DateTimeField(null=True, blank=True)
    qualified_at = models.DateTimeField(null=True, blank=True)
    area_matched_at = models.DateTimeField(null=True, blank=True)
    distributed_at = models.DateTimeField(null=True, blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    contacted_at = models.DateTimeField(null=True, blank=True)
    follow_up_at = models.DateTimeField(null=True, blank=True)
    booked_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    current_branch = models.ForeignKey(
        "branches.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="current_doubletick_leads",
    )
    current_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="current_doubletick_leads",
    )
    current_device = models.ForeignKey(
        "devices.Device",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="current_doubletick_leads",
    )
    active_assignment = models.ForeignKey(
        "doubletick.DoubleTickLeadAssignment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="active_for_leads",
    )

    # Backward-compatible assignment fields used by existing routes/serializers.
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

    lost_reason = models.TextField(blank=True)
    closed_reason = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)

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
            models.Index(fields=["current_branch"], name="dt_lead_current_branch_idx"),
            models.Index(fields=["current_user"], name="dt_lead_current_user_idx"),
            models.Index(fields=["matched_area", "status"], name="dt_lead_area_status_idx"),
            models.Index(fields=["created_at"], name="dt_lead_created_idx"),
        ]

    def __str__(self):
        name = self.customer_name or self.whatsapp_name or self.phone_number
        return f"{name} - {self.status}"


class DoubleTickMessage(BaseModel, TimeStampedModel):
    """Complete local chat history for a DoubleTick conversation."""

    class Direction(models.TextChoices):
        INBOUND = "inbound", "Inbound"
        OUTBOUND = "outbound", "Outbound"

    class Origin(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        BOT = "bot", "Bot"
        AGENT = "agent", "Agent"
        API = "api", "API"
        SYSTEM = "system", "System"

    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        QUEUED = "queued", "Queued"
        SENT = "sent", "Sent"
        DELIVERED = "delivered", "Delivered"
        READ = "read", "Read"
        FAILED = "failed", "Failed"

    conversation = models.ForeignKey(
        DoubleTickConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    lead = models.ForeignKey(
        DoubleTickLead,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="messages",
    )
    customer = models.ForeignKey(
        DoubleTickCustomer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="messages",
    )
    dt_message_id = models.CharField(max_length=255, blank=True, db_index=True)
    message_id = models.CharField(max_length=255, blank=True, db_index=True)
    direction = models.CharField(max_length=20, choices=Direction.choices, db_index=True)
    origin = models.CharField(max_length=20, choices=Origin.choices, db_index=True)
    message_type = models.CharField(max_length=50, default="text")
    text = models.TextField(blank=True)
    media_url = models.URLField(null=True, blank=True)
    caption = models.TextField(null=True, blank=True)
    interactive_payload = models.JSONField(default=dict, blank=True)
    callback_data = models.TextField(null=True, blank=True)
    sender_display_name = models.CharField(max_length=255, blank=True)
    sent_by_raw = models.CharField(max_length=255, blank=True)
    assigned_to_raw = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RECEIVED, db_index=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="doubletick_sent_messages",
    )
    customer_number = models.CharField(max_length=30, blank=True)
    waba_number = models.CharField(max_length=30, blank=True)
    message_timestamp = models.DateTimeField(null=True, blank=True, db_index=True)
    received_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "doubletick_messages"
        ordering = ["message_timestamp", "received_at", "sent_at", "created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"], name="dt_msg_conv_created_idx"),
            models.Index(fields=["dt_message_id"], name="dt_msg_dt_id_idx"),
            models.Index(fields=["message_id"], name="dt_msg_provider_id_idx"),
            models.Index(fields=["direction", "origin"], name="dt_msg_direction_origin_idx"),
            models.Index(fields=["status"], name="dt_msg_status_idx"),
            models.Index(fields=["message_timestamp"], name="dt_msg_timestamp_idx"),
        ]

    def __str__(self):
        return self.text[:80] or self.message_type


class DoubleTickTeamMemberMapping(BaseModel, TimeStampedModel):
    """Map DoubleTick associate identifiers to readable CRM sender names."""

    doubletick_user_id = models.CharField(max_length=255, blank=True, db_index=True)
    doubletick_phone = models.CharField(max_length=30, blank=True, db_index=True)
    display_name = models.CharField(max_length=255)
    crm_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="doubletick_team_mappings",
    )
    channel = models.ForeignKey(
        DoubleTickChannel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="team_member_mappings",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "doubletick_team_member_mappings"
        ordering = ["display_name"]
        indexes = [
            models.Index(fields=["doubletick_user_id", "is_active"], name="dt_team_user_active_idx"),
            models.Index(fields=["doubletick_phone", "is_active"], name="dt_team_phone_active_idx"),
        ]

    def __str__(self):
        return self.display_name


class DoubleTickLeadVisibility(BaseModel, TimeStampedModel):
    """Visibility says who can see a lead; it is not ownership."""

    lead = models.ForeignKey(DoubleTickLead, on_delete=models.CASCADE, related_name="visibilities")
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, related_name="doubletick_visibilities")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    device = models.ForeignKey("devices.Device", null=True, blank=True, on_delete=models.CASCADE)
    is_visible = models.BooleanField(default=True)
    notification_sent = models.BooleanField(default=False)
    notified_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    notification_error = models.TextField(blank=True)

    class Meta:
        db_table = "doubletick_lead_visibilities"
        indexes = [
            models.Index(fields=["lead", "branch"], name="dt_visibility_lead_branch_idx"),
            models.Index(fields=["user", "is_visible"], name="dt_visibility_user_idx"),
            models.Index(fields=["device", "is_visible"], name="dt_visibility_device_idx"),
        ]


class DoubleTickLeadAssignment(BaseModel, TimeStampedModel):
    """Claim/contact attempt history. Only one active assignment is allowed."""

    class Status(models.TextChoices):
        CLAIMED = "claimed", "Claimed"
        OPENED = "opened", "Opened"
        CONTACT_STARTED = "contact_started", "Contact Started"
        CONTACTED = "contacted", "Contacted"
        FOLLOW_UP = "follow_up", "Follow Up"
        RELEASED = "released", "Released"
        EXPIRED = "expired", "Expired"
        BOOKED = "booked", "Booked"
        LOST = "lost", "Lost"
        CLOSED = "closed", "Closed"

    lead = models.ForeignKey(DoubleTickLead, on_delete=models.CASCADE, related_name="assignments")
    attempt_number = models.PositiveIntegerField(default=1)
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, related_name="doubletick_assignments")
    assigned_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="doubletick_assignments")
    assigned_device = models.ForeignKey("devices.Device", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.CLAIMED, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    contact_started_at = models.DateTimeField(null=True, blank=True)
    contact_completed_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    follow_up_at = models.DateTimeField(null=True, blank=True)
    outcome = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    release_reason = models.TextField(blank=True)

    class Meta:
        db_table = "doubletick_lead_assignments"
        ordering = ["-attempt_number"]
        indexes = [
            models.Index(fields=["lead", "is_active"], name="dt_assignment_lead_active_idx"),
            models.Index(fields=["assigned_user", "is_active"], name="dt_assignment_user_active_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["lead"],
                condition=models.Q(is_active=True),
                name="unique_active_doubletick_assignment",
            )
        ]


class DoubleTickActivity(BaseModel):
    """Immutable timeline for conversations, leads, assignments and messages."""

    class Action(models.TextChoices):
        WEBHOOK_RECEIVED = "webhook_received", "Webhook Received"
        CONVERSATION_CREATED = "conversation_created", "Conversation Created"
        MESSAGE_RECEIVED = "message_received", "Message Received"
        MESSAGE_SENT = "message_sent", "Message Sent"
        MANUAL_REPLY_SENT = "manual_reply_sent", "Manual Reply Sent"
        CUSTOMER_REPLIED = "customer_replied", "Customer Replied"
        PENDING_REASON_UPDATED = "pending_reason_updated", "Pending Reason Updated"
        MANUAL_ATTENTION_REQUIRED = "manual_attention_required", "Manual Attention Required"
        LOCATION_REQUESTED = "location_requested", "Location Requested"
        LOCATION_RECEIVED = "location_received", "Location Received"
        AREA_MATCHED = "area_matched", "Area Matched"
        AREA_UNMATCHED = "area_unmatched", "Area Unmatched"
        LEAD_QUALIFIED = "lead_qualified", "Lead Qualified"
        LEAD_DISTRIBUTED = "lead_distributed", "Lead Distributed"
        NOTIFICATION_SENT = "notification_sent", "Notification Sent"
        VIEWED = "viewed", "Viewed"
        CLAIMED = "claimed", "Claimed"
        CONTACT_STARTED = "contact_started", "Contact Started"
        STATUS_UPDATED = "status_updated", "Status Updated"
        FOLLOW_UP_ADDED = "follow_up_added", "Follow Up Added"
        RELEASED = "released", "Released"
        REASSIGNED = "reassigned", "Reassigned"
        BOOKED = "booked", "Booked"
        LOST = "lost", "Lost"
        CLOSED = "closed", "Closed"
        PROCESSING_FAILED = "processing_failed", "Processing Failed"

    conversation = models.ForeignKey(DoubleTickConversation, null=True, blank=True, on_delete=models.CASCADE, related_name="timeline")
    lead = models.ForeignKey(DoubleTickLead, null=True, blank=True, on_delete=models.CASCADE, related_name="timeline")
    assignment = models.ForeignKey(DoubleTickLeadAssignment, null=True, blank=True, on_delete=models.SET_NULL, related_name="timeline")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    device = models.ForeignKey("devices.Device", null=True, blank=True, on_delete=models.SET_NULL)
    branch = models.ForeignKey("branches.Branch", null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=50, choices=Action.choices, db_index=True)
    old_status = models.CharField(max_length=50, blank=True)
    new_status = models.CharField(max_length=50, blank=True)
    note = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "doubletick_activities"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"], name="dt_activity_conv_created_idx"),
            models.Index(fields=["lead", "created_at"], name="dt_activity_lead_created_idx2"),
            models.Index(fields=["action"], name="dt_activity_action_idx2"),
        ]


class DoubleTickLeadActivity(BaseModel, TimeStampedModel):
    """
    Backward-compatible lead activity model from the first implementation.

    New code writes DoubleTickActivity for the complete immutable timeline, but
    this model remains to avoid breaking earlier admin/API serializers.
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

    lead = models.ForeignKey(DoubleTickLead, on_delete=models.CASCADE, related_name="activities")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="doubletick_activities")
    device = models.ForeignKey("devices.Device", null=True, blank=True, on_delete=models.SET_NULL, related_name="doubletick_activities")
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


class DoubleTickWebhookLog(BaseModel, TimeStampedModel):
    """Raw webhook audit log. Every webhook is stored before processing."""

    event_type = models.CharField(max_length=100, blank=True)
    doubletick_event_id = models.CharField(max_length=255, null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    processed = models.BooleanField(default=False, db_index=True)
    error_message = models.TextField(null=True, blank=True)
    lead = models.ForeignKey(DoubleTickLead, null=True, blank=True, on_delete=models.SET_NULL, related_name="webhook_logs")
    conversation = models.ForeignKey(DoubleTickConversation, null=True, blank=True, on_delete=models.SET_NULL, related_name="webhook_logs")
    message = models.ForeignKey(DoubleTickMessage, null=True, blank=True, on_delete=models.SET_NULL, related_name="webhook_logs")

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
