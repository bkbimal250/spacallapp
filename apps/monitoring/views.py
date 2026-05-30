"""
Monitoring views for the CallLog SPA Management System.

Provides device health monitoring and event tracking.

Access Control:
    super_admin / admin → See all device events and health data.
    branch_manager      → See only devices in their assigned branch.
"""

from datetime import timedelta
from django.utils import timezone
from rest_framework import viewsets, permissions, views, response, status
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from rest_framework import serializers
from django_filters.rest_framework import DjangoFilterBackend
from .filters import DeviceEventFilter

from .models import DeviceEvent, DeviceHealth
from .serializers import DeviceEventSerializer, DeviceHealthSerializer
from apps.devices.models import Device
from apps.common.utils import get_branch_filter_ids
from core.authentication import DeviceAuthentication
from core.permissions import IsDevice


class DeviceHeartbeatView(views.APIView):
    """
    Android device heartbeat endpoint.

    Called periodically by the Android app to signal that a device
    is still alive and operational.

    Authenticated via DeviceAuthentication (device_id + HMAC).

    Payload (all fields optional):
        {
          "battery_level": 85,
          "signal_strength": -70,
          "app_version": "1.0.3",
          "storage_used_mb": 512.5
        }
    """
    authentication_classes = [DeviceAuthentication]
    permission_classes = [IsDevice]

    @extend_schema(
        summary="Device Heartbeat",
        description="Updates device heartbeat and health metrics. Triggered periodically by the Android app.",
        request=inline_serializer(
            name="HeartbeatPayload",
            fields={
                "battery_level": serializers.IntegerField(required=False),
                "signal_strength": serializers.IntegerField(required=False),
                "app_version": serializers.CharField(required=False),
                "storage_used_mb": serializers.FloatField(required=False),
            }
        ),
        responses={200: inline_serializer(
            name="HeartbeatResponse",
            fields={"status": serializers.CharField()}
        )}
    )
    def post(self, request):
        device = request.auth
        now = timezone.now()
        health_data = request.data

        # Update device's last heartbeat timestamp
        device.last_heartbeat = now
        device.save(update_fields=["last_heartbeat"])

        # Update or create device health record
        health, _ = DeviceHealth.objects.get_or_create(device=device)
        health.is_online = True
        health.last_heartbeat = now

        # Update health metrics if provided in payload
        if "battery_level" in health_data:
            battery = health_data["battery_level"]
            health.battery_level = battery
            # Trigger alert for low battery (< 15%)
            if battery < 15:
                if not DeviceEvent.objects.filter(device=device, event_type='battery_low', resolved=False).exists():
                    DeviceEvent.objects.create(
                        device=device,
                        event_type='battery_low',
                        description=f"Battery critically low: {battery}%"
                    )
                    from apps.notifications.services import NotificationService
                    NotificationService.send_push(
                        device=device,
                        title="Battery Low",
                        body=f"Device {device.device_id} is at {battery}%. Please connect to power.",
                        notification_type="alert"
                    )

        # SIM Change Detection
        sim_changed = False
        description = "SIM change detected: "
        
        if "sim_1_number" in health_data:
            new_sim1 = health_data["sim_1_number"]
            # Check against Device model (source of truth for registration)
            if device.sim_1_number and new_sim1 and device.sim_1_number != new_sim1:
                sim_changed = True
                description += f"SIM1 ({device.sim_1_number} -> {new_sim1}) "
            health.sim_1_number = new_sim1

        if "sim_2_number" in health_data:
            new_sim2 = health_data["sim_2_number"]
            if device.sim_2_number and new_sim2 and device.sim_2_number != new_sim2:
                sim_changed = True
                description += f"SIM2 ({device.sim_2_number} -> {new_sim2}) "
            health.sim_2_number = new_sim2

        if sim_changed:
            DeviceEvent.objects.create(
                device=device,
                event_type='sim_change',
                description=description
            )
            from apps.notifications.services import NotificationService
            NotificationService.send_push(
                device=device,
                title="SIM Card Changed",
                body=f"Device {device.device_id} reported a SIM change. Please verify security.",
                notification_type="alert"
            )

        if "signal_strength" in health_data:
            health.signal_strength = health_data["signal_strength"]
        if "app_version" in health_data:
            health.app_version = health_data["app_version"]
        if "storage_used_mb" in health_data:
            health.storage_used_mb = health_data["storage_used_mb"]

        health.save()

        # If this device had an active 'offline' alert, resolve it automatically
        DeviceEvent.objects.filter(
            device=device,
            event_type="offline",
            resolved=False,
        ).update(resolved=True, resolved_at=now)

        return response.Response(
            {"status": "heartbeat acknowledged"},
            status=status.HTTP_200_OK
        )


