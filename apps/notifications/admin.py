from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "device", "user", "notification_type", "is_sent", "created_at")
    list_filter = ("notification_type", "is_sent", "created_at")
    search_fields = ("title", "body", "device__device_id", "user__email", "user__phone_number", "user__full_name")
    readonly_fields = ("created_at", "updated_at", "firebase_message_id", "error_message")
    
    def has_add_permission(self, request):
        return False  # Notifications should be created via services/logic
