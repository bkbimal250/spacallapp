from django.contrib import admin
from .models import CallLog

@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ("call_time", "contact", "phone_number", "call_type", "duration", "branch", "device")
    list_filter = ("call_type", "branch", "call_time")
    search_fields = ("phone_number", "contact__name", "branch__name", "device__device_id")
    date_hierarchy = "call_time"
    readonly_fields = [field.name for field in CallLog._meta.fields]
    
    def has_add_permission(self, request):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False
