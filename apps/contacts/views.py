from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticated
from .models import Contact
from .serializers import ContactSerializer
from .services import ContactService

class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all().order_by('-created_at')
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action == 'destroy':
            from apps.common.permissions import IsSuperAdmin
            return [IsAuthenticated(), IsSuperAdmin()]
        
        if self.request.user.is_authenticated and self.request.user.role == 'viewer':
            return [IsAuthenticated(), permissions.IsAuthenticatedOrReadOnly()]
            
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        queryset = Contact.objects.all().order_by('-created_at')
        
        # Super Admin and Admin can see everything
        if user.role in ['super_admin', 'admin']:
            return queryset
            
        from django.db.models import Q
        # For others, restrict to contacts that have call logs in their assigned branch(es)
        # OR were created by them/their branch members
        if user.role == 'branch_manager' and user.branch:
            queryset = queryset.filter(
                Q(call_logs__branch=user.branch) | 
                Q(created_by__branch=user.branch) |
                Q(created_by=user)
            ).distinct()
        elif user.role == 'regional_manager':
            assigned_branches = user.assigned_branches.all()
            if assigned_branches.exists():
                queryset = queryset.filter(
                    Q(call_logs__branch__in=assigned_branches) |
                    Q(created_by__branch__in=assigned_branches)
                ).distinct()
            elif user.branch:
                queryset = queryset.filter(
                    Q(call_logs__branch=user.branch) |
                    Q(created_by__branch=user.branch)
                ).distinct()
        elif user.role == 'viewer' and user.branch:
            queryset = queryset.filter(
                Q(call_logs__branch=user.branch) |
                Q(created_by__branch=user.branch)
            ).distinct()
            
        return queryset

    def perform_create(self, serializer):
        ContactService.create_contact(serializer.validated_data, self.request.user)

    def perform_update(self, serializer):
        ContactService.update_contact(self.get_object(), serializer.validated_data, self.request.user)

    def perform_destroy(self, instance):
        ContactService.delete_contact(instance)
