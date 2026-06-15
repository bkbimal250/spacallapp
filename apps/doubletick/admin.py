from django.contrib import admin

from .models import (
    DoubleTickActivity,
    DoubleTickAreaAlias,
    DoubleTickChannel,
    DoubleTickConversation,
    DoubleTickCustomer,
    DoubleTickLead,
    DoubleTickLeadActivity,
    DoubleTickLeadArea,
    DoubleTickLeadAreaBranch,
    DoubleTickLeadAssignment,
    DoubleTickLeadVisibility,
    DoubleTickMessage,
    DoubleTickTeamMemberMapping,
    DoubleTickWebhookLog,
)


@admin.register(DoubleTickChannel)
class DoubleTickChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "waba_number", "state", "city", "branch_group", "is_active")
    search_fields = ("name", "waba_number", "city", "state")
    list_filter = ("is_active", "state", "city")


@admin.register(DoubleTickCustomer)
class DoubleTickCustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "phone_number", "normalized_phone", "dt_customer_id", "channel", "last_seen_at")
    search_fields = ("customer_name", "whatsapp_name", "phone_number", "normalized_phone", "dt_customer_id")
    list_filter = ("channel", "first_seen_at", "last_seen_at")


@admin.register(DoubleTickLeadArea)
class DoubleTickLeadAreaAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "state", "distribution_mode", "is_active", "priority")
    search_fields = ("name", "normalized_name", "city", "state")
    list_filter = ("is_active", "distribution_mode", "city", "state")


@admin.register(DoubleTickAreaAlias)
class DoubleTickAreaAliasAdmin(admin.ModelAdmin):
    list_display = ("alias", "lead_area", "channel", "is_active", "created_from_manual_mapping")
    search_fields = ("alias", "normalized_alias", "lead_area__name")
    list_filter = ("is_active", "created_from_manual_mapping", "channel")


@admin.register(DoubleTickLeadAreaBranch)
class DoubleTickLeadAreaBranchAdmin(admin.ModelAdmin):
    list_display = ("lead_area", "branch", "is_active", "receives_leads", "priority")
    search_fields = ("lead_area__name", "branch__spa_name", "branch__code")
    list_filter = ("is_active", "receives_leads", "lead_area")


@admin.register(DoubleTickConversation)
class DoubleTickConversationAdmin(admin.ModelAdmin):
    list_display = ("customer", "status", "pending_reason", "raw_city", "raw_area", "matched_area", "requires_manual_attention", "last_message_at")
    search_fields = ("customer__phone_number", "customer__customer_name", "raw_city", "raw_area", "raw_service", "dt_conversation_id")
    list_filter = ("status", "pending_reason", "requires_manual_attention", "area_confirmed", "matched_area")
    readonly_fields = ("created_at", "updated_at")


@admin.register(DoubleTickMessage)
class DoubleTickMessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "direction", "origin", "sender_display_name", "status", "text", "message_timestamp")
    search_fields = ("text", "dt_message_id", "message_id", "customer_number", "waba_number", "sender_display_name", "sent_by_raw", "assigned_to_raw")
    list_filter = ("direction", "origin", "status", "message_type")
    readonly_fields = ("created_at", "updated_at")


@admin.register(DoubleTickTeamMemberMapping)
class DoubleTickTeamMemberMappingAdmin(admin.ModelAdmin):
    list_display = ("display_name", "doubletick_phone", "doubletick_user_id", "crm_user", "channel", "is_active")
    search_fields = ("display_name", "doubletick_phone", "doubletick_user_id", "crm_user__full_name", "crm_user__email")
    list_filter = ("is_active", "channel")


@admin.register(DoubleTickLead)
class DoubleTickLeadAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "phone_number", "raw_city", "raw_area", "matched_area", "status", "current_branch", "current_user", "created_at")
    search_fields = ("phone_number", "customer_name", "raw_city", "raw_area", "doubletick_chat_id")
    list_filter = ("status", "matched_area", "current_branch", "current_user", "raw_city", "raw_area", "created_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(DoubleTickLeadVisibility)
class DoubleTickLeadVisibilityAdmin(admin.ModelAdmin):
    list_display = ("lead", "branch", "user", "device", "is_visible", "notification_sent", "notified_at")
    search_fields = ("lead__phone_number", "branch__spa_name", "user__full_name", "device__device_id")
    list_filter = ("is_visible", "notification_sent", "branch")


@admin.register(DoubleTickLeadAssignment)
class DoubleTickLeadAssignmentAdmin(admin.ModelAdmin):
    list_display = ("lead", "attempt_number", "branch", "assigned_user", "status", "is_active", "claimed_at", "released_at")
    search_fields = ("lead__phone_number", "branch__spa_name", "assigned_user__full_name")
    list_filter = ("status", "is_active", "branch", "claimed_at")


@admin.register(DoubleTickActivity)
class DoubleTickActivityAdmin(admin.ModelAdmin):
    list_display = ("action", "conversation", "lead", "user", "branch", "created_at")
    search_fields = ("note", "conversation__customer__phone_number", "lead__phone_number")
    list_filter = ("action", "created_at")


@admin.register(DoubleTickLeadActivity)
class DoubleTickLeadActivityAdmin(admin.ModelAdmin):
    list_display = ("lead", "action", "user", "device", "created_at")
    search_fields = ("lead__phone_number", "lead__customer_name", "note")
    list_filter = ("action", "created_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(DoubleTickWebhookLog)
class DoubleTickWebhookLogAdmin(admin.ModelAdmin):
    list_display = ("event_type", "doubletick_event_id", "processed", "conversation", "lead", "message", "created_at")
    search_fields = ("event_type", "doubletick_event_id", "lead__phone_number", "conversation__customer__phone_number")
    list_filter = ("processed", "event_type", "created_at")
    readonly_fields = ("created_at", "updated_at")
