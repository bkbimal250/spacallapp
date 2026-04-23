from django.db.models import Count, Q
from rest_framework import views, viewsets, response, status, permissions, serializers
from django_filters.rest_framework import DjangoFilterBackend
from .filters import NotificationFilter
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from .models import Notification
from .serializers import NotificationSerializer
from .services import NotificationService
from apps.devices.models import Device

from core.permissions import IsAdmin

class AdminSendNotificationView(views.APIView):
    """
    Allow admins to send manual notifications to devices from the dashboard.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    @extend_schema(
        summary="Send Manual Notification",
        description="Allows managers to send push notifications to one or more devices.",
        request=inline_serializer(
            name="SendNotificationRequest",
            fields={
                "device_ids": serializers.ListField(child=serializers.UUIDField(), required=False),
                "title": serializers.CharField(),
                "body": serializers.CharField(),
                "type": serializers.CharField(default="system"),
            }
        ),
        responses={200: inline_serializer(
            name="SendNotificationResponse",
            fields={
                "status": serializers.CharField(),
                "sent_count": serializers.IntegerField(),
                "total_count": serializers.IntegerField(),
            }
        )}
    )
    def post(self, request):
        device_ids = request.data.get("device_ids", [])
        title = request.data.get("title")
        body = request.data.get("body")
        notif_type = request.data.get("type", "system")

        if not title or not body:
            return response.Response({"error": "Title and body required"}, status=status.HTTP_400_BAD_REQUEST)

        # Base active devices queryset
        devices = Device.objects.filter(is_active=True, is_deleted=False)

        # Respect user branch scope
        if hasattr(request.user, 'role') and request.user.role == 'branch_manager' and hasattr(request.user, 'branch'):
            devices = devices.filter(branch=request.user.branch)

        # Handle specific targets if provided
        if device_ids:
            from uuid import UUID
            valid_uuids = []
            for d_id in device_ids:
                if not d_id: continue  # Skip empty strings (common if "All" is selected in some frontends)
                try:
                    # Validate UUID format to prevent 400 error in the filter
                    UUID(str(d_id))
                    valid_uuids.append(d_id)
                except (ValueError, TypeError):
                    continue
            
            if valid_uuids:
                devices = devices.filter(id__in=valid_uuids)
            elif any(d_id == "" for d_id in device_ids):
                # If only "" was provided, we treat it as "all devices in scope"
                pass
            else:
                # If IDs were provided but none were valid, we return empty to be safe
                devices = devices.none()

        success_count = 0
        total_count = devices.count()
        
        for device in devices:
            if NotificationService.send_push(device, title, body, notif_type):
                success_count += 1

        return response.Response({
            "status": "success",
            "sent_count": success_count,
            "total_count": total_count
        })


class NotificationViewSet(viewsets.ModelViewSet):
    """
    View summary and delete history of sent notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = NotificationFilter

    def get_queryset(self):
        """
        Return notifications scoped by user role.
        """
        user = self.request.user
        qs = Notification.objects.select_related("device", "device__branch").all().order_by("-created_at")

        # Optimization: prune columns for the list view
        if self.action == "list":
            qs = qs.only(
                "id", "title", "notification_type", "is_sent", "created_at",
                "device__id", "device__device_id",
                "device__branch__id", "device__branch__spa_name"
            )

        if user.role == "branch_manager":
            # Show notifications for their branch's devices OR notifications sent specifically to them
            qs = qs.filter(
                Q(device__branch=user.branch) | Q(user=user)
            )
        
        # Admin and super_admin see all history

        return qs

    @extend_schema(
        summary="List Notifications",
        parameters=[]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Retrieve Notification")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.delete()
        NotificationService._broadcast_refresh()

    @extend_schema(
        summary="Delete All Notifications",
        description="Permanently deletes all notification logs within the user's branch/global scope.",
        responses={200: inline_serializer(
            name="DeleteAllNotificationsResponse",
            fields={
                "status": serializers.CharField(),
                "count": serializers.IntegerField()
            }
        )}
    )
    @action(detail=False, methods=['delete'])
    def delete_all(self, request):
        """Delete all notification logs in the user's scope."""
        queryset = self.get_queryset()
        count = queryset.count()
        queryset.delete()
        NotificationService._broadcast_refresh()
        return response.Response({'status': 'all notifications deleted', 'count': count})


class NotificationStatsView(views.APIView):
    """
    Returns summary statistics for the notification dashboard.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Notification Statistics",
        description="Returns aggregate health metrics for the notification system (delivery rates).",
        responses={200: inline_serializer(
            name="NotificationStats",
            fields={
                "total_sent": serializers.IntegerField(),
                "delivery_rate": serializers.CharField(),
                "active_devices": serializers.IntegerField(),
            }
        )}
    )
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
