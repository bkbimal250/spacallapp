from django.contrib import admin

from .models import (
    WebsiteFormConfiguration,
    WebsiteFormDailyStats,
    WebsiteLead,
    WebsiteLeadActivity,
)


@admin.register(WebsiteFormConfiguration)
class WebsiteFormConfigurationAdmin(admin.ModelAdmin):
    list_display = ("form_key", "website_name", "website_url", "branch", "is_active", "created_at")
    list_filter = ("is_active", "theme", "branch", "created_at")
    search_fields = ("form_key", "website_name", "website_url", "branch__spa_name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(WebsiteLead)
class WebsiteLeadAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name",
        "phone",
        "address",
        "website_name",
        "branch",
        "status",
        "routing_status",
        "notification_status",
        "created_at",
    )
    list_filter = ("status", "routing_status", "notification_status", "branch", "created_at")
    search_fields = ("customer_name", "phone", "address", "website_name", "form_key")
    readonly_fields = ("created_at", "updated_at")


@admin.register(WebsiteLeadActivity)
class WebsiteLeadActivityAdmin(admin.ModelAdmin):
    list_display = ("action", "lead", "form_configuration", "created_by", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("action", "message", "lead__phone", "form_configuration__form_key")


@admin.register(WebsiteFormDailyStats)
class WebsiteFormDailyStatsAdmin(admin.ModelAdmin):
    list_display = ("date", "branch", "website_name", "form_key", "total_submissions")
    list_filter = ("date", "branch")
    search_fields = ("website_name", "website_url", "form_key", "branch__spa_name")
