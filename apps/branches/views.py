from django.db import models
from rest_framework import viewsets, permissions
from .models import Branch
from .serializers import BranchSerializer

class BranchViewSet(viewsets.ModelViewSet):
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Branch.objects.all().order_by('spa_name')

        # Restriction for branch/regional managers to their assigned branch(es)
        if user.is_authenticated:
            if user.role in ['super_admin', 'admin', 'viewer']:
                if user.role == 'viewer' and user.branch:
                    queryset = queryset.filter(id=user.branch.id)
                else:
                    pass # See all
            elif user.role == 'branch_manager' and user.branch:
                queryset = queryset.filter(id=user.branch.id)
            elif user.role == 'regional_manager':
                assigned_branches = user.assigned_branches.all()
                if assigned_branches.exists():
                    queryset = queryset.filter(id__in=assigned_branches)
                elif user.branch:
                    queryset = queryset.filter(id=user.branch.id)
        
        search = self.request.query_params.get('search', None)

        city = self.request.query_params.get('city', None)
        status = self.request.query_params.get('status', None)

        if search:
            queryset = queryset.filter(
                models.Q(spa_name__icontains=search) | 
                models.Q(code__icontains=search)
            )
        
        if city:
            queryset = queryset.filter(city__icontains=city)
            
        if status is not None:
            is_active = status.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)

        return queryset