class DeviceEventViewSet(viewsets.ModelViewSet):
    """
    Device Event log viewset (read/filter).

    Events are logged automatically when devices go offline, change SIM cards,
    or encounter errors. This viewset is read-only for branch managers.

    Filters:
        ?event_type=offline|sim_change|error
        ?branch=<uuid>
        ?resolved=true|false
    """
    serializer_class = DeviceEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DeviceEventFilter

    def get_queryset(self):
        """
        Filter queryset based on user role and query parameters.
        """
        if getattr(self, "swagger_fake_view", False):
            return DeviceEvent.objects.none()

        user = self.request.user
        queryset = DeviceEvent.objects.all().select_related('device', 'device__branch')

        # ── Role-based Access Control ──────────────────────────────────────────
        # Use existing utility to get the branch scope
        branch_ids = get_branch_filter_ids(user)

        if branch_ids and branch_ids != ["NONE"]:
            # Restrict to assigned branches
            queryset = queryset.filter(device__branch_id__in=branch_ids)
        elif branch_ids == ["NONE"]:
            # Branch manager with no branch — return empty
            return DeviceEvent.objects.none()

        return queryset.order_by('-created_at')

    @extend_schema(
        summary="List Device Events",
        parameters=[]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Resolve Event",
        description="Mark a single device event as resolved.",
        responses={200: inline_serializer(
            name="ResolveEventResponse",
            fields={"status": serializers.CharField()}
        )}
    )
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark a single event as resolved."""
        event = self.get_object()
        event.resolved = True
        event.resolved_at = timezone.now()
        event.save()
        return response.Response({'status': 'event resolved'})

    @extend_schema(
        summary="Resolve All Events",
        description="Mark all unresolved events in the user's current scope as resolved.",
        responses={200: inline_serializer(
            name="ResolveAllEventsResponse",
            fields={
                "status": serializers.CharField(),
                "count": serializers.IntegerField()
            }
        )}
    )
    @action(detail=False, methods=['post'])
    def resolve_all(self, request):
        """Mark all unresolved events in the user's scope as resolved."""
        queryset = self.filter_queryset(self.get_queryset()).filter(resolved=False)
        count = queryset.update(resolved=True, resolved_at=timezone.now())
        return response.Response({'status': 'all events resolved', 'count': count})

    @extend_schema(
        summary="Delete Selected Events",
        description="Delete selected device events within the user's current scope.",
        request=inline_serializer(
            name="DeleteSelectedEventsRequest",
            fields={"ids": serializers.ListField(child=serializers.UUIDField())}
        ),
        responses={200: inline_serializer(
            name="DeleteSelectedEventsResponse",
            fields={
                "status": serializers.CharField(),
                "count": serializers.IntegerField()
            }
        )}
    )
    @action(detail=False, methods=['post'])
    def delete_selected(self, request):
        """Delete selected events without bypassing branch/user scope."""
        event_ids = request.data.get("ids") or []
        if not event_ids:
            return response.Response(
                {"error": "Select at least one alert to delete."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset().filter(id__in=event_ids)
        count, _ = queryset.delete()
        return response.Response({'status': 'selected events deleted', 'count': count})

    @extend_schema(
        summary="Delete Filtered Events",
        description="Delete all device events matching the current filters within the user's current scope.",
        responses={200: inline_serializer(
            name="DeleteFilteredEventsResponse",
            fields={
                "status": serializers.CharField(),
                "count": serializers.IntegerField()
            }
        )}
    )
    @action(detail=False, methods=['delete'])
    def delete_all(self, request):
        """Delete all filtered events in the user's scope."""
        queryset = self.filter_queryset(self.get_queryset())
        count, _ = queryset.delete()
        return response.Response({'status': 'filtered events deleted', 'count': count})


class DeviceStatusResultView(views.APIView):
    """
    Returns device status summary counts for the monitoring dashboard.

    Response:
        - total_devices      : Count of devices in scope
        - active_devices     : Devices with heartbeat in last 5 minutes
        - online_devices     : Devices marked online in DeviceHealth
        - offline_alerts     : Unresolved 'offline' events
        - sim_change_alerts  : Unresolved 'sim_change' events

    Access:
        super_admin / admin → All devices (or filtered by ?branch=).
        branch_manager      → Only their assigned branch's devices.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Device Monitoring Status Summary",
        description="Returns aggregate health counts for the management dashboard.",
        parameters=[
            OpenApiParameter("branch", type=str, description="Optional branch ID to filter stats (Admin only)")
        ],
        responses={200: inline_serializer(
            name="DeviceStatusSummary",
            fields={
                "total_devices": serializers.IntegerField(),
                "active_devices": serializers.IntegerField(),
                "online_devices": serializers.IntegerField(),
                "offline_alerts": serializers.IntegerField(),
                "sim_change_alerts": serializers.IntegerField(),
            }
        )}
    )
    def get(self, request):
        user = request.user
        branch_id_param = request.query_params.get("branch")

        # Determine branch scope based on user role
        branch_ids = get_branch_filter_ids(user)

        devices_qs = Device.objects.all()
        health_qs = DeviceHealth.objects.all()
        events_qs = DeviceEvent.objects.all()

        if branch_ids and branch_ids != ["NONE"]:
            # Role-restricted user: filter to their branch
            devices_qs = devices_qs.filter(branch_id__in=branch_ids)
            health_qs = health_qs.filter(device__branch_id__in=branch_ids)
            events_qs = events_qs.filter(device__branch_id__in=branch_ids)
        elif branch_ids == ["NONE"]:
            # Branch manager with no branch — return zeros
            return response.Response({
                "total_devices": 0,
                "active_devices": 0,
                "online_devices": 0,
                "offline_alerts": 0,
                "sim_change_alerts": 0,
            })
        elif branch_id_param and branch_id_param.strip() and branch_id_param not in ("undefined", "null"):
            # Admin manually filtering by branch
            devices_qs = devices_qs.filter(branch_id=branch_id_param)
            health_qs = health_qs.filter(device__branch_id=branch_id_param)
            events_qs = events_qs.filter(device__branch_id=branch_id_param)

        # ── Aggregate Counts ───────────────────────────────────────────────────
        # Ensure we only count for non-deleted devices (all_objects used for broad check, then filtered)
        threshold = timezone.now() - timedelta(minutes=5)
        
        # devices_qs and health_qs already exclude soft-deleted items by default due to managers
        total_devices = devices_qs.count()
        active_devices = devices_qs.filter(last_heartbeat__gte=threshold).count()
        
        # Online devices are strictly those that have pinged in last 5 mins
        online_devices = health_qs.filter(
            device__is_deleted=False, 
            last_heartbeat__gte=threshold
        ).count()
        
        offline_alerts = events_qs.filter(
            device__is_deleted=False, 
            event_type="offline", 
            resolved=False
        ).count()
        
        sim_change_alerts = events_qs.filter(
            device__is_deleted=False, 
            event_type="sim_change", 
            resolved=False
        ).count()

        return response.Response({
            "total_devices": total_devices,
            "active_devices": active_devices,
            "online_devices": online_devices,
            "offline_alerts": offline_alerts,
            "sim_change_alerts": sim_change_alerts,
        })
