from django.contrib import admin

from .models import DoubleTickLead, DoubleTickLeadActivity, DoubleTickWebhookLog


@admin.register(DoubleTickLead)
class DoubleTickLeadAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name",
        "phone_number",
        "city",
        "area",
        "status",
        "assigned_branch",
        "assigned_user",
        "created_at",
    )
    search_fields = (
        "phone_number",
        "normalized_phone",
        "customer_name",
        "city",
        "area",
        "doubletick_chat_id",
    )
    list_filter = ("status", "assigned_branch", "city", "area", "created_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(DoubleTickLeadActivity)
class DoubleTickLeadActivityAdmin(admin.ModelAdmin):
    list_display = ("lead", "action", "user", "device", "created_at")
    search_fields = ("lead__phone_number", "lead__customer_name", "note")
    list_filter = ("action", "created_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(DoubleTickWebhookLog)
class DoubleTickWebhookLogAdmin(admin.ModelAdmin):
    list_display = ("event_type", "doubletick_event_id", "processed", "lead", "created_at")
    search_fields = ("event_type", "doubletick_event_id", "lead__phone_number")
    list_filter = ("processed", "event_type", "created_at")
    readonly_fields = ("created_at", "updated_at")
