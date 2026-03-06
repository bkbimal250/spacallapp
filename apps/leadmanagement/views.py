from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from .models import LeadManagement
from .serializers import LeadManagementSerializer
from apps.calllogs.models import CallLog
from apps.contacts.models import Contact
from apps.common.permissions import IsSuperAdmin

class LeadManagementViewSet(viewsets.ModelViewSet):
    """
    Lead Management endpoint.
    Filters implicitly to the assigned branch of the logged-in user if they are a Branch Manager.
    """
    serializer_class = LeadManagementSerializer
    def get_permissions(self):
        if self.action in ['destroy', 'bulk_delete']:
            # Only admin and super_admin can delete leads
            return [permissions.IsAuthenticated(), permissions.IsAdminUser() | IsSuperAdmin()]
        
        if self.request.user.is_authenticated and self.request.user.role == 'viewer':
            # Viewer can only see leads
            return [permissions.IsAuthenticated(), permissions.IsAuthenticatedOrReadOnly()]
            
        return [permissions.IsAuthenticated()]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'status': ['exact'],
        'calllog__branch': ['exact', 'isnull'],
        'contact': ['exact'],
        'calllog': ['exact']
    }
    search_fields = ['calllog__phone_number', 'remarks']
    ordering_fields = ['created_at', 'booking_date', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        qs = LeadManagement.objects.select_related('branch', 'contact', 'calllog', 'created_by', 'updated_by').all()
        
        # Super Admin, Admin can see everything
        if user.role in ['super_admin', 'admin']:
            return qs
            
        # Restrict for branch/regional managers to their assigned branches
        if user.role == 'branch_manager' and user.branch:
            qs = qs.filter(branch=user.branch)
        elif user.role == 'regional_manager':
            assigned_branches = user.assigned_branches.all()
            if assigned_branches.exists():
                qs = qs.filter(branch__in=assigned_branches)
            elif user.branch:
                qs = qs.filter(branch=user.branch)
        elif user.role == 'viewer' and user.branch:
            qs = qs.filter(branch=user.branch)
            
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        calllog_id = self.request.data.get('calllog')
        
        extra_data = {}
        
        if calllog_id:
            try:
                cl = CallLog.objects.select_related('contact', 'branch').get(id=calllog_id)
                # Auto-fill contact from calllog
                extra_data['contact'] = cl.contact
            except CallLog.DoesNotExist:
                pass
                
        # If contact passed explicitly, they override calllog defaults
        contact_id = self.request.data.get('contact')
        
        if contact_id:
            extra_data.pop('contact', None) # Use serializer's validated one

        serializer.save(**extra_data)

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'])
    def branch_summary(self, request):
        from django.db.models import Count, Q
        
        qs = self.get_queryset()
            
        branch_search = request.query_params.get('branch_search', None)
        city = request.query_params.get('city', None)
        status_val = request.query_params.get('status', None)

        if branch_search:
            qs = qs.filter(Q(calllog__branch__spa_name__icontains=branch_search) | Q(calllog__branch__code__icontains=branch_search))
        if city:
            qs = qs.filter(calllog__branch__city__icontains=city)
        if status_val == 'active':
            qs = qs.filter(calllog__branch__is_active=True)
        elif status_val == 'inactive':
            qs = qs.filter(calllog__branch__is_active=False)

        summary = qs.values(
            'branch__id', 
            'branch__spa_name',
            'branch__city',
            'branch__area'
        ).annotate(
            total_leads=Count('id'),
            total_pending=Count('id', filter=Q(status='pending')),
            total_ringing=Count('id', filter=Q(status='ringing')),
            total_coming=Count('id', filter=Q(status='coming')),
            total_interested=Count('id', filter=Q(status='interested')),
            total_not_interested=Count('id', filter=Q(status='not_interested')),
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
                    'total_leads': s['total_leads'],
                    'total_pending': s['total_pending'],
                    'total_ringing': s['total_ringing'],
                    'total_coming': s['total_coming'],
                    'total_interested': s['total_interested'],
                    'total_not_interested': s['total_not_interested']
                })
            return self.get_paginated_response(result)
            
        result = []
        for s in summary:
            result.append({
                'branch_id': s['branch__id'],
                'branch_name': s['branch__spa_name'] or 'Unknown Branch',
                'city': s['branch__city'] or 'N/A',
                'area': s['branch__area'] or 'N/A',
                'total_leads': s['total_leads'],
                'total_pending': s['total_pending'],
                'total_ringing': s['total_ringing'],
                'total_coming': s['total_coming'],
                'total_interested': s['total_interested'],
                'total_not_interested': s['total_not_interested']
            })
            
        return Response(result, status=status.HTTP_200_OK)
from core.authentication import DeviceAuthentication
from core.permissions import IsDevice

class LeadsSyncView(viewsets.ViewSet):
    """
    Endpoint for Android app to sync leads.
    """
    authentication_classes = [DeviceAuthentication]
    permission_classes = [IsDevice]

    def create(self, request):
        device = request.auth
        payloads = request.data
        
        if not isinstance(payloads, list):
            return Response({"error": "Payload must be a list of leads"}, status=status.HTTP_400_BAD_REQUEST)

        created_count = 0
        for item in payloads:
            phone_number = item.get('phone_number')
            if not phone_number:
                continue
            
            # Find the call log by hash if provided
            call_hash = item.get('call_hash')
            calllog = None
            if call_hash:
                calllog = CallLog.objects.filter(call_hash=call_hash).first()
            
            if not calllog:
                # Latest call from this number in this branch
                calllog = CallLog.objects.filter(
                    phone_number__endswith=phone_number[-10:], 
                    branch_id=device.branch_id
                ).order_by('-call_time').first()

            if calllog:
                # If we have a calllog, avoid duplicate leads for it
                obj, created = LeadManagement.objects.get_or_create(
                    calllog=calllog,
                    defaults={
                        'contact': calllog.contact,
                        'status': item.get('status', 'pending'),
                        'remarks': item.get('remarks', ''),
                        'booking_date': item.get('booking_date'),
                    }
                )
                if created:
                    created_count += 1
            else:
                # Manual lead from app, try to find contact by phone number
                from apps.contacts.models import Contact
                from django.db.models import Q
                
                last_10 = phone_number[-10:] if len(phone_number) >= 10 else phone_number
                contact = Contact.objects.filter(phone_number__endswith=last_10).first()
                
                LeadManagement.objects.create(
                    branch=device.branch,
                    contact=contact,
                    status=item.get('status', 'pending'),
                    remarks=f"Manual from App: {item.get('remarks', '')}",
                    booking_date=item.get('booking_date'),
                )
                created_count += 1

        return Response({"status": "success", "synced_count": created_count}, status=status.HTTP_201_CREATED)
