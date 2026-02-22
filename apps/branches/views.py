from django.db import models
from rest_framework import viewsets, permissions
from .models import Branch
from .serializers import BranchSerializer

class BranchViewSet(viewsets.ModelViewSet):
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Branch.objects.all().order_by('spa_name')
        
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
