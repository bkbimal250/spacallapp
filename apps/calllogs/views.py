from rest_framework import viewsets, permissions, views, response, status
from .models import CallLog
from .serializers import CallLogSerializer
from core.authentication import DeviceAuthentication
from core.permissions import IsDevice
from django.utils import timezone
from django.db.models import Count, Q, Sum, Avg

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

from apps.common.permissions import IsSuperAdmin

from rest_framework.decorators import action

class CallLogViewSet(viewsets.ModelViewSet):
    serializer_class = CallLogSerializer
    
    def get_permissions(self):
        if self.action in ['destroy', 'bulk_delete']:
            return [permissions.IsAuthenticated(), IsSuperAdmin()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return response.Response({"error": "No IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count, _ = CallLog.objects.filter(id__in=ids).delete()
        return response.Response({
            "status": "success", 
            "message": f"Successfully deleted {deleted_count} records"
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        queryset = self.apply_filters(self.get_queryset())
        stats = queryset.aggregate(
            total=Count('id'),
            incoming=Count('id', filter=Q(call_type='incoming')),
            outgoing=Count('id', filter=Q(call_type='outgoing')),
            missed=Count('id', filter=Q(call_type='missed')),
            rejected=Count('id', filter=Q(call_type='rejected')),
            total_duration=Sum('duration'),
            avg_duration=Avg('duration')
        )
        return response.Response(stats)

    def apply_filters(self, queryset):
        search = self.request.query_params.get('search', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        call_type = self.request.query_params.get('call_type', None)
        branch = self.request.query_params.get('branch', None)
        device = self.request.query_params.get('device', None)

        if call_type:
            queryset = queryset.filter(call_type=call_type)
        if branch and branch.strip() and branch != 'null' and branch != 'undefined':
            queryset = queryset.filter(branch_id=branch)
        if device and device.strip() and device != 'null' and device != 'undefined':
            queryset = queryset.filter(device_id=device)
        if search:
            queryset = queryset.filter(phone_number__icontains=search)
        if start_date:
            queryset = queryset.filter(call_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(call_time__date__lte=end_date)
            
        return queryset

    def get_queryset(self):
        queryset = CallLog.objects.all().order_by('-call_time')
        if self.action != 'stats':
            queryset = self.apply_filters(queryset)
        return queryset
