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
from apps.accounts.models.user import User
from apps.common.utils import apply_branch_filter

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
                "user_ids": serializers.ListField(child=serializers.UUIDField(), required=False),
                "target_type": serializers.CharField(default="devices"),
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
        user_ids = request.data.get("user_ids", [])
        target_type = request.data.get("target_type", "devices")
        title = request.data.get("title")
        body = request.data.get("body")
        notif_type = request.data.get("type", "system")
        user = request.user

        if not title or not body:
            return response.Response({"error": "Title and body required"}, status=status.HTTP_400_BAD_REQUEST)

        # Base active devices queryset
        devices = Device.objects.filter(is_active=True, is_deleted=False)

        # Respect user branch scope
        devices = apply_branch_filter(devices, "branch_id", user)
        users = User.objects.filter(is_active=True).exclude(fcm_token__isnull=True).exclude(fcm_token="")
        if notif_type == "alert":
            users = users.filter(role="spa_manager")
        users = apply_branch_filter(users, "branch_id", user)

        if target_type == "users":
            devices = devices.none()
        elif target_type == "devices":
            users = users.none()

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

        if user_ids:
            from uuid import UUID
            valid_user_uuids = []
            for u_id in user_ids:
                if not u_id:
                    continue
                try:
                    UUID(str(u_id))
                    valid_user_uuids.append(u_id)
                except (ValueError, TypeError):
                    continue

            if valid_user_uuids:
                users = users.filter(id__in=valid_user_uuids)
            elif any(u_id == "" for u_id in user_ids):
                pass
            else:
                users = users.none()

        success_count = 0
        total_count = devices.count() + users.count()
        
        for device in devices:
            if NotificationService.send_push(device, title, body, notif_type):
                success_count += 1
        for target_user in users:
            if NotificationService.send_push(target_user, title, body, notif_type):
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
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()

        user = self.request.user
        qs = Notification.objects.select_related("device", "device__branch", "user", "user__branch").all().order_by("-created_at")

        # Optimization: prune columns for the list view
        if self.action == "list":
            qs = qs.only(
                "id", "title", "notification_type", "is_sent", "created_at",
                "body", "error_message",
                "device__id", "device__device_id", "device__phone_name",
                "device__branch__id", "device__branch__spa_name",
                "user__id", "user__full_name", "user__email", "user__phone_number",
                "user__branch__id", "user__branch__spa_name",
            )

        if user.role in ["spa_manager", "area_manager"]:
            # Show notifications for their branch's devices OR notifications sent specifically to them
            if user.role == "area_manager":
                branch_qs = apply_branch_filter(qs, "device__branch_id", user)
                qs = branch_qs | qs.filter(user=user)
            elif user.branch:
                qs = qs.filter(
                    Q(device__branch=user.branch) | Q(user=user)
                )
            else:
                return qs.none()
        
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

        if user.role in ['spa_manager', 'area_manager']:
            notif_qs = apply_branch_filter(notif_qs, "device__branch_id", user) | notif_qs.filter(user=user)
            device_qs = apply_branch_filter(device_qs, "branch_id", user)

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
