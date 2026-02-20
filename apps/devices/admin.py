from django.contrib import admin
from .models import Device

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("device_id", "branch", "is_active", "is_blocked", "last_heartbeat", "last_sync")
    list_filter = ("is_active", "is_blocked", "branch")
    search_fields = ("device_id", "branch__spa_name", "sim_1_number", "sim_2_number")
    ordering = ("-created_at",)
    readonly_fields = ("secret_key", "last_heartbeat", "last_sync", "created_at")
    
    actions = ["block_devices", "unblock_devices"]

    @admin.action(description="Block selected devices")
    def block_devices(self, request, queryset):
        queryset.update(is_blocked=True)

    @admin.action(description="Unblock selected devices")
    def unblock_devices(self, request, queryset):
        queryset.update(is_blocked=False)
