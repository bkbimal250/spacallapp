from rest_framework import viewsets, permissions, views, response, status
from .models import DeviceEvent, DeviceHealth
from .serializers import DeviceEventSerializer, DeviceHealthSerializer
from apps.devices.models import Device
from django.utils import timezone
from datetime import timedelta
from core.authentication import DeviceAuthentication
from core.permissions import IsDevice

class DeviceHeartbeatView(views.APIView):
    authentication_classes = [DeviceAuthentication]
    permission_classes = [IsDevice]

    def post(self, request):
        device = request.auth
        now = timezone.now()
        
        # Update device last heartbeat
        device.last_heartbeat = now
        device.save(update_fields=['last_heartbeat'])

        # Update or Create DeviceHealth
        health_data = request.data
        health, created = DeviceHealth.objects.get_or_create(device=device)
        
        health.is_online = True
        health.last_heartbeat = now
        
        if 'battery_level' in health_data:
            health.battery_level = health_data.get('battery_level')
        if 'signal_strength' in health_data:
            health.signal_strength = health_data.get('signal_strength')
        if 'app_version' in health_data:
            health.app_version = health_data.get('app_version')
        if 'storage_used_mb' in health_data:
            health.storage_used_mb = health_data.get('storage_used_mb', 0.0)
            
        health.save()
        
        # If there's an active 'offline' event, resolve it
        DeviceEvent.objects.filter(device=device, event_type='offline', resolved=False).update(
            resolved=True,
            resolved_at=now
        )

        return response.Response({"status": "heartbeat acknowledged"}, status=status.HTTP_200_OK)

class DeviceEventViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = DeviceEvent.objects.all().order_by('-created_at')
        
        event_type = self.request.query_params.get('event_type', None)
        branch = self.request.query_params.get('branch', None)
        resolved = self.request.query_params.get('resolved', None)

        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        if branch:
            queryset = queryset.filter(device__branch_id=branch)
            
        if resolved is not None:
            is_resolved = resolved.lower() == 'true'
            queryset = queryset.filter(resolved=is_resolved)

        return queryset

class DeviceStatusResultView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        total_devices = Device.objects.count()
        threshold = timezone.now() - timedelta(minutes=5)
        
        # Count based on recorded heartbeat time
        active_devices = Device.objects.filter(last_heartbeat__gte=threshold).count()
        
        # Count based on health status flag
        online_devices = DeviceHealth.objects.filter(is_online=True).count()
        
        offline_alerts = DeviceEvent.objects.filter(event_type='offline', resolved=False).count()
        sim_change_alerts = DeviceEvent.objects.filter(event_type='sim_change', resolved=False).count()
        
        return response.Response({
            "total_devices": total_devices,
            "active_devices": active_devices,
            "online_devices": online_devices,
            "offline_alerts": offline_alerts,
            "sim_change_alerts": sim_change_alerts
        })
