from django.db.models import Count, Q
from rest_framework import views, viewsets, response, status, permissions
from .models import Notification
from .serializers import NotificationSerializer
from .services import NotificationService
from apps.devices.models import Device

class AdminSendNotificationView(views.APIView):
    """
    Allow admins to send manual notifications to devices from the dashboard.
    """
    permission_classes = [permissions.IsAuthenticated] # Should be IsAdmin

    def post(self, request):
        device_ids = request.data.get("device_ids", []) # List of UUIDs or [] for all
        title = request.data.get("title")
        body = request.data.get("body")
        notif_type = request.data.get("type", "system")

        if not title or not body:
            return response.Response({"error": "Title and body required"}, status=status.HTTP_400_BAD_REQUEST)

        devices = Device.objects.filter(is_active=True)
        if device_ids:
            devices = devices.filter(id__in=device_ids)

        success_count = 0
        for device in devices:
            if NotificationService.send_push(device, title, body, notif_type):
                success_count += 1

        return response.Response({
            "status": "success",
            "sent_count": success_count,
            "total_count": devices.count()
        })


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View history of sent notifications.
    """
    queryset = Notification.objects.all().select_related('device', 'device__branch').order_by('-created_at')
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.role == 'branch_manager':
            queryset = queryset.filter(device__branch=user.branch)
        
        # Filtering
        notif_type = self.request.query_params.get('type')
        if notif_type:
            queryset = queryset.filter(notification_type=notif_type)
            
        return queryset


class NotificationStatsView(views.APIView):
    """
    Returns summary statistics for the notification dashboard.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = self.request.user
        
        # Base queries
        notif_qs = Notification.objects.all()
        device_qs = Device.objects.filter(is_active=True, is_deleted=False)

        if user.role == 'branch_manager':
            notif_qs = notif_qs.filter(device__branch=user.branch)
            device_qs = device_qs.filter(branch=user.branch)

        total_sent = notif_qs.count()
        successful_sent = notif_qs.filter(is_sent=True).count()
        
        delivery_rate = 0
        if total_sent > 0:
            delivery_rate = round((successful_sent / total_sent) * 100, 1)

        active_devices = device_qs.count()

        return response.Response({
            "total_sent": total_sent,
            "delivery_rate": f"{delivery_rate}%",
            "active_devices": active_devices
        })
