from django.conf import settings
from django.db import models

from core.models.base import BaseModel
from core.models.timestamped import TimeStampedModel


class Bot(BaseModel, TimeStampedModel):
    class BotType(models.TextChoices):
        BOOKING = "booking", "Booking"
        JOB = "job", "Job Inquiry"
        SUPPORT = "support", "Support"
        FOLLOW_UP = "follow_up", "Follow Up"
        BRANCH = "branch", "Branch Specific"
        CITY = "city", "City Specific"
        GENERIC = "generic", "Generic"

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    bot_type = models.CharField(max_length=40, choices=BotType.choices, default=BotType.BOOKING)
    description = models.TextField(blank=True)
    default_language = models.CharField(max_length=20, default="en")
    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.IntegerField(default=0)
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "bots"
        ordering = ["priority", "name"]

    def __str__(self):
        return self.name


class BotFlow(BaseModel, TimeStampedModel):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name="flows")
    name = models.CharField(max_length=255)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=False, db_index=True)
    is_published = models.BooleanField(default=False, db_index=True)
    config = models.JSONField(default=dict, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "bot_flows"
        unique_together = ("bot", "version")
        ordering = ["bot__name", "-version"]

    def __str__(self):
        return f"{self.bot} v{self.version}"


class BotNode(BaseModel, TimeStampedModel):
    class NodeType(models.TextChoices):
        START = "start", "Start"
        TEXT_MESSAGE = "text_message", "Text Message"
        TEMPLATE_MESSAGE = "template_message", "Template Message"
        QUESTION = "question", "Question"
        OPTION_BUTTONS = "option_buttons", "Option Buttons"
        INTERACTIVE_LIST = "interactive_list", "Interactive List"
        DYNAMIC_STATE_SELECT = "dynamic_state_select", "Dynamic State Select"
        DYNAMIC_CITY_SELECT = "dynamic_city_select", "Dynamic City Select"
        DYNAMIC_AREA_SELECT = "dynamic_area_select", "Dynamic Area Select"
        DYNAMIC_BRANCH_SELECT = "dynamic_branch_select", "Dynamic Branch Select"
        COLLECT_INPUT = "collect_input", "Collect Input"
        CONDITION = "condition", "Condition"
        MATCH_LOCATION = "match_location", "Match Location"
        ASSIGN_LEAD = "assign_lead", "Assign Lead"
        BROADCAST_LEAD = "broadcast_lead", "Broadcast Lead"
        ROUND_ROBIN_ASSIGN = "round_robin_assign", "Round Robin Assign"
        MANUAL_HANDOVER = "manual_handover", "Manual Handover"
        API_CALL = "api_call", "API Call"
        GOOGLE_SHEET_APPEND = "google_sheet_append", "Google Sheet Append"
        TAG_LEAD = "tag_lead", "Tag Lead"
        UPDATE_LEAD_STATUS = "update_lead_status", "Update Lead Status"
        DELAY = "delay", "Delay"
        END = "end", "End"
        FALLBACK = "fallback", "Fallback"

    flow = models.ForeignKey(BotFlow, on_delete=models.CASCADE, related_name="nodes")
    name = models.CharField(max_length=255)
    node_type = models.CharField(max_length=50, choices=NodeType.choices, db_index=True)
    message_text = models.TextField(blank=True)
    language = models.CharField(max_length=20, blank=True)
    config = models.JSONField(default=dict, blank=True)
    position = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    default_next_node = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="default_previous_nodes")

    class Meta:
        db_table = "bot_nodes"
        ordering = ["flow", "order", "position", "name"]

    def __str__(self):
        return f"{self.flow}: {self.name}"


class BotNodeOption(BaseModel, TimeStampedModel):
    node = models.ForeignKey(BotNode, on_delete=models.CASCADE, related_name="options")
    label = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    payload_id = models.CharField(max_length=255, blank=True, db_index=True)
    next_node = models.ForeignKey(BotNode, null=True, blank=True, on_delete=models.SET_NULL, related_name="incoming_options")
    action = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "bot_node_options"
        ordering = ["node", "order", "label"]

    def __str__(self):
        return self.label


class BotTransition(BaseModel, TimeStampedModel):
    flow = models.ForeignKey(BotFlow, on_delete=models.CASCADE, related_name="transitions")
    from_node = models.ForeignKey(BotNode, on_delete=models.CASCADE, related_name="outgoing_transitions")
    to_node = models.ForeignKey(BotNode, on_delete=models.CASCADE, related_name="incoming_transitions")
    condition = models.JSONField(default=dict, blank=True)
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "bot_transitions"
        ordering = ["priority", "created_at"]


