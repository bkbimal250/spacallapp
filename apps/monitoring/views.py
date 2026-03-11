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

    def get_queryset(self):
        user = self.request.user
        queryset = DeviceEvent.objects.select_related("device", "device__branch").filter(
            device__is_deleted=False
        ).order_by("-created_at")

        # Apply role-based branch restriction
        branch_ids = get_branch_filter_ids(user)
        if branch_ids and branch_ids != ["NONE"]:
            queryset = queryset.filter(device__branch_id__in=branch_ids)
        elif branch_ids == ["NONE"]:
            return queryset.none()

        # ── Optional Filters ─────────────────────────────────────────────────
        event_type = self.request.query_params.get("event_type", None)
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        branch = self.request.query_params.get("branch", None)
        if branch:
            queryset = queryset.filter(device__branch_id=branch)

        resolved = self.request.query_params.get("resolved", None)
        if resolved is not None:
            queryset = queryset.filter(resolved=resolved.lower() == "true")

        return queryset


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
