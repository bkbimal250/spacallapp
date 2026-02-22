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
        device.last_heartbeat = timezone.now()
        device.save(update_fields=['last_heartbeat'])
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
        active_devices = Device.objects.filter(last_heartbeat__gte=threshold).count()
        offline_alerts = DeviceEvent.objects.filter(event_type='offline', resolved=False).count()
        sim_change_alerts = DeviceEvent.objects.filter(event_type='sim_change', resolved=False).count()
        
        return response.Response({
            "total_devices": total_devices,
            "active_devices": active_devices,
            "offline_alerts": offline_alerts,
            "sim_change_alerts": sim_change_alerts
        })
