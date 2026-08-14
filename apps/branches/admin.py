from django.contrib import admin
from .models import Branch, BranchOperatingHours

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("spa_name", "code", "city", "state", "is_active", "created_at")
    list_filter = ("is_active", "state", "city")
    search_fields = ("spa_name", "code", "city")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(BranchOperatingHours)
class BranchOperatingHoursAdmin(admin.ModelAdmin):
    list_display = (
        "branch",
        "weekday",
        "is_closed",
        "is_24_hours",
        "opens_at",
        "closes_at",
        "timezone",
        "is_active",
    )
    list_filter = ("weekday", "is_closed", "is_24_hours", "is_active", "timezone")
    search_fields = ("branch__spa_name", "branch__code", "branch__city", "branch__area")
    raw_id_fields = ("branch",)
    ordering = ("branch__spa_name", "weekday")
    readonly_fields = ("created_at", "updated_at")
