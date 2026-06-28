"""
Monitoring views for the CallLog SPA Management System.

Provides device health monitoring and event tracking.

Access Control:
    super_admin / admin → See all device events and health data.
    branch_manager      → See only devices in their assigned branch.
"""

from datetime import timedelta
import logging
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import viewsets, permissions, views, response, status
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from rest_framework import serializers
from django_filters.rest_framework import DjangoFilterBackend
from .filters import DeviceEventFilter

from .models import DeviceEvent, DeviceHealth
from .serializers import DeviceEventSerializer, DeviceHealthSerializer
from .services import MonitoringAlertService, offline_threshold
from apps.devices.models import Device
from apps.common.utils import get_branch_filter_ids
from core.authentication import DeviceAuthentication
from core.permissions import IsDevice

logger = logging.getLogger(__name__)


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
                "sim_1_number": serializers.CharField(required=False),
                "sim_2_number": serializers.CharField(required=False),
                "android_id": serializers.CharField(required=False),
                "fcm_token": serializers.CharField(required=False),
                "device_model": serializers.CharField(required=False),
                "manufacturer": serializers.CharField(required=False),
                "device_id": serializers.CharField(required=False),
                "timestamp": serializers.CharField(required=False),
                "device_current_time_ms": serializers.IntegerField(required=False),
                "timezone": serializers.CharField(required=False),
                "pending_call_count": serializers.IntegerField(required=False),
                "last_sync_error": serializers.CharField(required=False),
                "permission_denied": serializers.BooleanField(required=False),
                "permission_name": serializers.CharField(required=False),
                "app_crash": serializers.BooleanField(required=False),
                "crash_message": serializers.CharField(required=False),
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
        was_offline = not device.is_online
        device.last_heartbeat = now
        update_fields = ["last_heartbeat"]
        android_id = (health_data.get("android_id") or "").strip()
        fcm_token = (health_data.get("fcm_token") or "").strip()
        if android_id and device.android_id != android_id:
            if Device.objects.filter(android_id=android_id).exclude(pk=device.pk).exists():
                logger.warning(
                    "Heartbeat android_id ignored because it belongs to another device",
                    extra={"device_id": device.device_id, "android_id": android_id},
                )
            else:
                device.android_id = android_id
                update_fields.append("android_id")
        if fcm_token and device.fcm_token != fcm_token:
            device.fcm_token = fcm_token
            update_fields.append("fcm_token")
        device.save(update_fields=update_fields)

        # Update or create device health record
        health, _ = DeviceHealth.objects.get_or_create(device=device)
        health.is_online = True
        health.last_heartbeat = now

        # Update health metrics if provided in payload
        if "battery_level" in health_data:
            battery = int(health_data["battery_level"])
            health.battery_level = battery
            # Trigger alert for low battery (< 15%)
            if battery < settings.MONITORING_LOW_BATTERY_PERCENT:
                MonitoringAlertService.raise_event(
                    device=device,
                    event_type="battery_low",
                    description=f"Battery critically low: {battery}%",
                )
            elif battery >= settings.MONITORING_BATTERY_RECOVERY_PERCENT:
                MonitoringAlertService.resolve_events(device, ["battery_low"])

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
            MonitoringAlertService.raise_event(
                device=device,
                event_type='sim_change',
                description=description,
                dedupe_active=False,
            )

        if "signal_strength" in health_data:
            signal = int(health_data["signal_strength"])
            health.signal_strength = signal
            if signal <= settings.MONITORING_WEAK_SIGNAL_DBM:
                MonitoringAlertService.raise_event(
                    device=device,
                    event_type="network_weak",
                    description=f"Weak signal reported: {signal} dBm",
                )
            elif signal >= settings.MONITORING_SIGNAL_RECOVERY_DBM:
                MonitoringAlertService.resolve_events(device, ["network_weak"])
        if "app_version" in health_data:
            health.app_version = health_data["app_version"]
        if "device_model" in health_data:
            health.device_model = health_data["device_model"]
        if "manufacturer" in health_data:
            health.manufacturer = health_data["manufacturer"]
        if "pending_call_count" in health_data:
            try:
                health.pending_call_count = max(0, int(health_data["pending_call_count"]))
            except (TypeError, ValueError):
                logger.warning(
                    "Heartbeat ignored invalid pending_call_count",
                    extra={"device_id": device.device_id, "value": health_data.get("pending_call_count")},
                )
        if "last_sync_error" in health_data:
            health.last_sync_error = str(health_data.get("last_sync_error") or "")[:1000]
        if "timestamp" in health_data:
            reported_at = parse_datetime(str(health_data["timestamp"]))
            if reported_at:
                health.device_reported_at = reported_at if timezone.is_aware(reported_at) else timezone.make_aware(reported_at)
        device_time_wrong = None
        device_time_skew_seconds = None
        if "device_current_time_ms" in health_data:
            try:
                device_time_ms = int(health_data["device_current_time_ms"])
                server_time_ms = int(now.timestamp() * 1000)
                device_time_skew_seconds = int((device_time_ms - server_time_ms) / 1000)
                health.device_time_skew_seconds = device_time_skew_seconds
                device_time_wrong = abs(device_time_skew_seconds) > 5 * 60
            except (TypeError, ValueError):
                logger.warning(
                    "Heartbeat ignored invalid device_current_time_ms",
                    extra={"device_id": device.device_id, "value": health_data.get("device_current_time_ms")},
                )
        if "storage_used_mb" in health_data:
            storage_used = float(health_data["storage_used_mb"])
            health.storage_used_mb = storage_used
            if storage_used >= settings.MONITORING_STORAGE_ALERT_MB:
                MonitoringAlertService.raise_event(
                    device=device,
                    event_type="storage_full",
                    description=f"App storage usage reported: {storage_used:.1f} MB",
                )
            else:
                MonitoringAlertService.resolve_events(device, ["storage_full"])

        if health_data.get("permission_denied"):
            permission_name = health_data.get("permission_name") or "Required permission"
            MonitoringAlertService.raise_event(
                device=device,
                event_type="permission_denied",
                description=f"{permission_name} permission denied on device.",
            )

        if health_data.get("app_crash"):
            crash_message = health_data.get("crash_message") or "App crash reported by device."
            MonitoringAlertService.raise_event(
                device=device,
                event_type="app_crash",
                description=crash_message,
                dedupe_active=False,
            )

        health.save()

        # A successful heartbeat proves the app is installed and running again.
        resolved_count = MonitoringAlertService.resolve_events(
            device,
            ["offline", "app_uninstall_suspected"],
        )
        if was_offline or resolved_count:
            MonitoringAlertService.broadcast_device_status(device, "online")
        else:
            MonitoringAlertService.broadcast_device_status(device, "heartbeat")

        try:
            from .compliance import DeviceComplianceService
            if fcm_token:
                DeviceComplianceService.mark_fcm_valid(device)
            if device_time_wrong is True:
                DeviceComplianceService.mark_device_time_wrong(device, device_time_skew_seconds)
            elif device_time_wrong is False:
                DeviceComplianceService.mark_device_time_ok(device)
            DeviceComplianceService.check_device(device)
        except Exception:
            logger.exception("Failed to update device compliance after heartbeat")

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
        MonitoringAlertService._broadcast(event, "resolved")
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
        events = list(queryset)
        count = queryset.update(resolved=True, resolved_at=timezone.now())
        for event in events:
            event.resolved = True
            event.resolved_at = timezone.now()
            MonitoringAlertService._broadcast(event, "resolved")
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
        events = list(queryset)
        count, _ = queryset.delete()
        for event in events:
            MonitoringAlertService._broadcast(event, "deleted")
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
        events = list(queryset)
        count, _ = queryset.delete()
        for event in events:
            MonitoringAlertService._broadcast(event, "deleted")
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
                "uninstall_warning_alerts": serializers.IntegerField(),
                "sim_change_alerts": serializers.IntegerField(),
                "sync_failure_alerts": serializers.IntegerField(),
                "battery_low_alerts": serializers.IntegerField(),
                "storage_alerts": serializers.IntegerField(),
                "network_alerts": serializers.IntegerField(),
                "active_alerts": serializers.IntegerField(),
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
                "uninstall_warning_alerts": 0,
                "sim_change_alerts": 0,
                "sync_failure_alerts": 0,
                "battery_low_alerts": 0,
                "storage_alerts": 0,
                "network_alerts": 0,
                "active_alerts": 0,
            })
        elif branch_id_param and branch_id_param.strip() and branch_id_param not in ("undefined", "null"):
            # Admin manually filtering by branch
            devices_qs = devices_qs.filter(branch_id=branch_id_param)
            health_qs = health_qs.filter(device__branch_id=branch_id_param)
            events_qs = events_qs.filter(device__branch_id=branch_id_param)

        # ── Aggregate Counts ───────────────────────────────────────────────────
        # Ensure we only count for non-deleted devices (all_objects used for broad check, then filtered)
        threshold = offline_threshold()
        
        # devices_qs and health_qs already exclude soft-deleted items by default due to managers
        total_devices = devices_qs.count()
        active_devices = devices_qs.filter(last_heartbeat__gte=threshold).count()
        
        # Online devices are strictly those that have pinged within the monitoring threshold.
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
        uninstall_warning_alerts = events_qs.filter(
            device__is_deleted=False,
            event_type="app_uninstall_suspected",
            resolved=False,
        ).count()
        sync_failure_alerts = events_qs.filter(
            device__is_deleted=False,
            event_type="sync_failure",
            resolved=False,
        ).count()
        battery_low_alerts = events_qs.filter(
            device__is_deleted=False,
            event_type="battery_low",
            resolved=False,
        ).count()
        storage_alerts = events_qs.filter(
            device__is_deleted=False,
            event_type="storage_full",
            resolved=False,
        ).count()
        network_alerts = events_qs.filter(
            device__is_deleted=False,
            event_type="network_weak",
            resolved=False,
        ).count()
        active_alerts = events_qs.filter(
            device__is_deleted=False,
            resolved=False,
        ).count()

        return response.Response({
            "total_devices": total_devices,
            "active_devices": active_devices,
            "online_devices": online_devices,
            "offline_alerts": offline_alerts,
            "uninstall_warning_alerts": uninstall_warning_alerts,
            "sim_change_alerts": sim_change_alerts,
            "sync_failure_alerts": sync_failure_alerts,
            "battery_low_alerts": battery_low_alerts,
            "storage_alerts": storage_alerts,
            "network_alerts": network_alerts,
            "active_alerts": active_alerts,
        })
