from django.contrib import admin
from .models import DeviceHealth, DeviceEvent

@admin.register(DeviceHealth)
class DeviceHealthAdmin(admin.ModelAdmin):
    list_display = ("device", "battery_level", "signal_strength", "storage_used_mb", "app_version", "manufacturer", "updated_at")
    list_filter = ("app_version", "manufacturer", "device__branch")
    search_fields = ("device__device_id", "device_model", "manufacturer")
    readonly_fields = [field.name for field in DeviceHealth._meta.fields]
    
    def has_add_permission(self, request):
        return False

@admin.register(DeviceEvent)
class DeviceEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "device", "resolved", "created_at")
    list_filter = ("event_type", "resolved", "created_at", "device__branch")
    search_fields = ("device__device_id", "description")
    ordering = ("-created_at",)
    readonly_fields = ("event_type", "device", "description", "created_at")
