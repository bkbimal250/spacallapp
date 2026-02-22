import secrets
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Device
from .serializers import DeviceSerializer, ClaimRegistrationSerializer

from django.db import models

class DeviceViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Device.objects.all().order_by('-created_at')
        
        search = self.request.query_params.get('search', None)
        branch = self.request.query_params.get('branch', None)
        is_registered = self.request.query_params.get('is_registered', None)

        if search:
            queryset = queryset.filter(
                models.Q(device_id__icontains=search) | 
                models.Q(registration_token__icontains=search)
            )
        
        if branch:
            queryset = queryset.filter(branch_id=branch)
            
        if is_registered is not None:
            is_reg = is_registered.lower() == 'true'
            queryset = queryset.filter(is_registered=is_reg)

        return queryset

class ClaimRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ClaimRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        token = serializer.validated_data['token']
        
        try:
            device = Device.objects.get(registration_token=token, is_registered=False)
        except Device.DoesNotExist:
            return Response(
                {"error": "Invalid or already used registration token."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate final credentials
        # device_id: e.g. SPA-XXXX-XXXX
        device_id = f"SPA-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}"
        secret_key = secrets.token_hex(32)

        device.device_id = device_id
        device.secret_key = secret_key
        device.is_registered = True
        device.registration_token = None # Clear token after use if desired, or keep track
        device.save()

        return Response({
            "status": "success",
            "device_id": device_id,
            "secret_key": secret_key,
            "branch_name": device.branch.spa_name if device.branch else "Unknown"
        }, status=status.HTTP_200_OK)

