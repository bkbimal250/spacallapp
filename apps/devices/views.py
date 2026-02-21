import secrets
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Device
from .serializers import DeviceSerializer, ClaimRegistrationSerializer

class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all().order_by('-created_at')
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

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

