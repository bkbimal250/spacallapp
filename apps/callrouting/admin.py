from django.contrib import admin

from .models import (
    RoutingAttempt,
    RoutingCandidate,
    RoutingEvent,
    RoutingRequest,
    RoutingRule,
    RoutingWhatsAppMessage,
)


@admin.register(RoutingRule)
class RoutingRuleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "routing_type",
        "enabled",
        "priority",
        "max_recommendations",
        "cooldown_minutes",
        "whatsapp_enabled",
        "dry_run",
    )
    list_filter = ("enabled", "routing_type", "whatsapp_enabled", "dry_run")
    search_fields = ("name", "description", "template_name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("priority", "name")


@admin.register(RoutingRequest)
class RoutingRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "routing_type",
        "source_branch",
        "normalized_phone",
        "routing_rule",
        "rejection_reason",
        "created_at",
        "completed_at",
    )
    list_filter = ("status", "routing_type", "rejection_reason", "source_branch", "routing_rule")
    search_fields = (
        "call_log__phone_number",
        "call_log__call_hash",
        "normalized_phone",
        "source_branch__spa_name",
        "source_branch__code",
    )
    raw_id_fields = ("call_log", "lead", "routing_rule", "source_branch", "source_device", "contact")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "call_log",
            "lead",
            "routing_rule",
            "source_branch",
            "source_device",
            "contact",
        )


@admin.register(RoutingCandidate)
class RoutingCandidateAdmin(admin.ModelAdmin):
    list_display = (
        "routing_request",
        "branch",
        "rank",
        "relevance_score",
        "is_open",
        "is_eligible",
        "is_selected",
        "rejection_reason",
    )
    list_filter = ("is_open", "is_eligible", "is_selected", "rejection_reason")
    search_fields = ("branch__spa_name", "branch__code", "routing_request__normalized_phone")
    raw_id_fields = ("routing_request", "branch")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("routing_request", "rank", "-relevance_score")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("routing_request", "branch")


@admin.register(RoutingAttempt)
class RoutingAttemptAdmin(admin.ModelAdmin):
    list_display = ("routing_request", "attempt_number", "status", "started_at", "completed_at", "error_code")
    list_filter = ("status", "error_code")
    search_fields = ("routing_request__normalized_phone", "error_code", "error_message")
    raw_id_fields = ("routing_request",)
    ordering = ("routing_request", "-attempt_number")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("routing_request")


@admin.register(RoutingEvent)
class RoutingEventAdmin(admin.ModelAdmin):
    list_display = ("routing_request", "event_type", "message", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("routing_request__normalized_phone", "message")
    raw_id_fields = ("routing_request",)
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("routing_request")


@admin.register(RoutingWhatsAppMessage)
class RoutingWhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = (
        "routing_request",
        "recipient_phone",
        "template_name",
        "status",
        "provider_message_id",
        "queued_at",
        "sent_at",
        "delivered_at",
        "read_at",
        "failed_at",
    )
    list_filter = ("status", "template_name", "template_language")
    search_fields = ("recipient_phone", "provider_message_id", "idempotency_key", "routing_request__normalized_phone")
    raw_id_fields = ("routing_request", "doubletick_message")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("routing_request", "doubletick_message")
