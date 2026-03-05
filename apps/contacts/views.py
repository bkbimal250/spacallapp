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
            
        # For others, maybe restrict or show all? 
        # Usually contacts are shared across branches if they are customers.
        # But if we want to follow the branch pattern:
        if user.role in ['branch_manager', 'regional_manager']:
            # We don't have branch on Contact model yet. 
            # We could filter by contacts created by them or their team.
            pass
            
        return queryset

    def perform_create(self, serializer):
        ContactService.create_contact(serializer.validated_data, self.request.user)

    def perform_update(self, serializer):
        ContactService.update_contact(self.get_object(), serializer.validated_data, self.request.user)

    def perform_destroy(self, instance):
        ContactService.delete_contact(instance)
