from rest_framework import viewsets, permissions
from .models import Branch
from .serializers import BranchSerializer

class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all().order_by('spa_name')
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]