class BotTrigger(BaseModel, TimeStampedModel):
    class TriggerType(models.TextChoices):
        FIRST_INBOUND = "first_inbound", "First Inbound Customer Message"
        KEYWORD = "keyword", "Keyword Match"
        LEAD_CREATED = "lead_created", "Lead Created"
        LOCATION_MISSING = "location_missing", "Location Missing"
        AREA_MATCHED = "area_matched", "Area Matched"
        MANUAL_ACTION = "manual_action", "Manual CRM Action"
        STATUS_CHANGED = "status_changed", "Status Changed"
        FOLLOW_UP_DUE = "follow_up_due", "Follow Up Due"
        ABANDONED = "abandoned", "Abandoned Conversation"
        CAMPAIGN_SOURCE = "campaign_source", "Campaign Source"
        CHANNEL = "channel", "WABA Channel"

    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name="triggers")
    trigger_type = models.CharField(max_length=50, choices=TriggerType.choices, db_index=True)
    keywords = models.JSONField(default=list, blank=True)
    channel = models.ForeignKey("doubletick.DoubleTickChannel", null=True, blank=True, on_delete=models.SET_NULL, related_name="bot_triggers")
    source_campaign = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    branch = models.ForeignKey("branches.Branch", null=True, blank=True, on_delete=models.SET_NULL, related_name="bot_triggers")
    lead_type = models.CharField(max_length=100, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "bot_triggers"
        ordering = ["priority", "created_at"]


class BotSession(BaseModel, TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        HANDED_OVER = "handed_over", "Handed Over"
        EXPIRED = "expired", "Expired"

    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name="sessions")
    flow = models.ForeignKey(BotFlow, null=True, blank=True, on_delete=models.SET_NULL, related_name="sessions")
    current_node = models.ForeignKey(BotNode, null=True, blank=True, on_delete=models.SET_NULL, related_name="sessions")
    customer = models.ForeignKey("doubletick.DoubleTickCustomer", null=True, blank=True, on_delete=models.SET_NULL, related_name="bot_sessions")
    conversation = models.ForeignKey("doubletick.DoubleTickConversation", null=True, blank=True, on_delete=models.SET_NULL, related_name="bot_sessions")
    lead = models.ForeignKey("doubletick.DoubleTickLead", null=True, blank=True, on_delete=models.SET_NULL, related_name="bot_sessions")
    selected_state = models.CharField(max_length=100, blank=True)
    selected_city = models.CharField(max_length=100, blank=True)
    selected_area = models.CharField(max_length=100, blank=True)
    selected_branch = models.ForeignKey("branches.Branch", null=True, blank=True, on_delete=models.SET_NULL, related_name="bot_sessions")
    intent = models.CharField(max_length=100, blank=True, db_index=True)
    language = models.CharField(max_length=20, blank=True)
    variables = models.JSONField(default=dict, blank=True)
    last_customer_message = models.TextField(blank=True)
    last_bot_message = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    retry_count = models.PositiveIntegerField(default=0)
    fallback_count = models.PositiveIntegerField(default=0)
    last_activity_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "bot_sessions"
        indexes = [
            models.Index(fields=["conversation", "status"], name="bot_session_conv_status_idx"),
            models.Index(fields=["lead", "status"], name="bot_session_lead_status_idx"),
        ]


class BotSessionVariable(BaseModel, TimeStampedModel):
    session = models.ForeignKey(BotSession, on_delete=models.CASCADE, related_name="session_variables")
    key = models.CharField(max_length=255)
    value = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "bot_session_variables"
        unique_together = ("session", "key")


class BotExecutionLog(BaseModel):
    class Status(models.TextChoices):
        STARTED = "started", "Started"
        SENT = "sent", "Sent"
        SKIPPED = "skipped", "Skipped"
        FAILED = "failed", "Failed"

    session = models.ForeignKey(BotSession, null=True, blank=True, on_delete=models.SET_NULL, related_name="execution_logs")
    node = models.ForeignKey(BotNode, null=True, blank=True, on_delete=models.SET_NULL, related_name="execution_logs")
    conversation = models.ForeignKey("doubletick.DoubleTickConversation", null=True, blank=True, on_delete=models.SET_NULL, related_name="bot_execution_logs")
    lead = models.ForeignKey("doubletick.DoubleTickLead", null=True, blank=True, on_delete=models.SET_NULL, related_name="bot_execution_logs")
    incoming_message = models.ForeignKey("doubletick.DoubleTickMessage", null=True, blank=True, on_delete=models.SET_NULL, related_name="bot_incoming_logs")
    outbound_message = models.ForeignKey("doubletick.DoubleTickMessage", null=True, blank=True, on_delete=models.SET_NULL, related_name="bot_outbound_logs")
    idempotency_key = models.CharField(max_length=255, blank=True, db_index=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.STARTED, db_index=True)
    event = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bot_execution_logs"
        indexes = [models.Index(fields=["idempotency_key"], name="bot_exec_idem_idx")]


class BotMessageTemplate(BaseModel, TimeStampedModel):
    bot = models.ForeignKey(Bot, null=True, blank=True, on_delete=models.CASCADE, related_name="message_templates")
    name = models.CharField(max_length=255)
    language = models.CharField(max_length=20, default="en")
    template_type = models.CharField(max_length=50, default="text")
    text = models.TextField()
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "bot_message_templates"
        unique_together = ("bot", "name", "language")


class BotDataSource(BaseModel, TimeStampedModel):
    class SourceType(models.TextChoices):
        STATES = "states", "States"
        CITIES = "cities", "Cities"
        AREAS = "areas", "Areas"
        BRANCHES = "branches", "Branches"
        DOUBLETick_AREAS = "doubletick_areas", "DoubleTick Areas"
        CUSTOM = "custom", "Custom"

    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, choices=SourceType.choices)
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "bot_data_sources"


