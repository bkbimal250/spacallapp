from rest_framework import viewsets, permissions, views, response, status
from .models import CallLog
from .serializers import CallLogSerializer
from core.authentication import DeviceAuthentication
from core.permissions import IsDevice
from django.utils import timezone

class DeviceSyncView(views.APIView):
    authentication_classes = [DeviceAuthentication]
    permission_classes = [IsDevice]

    def post(self, request):
        device = request.auth
        payloads = request.data
        
        if not isinstance(payloads, list):
            return response.Response({"error": "Payload must be a list of call logs"}, status=status.HTTP_400_BAD_REQUEST)

        logs_to_create = []
        for item in payloads:
            logs_to_create.append(
                CallLog(
                    branch_id=device.branch_id,
                    device_id=device.id,
                    phone_number=item.get('phone_number'),
                    call_type=item.get('call_type'),
                    duration=item.get('duration'),
                    sim_slot=item.get('sim_slot'),
                    call_time=item.get('call_time'),
                    call_hash=item.get('call_hash')
                )
            )

        # Bulk create ignoring duplicate call_hashes
        CallLog.objects.bulk_create(logs_to_create, ignore_conflicts=True)
        
        # Update device sync time
        device.last_sync = timezone.now()
        device.save(update_fields=['last_sync'])

        return response.Response({"status": "success", "synced_count": len(logs_to_create)}, status=status.HTTP_201_CREATED)

class CallLogViewSet(viewsets.ModelViewSet):
    serializer_class = CallLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = CallLog.objects.all().order_by('-call_time')
        
        search = self.request.query_params.get('search', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        # Original simple filtersets
        call_type = self.request.query_params.get('call_type', None)
        if call_type:
            queryset = queryset.filter(call_type=call_type)
            
        branch = self.request.query_params.get('branch', None)
        if branch:
            queryset = queryset.filter(branch_id=branch)
            
        device = self.request.query_params.get('device', None)
        if device:
            queryset = queryset.filter(device_id=device)

        if search:
            queryset = queryset.filter(phone_number__icontains=search)
        if start_date:
            queryset = queryset.filter(call_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(call_time__date__lte=end_date)
            
        return queryset
