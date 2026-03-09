"""
Views for the Accounts app.

Endpoints:
    POST /auth/login/         → Email + password JWT login.
    POST /auth/otp/request/   → Request OTP via email.
    POST /auth/otp/verify/    → Verify OTP and get JWT tokens.
    GET/POST/PATCH/DELETE /users/ → User management (Admin/SuperAdmin only).

Access Control:
    - Login/OTP endpoints are public (AllowAny).
    - User CRUD is restricted to admin and super_admin roles.
    - A super_admin can see and manage all users.
    - An admin can manage other users but cannot elevate to super_admin.
"""

from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import viewsets, status
from django.contrib.auth import authenticate

from .serializers import (
    LoginSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    UserSerializer,
)
from .models.user import User
from .services.auth_service import AuthService
from apps.common.permissions import IsSuperAdmin, IsAdminOrSuperAdmin


# ─── Auth Views ───────────────────────────────────────────────────────────────

class LoginView(APIView):
    """
    JWT Login using email and password.

    Returns:
        access  : Short-lived JWT access token.
        refresh : Long-lived refresh token for obtaining new access tokens.
        user    : Serialized user data (id, name, role, branch).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Authenticate using Django's built-in authentication backend
        user = authenticate(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        if not user:
            return Response(
                {"error": "Invalid credentials. Please check your email and password."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.is_active:
            return Response(
                {"error": "Your account has been deactivated. Contact your administrator."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate JWT token pair for the authenticated user
        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data
        })


class RequestOTPView(APIView):
    """
    Request an OTP to be sent to the given email address.
    Used for passwordless login flow.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AuthService.send_otp(serializer.validated_data["email"])
        return Response({"message": "OTP sent to your email address."})


class VerifyOTPView(APIView):
    """
    Verify the OTP sent to the email and return JWT tokens if valid.
    """
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
            "user": UserSerializer(user).data
        })


# ─── User Management Views ────────────────────────────────────────────────────

class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD for User management.

    Access Rules:
        - Only admin and super_admin can access this viewset.
        - A super_admin can create/manage users of any role.
        - An admin can create branch_manager users and assign branches.
        - Admin cannot create other admins or super_admins
          (enforced via serializer or can be added here).

    Filters:
        ?search=<name_or_email>   → Search by email or full name.
        ?role=<role>              → Filter by role.
        ?branch=<branch_uuid>     → Filter by assigned branch.
        ?is_active=true|false     → Filter by active status.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def get_queryset(self):
        """
        Return all users for admin/super_admin.
        Apply optional search filters.
        """
        queryset = User.objects.select_related("branch").all().order_by("-created_at")

        # Search by email or full name
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                models.Q(email__icontains=search) |
                models.Q(full_name__icontains=search)
            )

        # Filter by role
        role = self.request.query_params.get("role", None)
        if role:
            queryset = queryset.filter(role=role)

        # Filter by assigned branch
        branch = self.request.query_params.get("branch", None)
        if branch:
            queryset = queryset.filter(branch_id=branch)

        # Filter by active status
        is_active = self.request.query_params.get("is_active", None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        return queryset

    def perform_create(self, serializer):
        """
        Admin creates users and assigns a branch.
        An admin cannot create super_admin — only super_admin can.
        """
        requesting_user = self.request.user
        role = serializer.validated_data.get("role", "branch_manager")

        # Prevent admin from creating super_admin users
        if requesting_user.role == "admin" and role == "super_admin":
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admins cannot create Super Admin users.")

        serializer.save()

    def perform_destroy(self, instance):
        """
        Prevent deletion of super_admin by non-super_admin users.
        """
        requesting_user = self.request.user
        if instance.role == "super_admin" and requesting_user.role != "super_admin":
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only a Super Admin can remove another Super Admin.")

        instance.delete()
