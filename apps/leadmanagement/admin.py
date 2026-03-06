from django.contrib import admin
from .models import LeadManagement

@admin.register(LeadManagement)
class LeadManagementAdmin(admin.ModelAdmin):
    list_display = ('get_phone_number', 'branch', 'status', 'booking_date', 'created_at')
    list_filter = ('status', 'branch', 'created_at')
    search_fields = ('calllog__phone_number', 'remarks')
    raw_id_fields = ('calllog', 'contact', 'branch')
    
    def get_phone_number(self, obj):
        return obj.calllog.phone_number if obj.calllog else "N/A"
    get_phone_number.short_description = 'Phone Number'
