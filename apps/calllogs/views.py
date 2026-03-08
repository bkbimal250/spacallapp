from rest_framework import viewsets, permissions, views, response, status
from .models import CallLog
from .serializers import CallLogSerializer
from core.authentication import DeviceAuthentication
from core.permissions import IsDevice
from django.utils import timezone
from django.db.models import Count, Q, Sum, Avg
from django.http import HttpResponse
import openpyxl
from openpyxl.styles import Font

class DeviceSyncView(views.APIView):
    authentication_classes = [DeviceAuthentication]
    permission_classes = [IsDevice]

    def post(self, request):
        device = request.auth
        payloads = request.data
        
        if not isinstance(payloads, list):
            return response.Response({"error": "Payload must be a list of call logs"}, status=status.HTTP_400_BAD_REQUEST)

        from apps.contacts.models import Contact

        phone_numbers = {item.get('phone_number') for item in payloads if item.get('phone_number')}
        
        # Match by last 10 digits to ignore country code prefixes (+91, 0, etc)
        contact_query = Q()
        for pn in phone_numbers:
            last_10 = pn[-10:] if len(pn) >= 10 else pn
            contact_query |= Q(phone_number__endswith=last_10)
            
        contacts = Contact.objects.filter(contact_query) if contact_query else []
        contact_map = {}
        for c in contacts:
            c_last_10 = c.phone_number[-10:] if len(c.phone_number) >= 10 else c.phone_number
            contact_map[c_last_10] = c

        logs_to_create = []
        for item in payloads:
            # Normalize sim_slot: Map odd to 1, even to 2
            raw_slot = item.get('sim_slot', 1)
            try:
                raw_slot = int(raw_slot)
                # If slot is 0, map to 1? Or if even map to 2?
                # Android often uses 0 and 1 for slots. 
                # If we want 1 and 2, then 0 -> 1, 1 -> 2.
                # But if user gets 4 and 6, those are even, so map to 2.
                normalized_slot = 2 if raw_slot % 2 == 0 else 1
            except (ValueError, TypeError):
                normalized_slot = 1

            phone_num = item.get('phone_number')
            log_last_10 = phone_num[-10:] if phone_num and len(phone_num) >= 10 else phone_num
            logs_to_create.append(
                CallLog(
                    branch_id=device.branch_id,
                    device_id=device.id,
                    contact=contact_map.get(log_last_10),
                    phone_number=phone_num,
                    call_type=item.get('call_type'),
                    duration=item.get('duration'),
                    sim_slot=normalized_slot,
                    call_time=item.get('call_time'),
                    call_hash=item.get('call_hash')
                )
            )

        # Bulk create ignoring duplicate call_hashes
        CallLog.objects.bulk_create(logs_to_create, ignore_conflicts=True)
        
        # After bulk create, we need to create LeadManagement records for these new logs.
        # Since all calls are leads now, we fetch the newly created logs by their hashes.
        # We only need 'id' and 'contact_id' for LeadManagement creation.
        hashes = [log.call_hash for log in logs_to_create]
        new_logs_data = CallLog.objects.filter(call_hash__in=hashes).values_list('id', 'contact_id')
        
        from apps.leadmanagement.models import LeadManagement
        leads_to_create = [
            LeadManagement(
                calllog_id=log_id,
                contact_id=contact_id,
                branch_id=device.branch_id,
                status='pending'
            )
            for log_id, contact_id in new_logs_data
        ]
        
        if leads_to_create:
            LeadManagement.objects.bulk_create(leads_to_create, ignore_conflicts=True)

        # Update device sync time efficiently
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

    @action(detail=False, methods=['get'])
    def branch_summary(self, request):
        queryset = self.apply_filters(self.get_queryset())
        
        branch_search = request.query_params.get('branch_search', None)
        city = request.query_params.get('city', None)
        status_val = request.query_params.get('status', None)

        if branch_search:
            queryset = queryset.filter(Q(branch__spa_name__icontains=branch_search) | Q(branch__code__icontains=branch_search))
        if city:
            queryset = queryset.filter(branch__city__icontains=city)
        if status_val == 'active':
            queryset = queryset.filter(branch__is_active=True)
        elif status_val == 'inactive':
            queryset = queryset.filter(branch__is_active=False)
            
        summary = queryset.values(
            'branch__id', 
            'branch__spa_name',
            'branch__city',
            'branch__area'
        ).annotate(
            total_calls=Count('id'),
            total_missed=Count('id', filter=Q(call_type='missed')),
            total_outgoing=Count('id', filter=Q(call_type='outgoing')),
            total_incoming=Count('id', filter=Q(call_type='incoming')),
        ).order_by('branch__spa_name')

        page = self.paginate_queryset(summary)
        if page is not None:
            result = []
            for s in page:
                result.append({
                    'branch_id': s['branch__id'],
                    'branch_name': s['branch__spa_name'] or 'Unknown Branch',
                    'city': s['branch__city'] or 'N/A',
                    'area': s['branch__area'] or 'N/A',
                    'total_calls': s['total_calls'],
                    'total_missed': s['total_missed'],
                    'total_outgoing': s['total_outgoing'],
                    'total_incoming': s['total_incoming']
                })
            return self.get_paginated_response(result)
        
        # We process to a clean list of dicts
        result = []
        for s in summary:
            result.append({
                'branch_id': s['branch__id'],
                'branch_name': s['branch__spa_name'] or 'Unknown Branch',
                'city': s['branch__city'] or 'N/A',
                'area': s['branch__area'] or 'N/A',
                'total_calls': s['total_calls'],
                'total_missed': s['total_missed'],
                'total_outgoing': s['total_outgoing'],
                'total_incoming': s['total_incoming']
            })
            
        return response.Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def export_excel(self, request):
        # Apply filters to the queryset and optimize with select_related
        queryset = self.get_queryset().select_related('branch', 'device').iterator()
        
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "Call Logs"
        
        # Headers
        headers = ['Type', 'Number', 'Duration (s)', 'SIM Slot', 'Receiver Number', 'Branch', 'Device ID', 'Time']
        header_font = Font(bold=True)
        
        for col_num, header_title in enumerate(headers, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.value = header_title
            cell.font = header_font
            
        # Data
        for row_num, log in enumerate(queryset, 2):
            worksheet.cell(row=row_num, column=1).value = log.call_type
            worksheet.cell(row=row_num, column=2).value = log.phone_number
            worksheet.cell(row=row_num, column=3).value = log.duration
            worksheet.cell(row=row_num, column=4).value = f"SIM {log.sim_slot}"
            
            # Get receiver number
            receiver = "N/A"
            if log.device:
                if log.sim_slot == 1:
                    receiver = log.device.sim_1_number or "N/A"
                elif log.sim_slot == 2:
                    receiver = log.device.sim_2_number or "N/A"
            
            worksheet.cell(row=row_num, column=5).value = receiver
            worksheet.cell(row=row_num, column=6).value = log.branch.spa_name if log.branch else "N/A"
            worksheet.cell(row=row_num, column=7).value = log.device.device_id if log.device else "N/A"
            
            if log.call_time:
                worksheet.cell(row=row_num, column=8).value = log.call_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                worksheet.cell(row=row_num, column=8).value = "N/A"
            
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        response['Content-Disposition'] = f'attachment; filename="call_logs_{timestamp}.xlsx"'
        workbook.save(response)
        
        return response

    def apply_filters(self, queryset):
        search = self.request.query_params.get('search', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        call_type = self.request.query_params.get('call_type', None)
        branch = self.request.query_params.get('branch', None)
        device = self.request.query_params.get('device', None)

        if call_type:
            queryset = queryset.filter(call_type=call_type)
        if branch:
            if branch == 'null':
                queryset = queryset.filter(branch__isnull=True)
            elif branch.strip() and branch != 'undefined':
                queryset = queryset.filter(branch_id=branch)
        if device:
            if device == 'null':
                queryset = queryset.filter(device__isnull=True)
            elif device.strip() and device != 'undefined':
                queryset = queryset.filter(device__device_id=device)
        if search:
            queryset = queryset.filter(phone_number__icontains=search)
        if start_date:
            queryset = queryset.filter(call_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(call_time__date__lte=end_date)
            
        return queryset

    def get_queryset(self):
        user = self.request.user
        queryset = CallLog.objects.select_related('branch', 'device', 'contact').all().order_by('-call_time')
        
        # Super Admin and Admin can see everything
        if user.role in ['super_admin', 'admin']:
            pass 
        elif user.role == 'branch_manager':
            assigned_branches = user.assigned_branches.all()
            if assigned_branches.exists():
                queryset = queryset.filter(branch__in=assigned_branches)
            elif user.branch:
                queryset = queryset.filter(branch=user.branch)
        elif user.role == 'regional_manager':
            assigned_branches = user.assigned_branches.all()
            if assigned_branches.exists():
                queryset = queryset.filter(branch__in=assigned_branches)
            elif user.branch:
                queryset = queryset.filter(branch=user.branch)
        elif user.role == 'viewer' and user.branch:
            queryset = queryset.filter(branch=user.branch)
            
        if self.action not in ['stats', 'branch_summary']:
            queryset = self.apply_filters(queryset)
        return queryset

