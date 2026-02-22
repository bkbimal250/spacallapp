from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .serializers import (
    LoginSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    UserSerializer,
)
from .models.user import User
from rest_framework import viewsets, permissions
from .services.auth_service import AuthService
from apps.common.permissions import IsSuperAdmin



class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        if not user:
            return Response({"error": "Invalid credentials"}, status=400)

        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data
        })



class RequestOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AuthService.send_otp(serializer.validated_data["email"])
        return Response({"message": "OTP sent"})


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = AuthService.verify_otp(
            serializer.validated_data["email"],
            serializer.validated_data["otp"],
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })


from django.db import models

class UserViewSet(viewsets.ModelViewSet):

    """
    CRUD for Users.
    Only Super Admins can see list and create/delete.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]

    def get_queryset(self):
        queryset = User.objects.all().order_by("-created_at")
        
        search = self.request.query_params.get('search', None)
        role = self.request.query_params.get('role', None)
        branch = self.request.query_params.get('branch', None)

        if search:
            queryset = queryset.filter(
                models.Q(email__icontains=search) | 
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search)
            )
        
        if role:
            queryset = queryset.filter(role=role)
            
        if branch:
            queryset = queryset.filter(branch_id=branch)

        return queryset