class BotIntegration(BaseModel, TimeStampedModel):
    class IntegrationType(models.TextChoices):
        GOOGLE_SHEETS = "google_sheets", "Google Sheets"
        WEBHOOK_API = "webhook_api", "Webhook API"
        INTERNAL_API = "internal_api", "Internal API"
        DOUBLETICK = "doubletick", "DoubleTick"

    name = models.CharField(max_length=255)
    integration_type = models.CharField(max_length=50, choices=IntegrationType.choices)
    credentials = models.JSONField(default=dict, blank=True)
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "bot_integrations"


class BotApiCallLog(BaseModel):
    integration = models.ForeignKey(BotIntegration, null=True, blank=True, on_delete=models.SET_NULL, related_name="api_call_logs")
    session = models.ForeignKey(BotSession, null=True, blank=True, on_delete=models.SET_NULL, related_name="api_call_logs")
    node = models.ForeignKey(BotNode, null=True, blank=True, on_delete=models.SET_NULL, related_name="api_call_logs")
    url = models.URLField(blank=True)
    method = models.CharField(max_length=20, default="POST")
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    status_code = models.PositiveIntegerField(null=True, blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bot_api_call_logs"


class BotSheetSyncLog(BaseModel):
    integration = models.ForeignKey(BotIntegration, null=True, blank=True, on_delete=models.SET_NULL, related_name="sheet_sync_logs")
    session = models.ForeignKey(BotSession, null=True, blank=True, on_delete=models.SET_NULL, related_name="sheet_sync_logs")
    lead = models.ForeignKey("doubletick.DoubleTickLead", null=True, blank=True, on_delete=models.SET_NULL, related_name="bot_sheet_sync_logs")
    row_payload = models.JSONField(default=dict, blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bot_sheet_sync_logs"


class BotHandoverRule(BaseModel, TimeStampedModel):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name="handover_rules")
    name = models.CharField(max_length=255)
    condition = models.JSONField(default=dict, blank=True)
    assign_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="bot_handover_rules")
    assign_branch = models.ForeignKey("branches.Branch", null=True, blank=True, on_delete=models.SET_NULL, related_name="bot_handover_rules")
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = "bot_handover_rules"
        ordering = ["priority", "name"]


class BotFallbackRule(BaseModel, TimeStampedModel):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name="fallback_rules")
    name = models.CharField(max_length=255)
    retry_number = models.PositiveIntegerField(default=1)
    message_text = models.TextField(blank=True)
    next_node = models.ForeignKey(BotNode, null=True, blank=True, on_delete=models.SET_NULL, related_name="fallback_rules")
    handover_after = models.PositiveIntegerField(default=3)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "bot_fallback_rules"
        ordering = ["retry_number", "name"]
