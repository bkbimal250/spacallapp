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
from rest_framework import viewsets, status, exceptions
from django.contrib.auth import authenticate
from django.utils import timezone
from .services.realtime import RealTimeService
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter
from rest_framework import serializers

from .serializers import (
    LoginSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    PhoneOTPRequestSerializer,
    PhoneOTPVerifySerializer,
    UserSerializer,
    UserLoginHistorySerializer,
)
from .models.user import User
from .models.user_history import UserLoginHistory
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

    serializer_class = LoginSerializer

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: inline_serializer(
                name="LoginResponse",
                fields={
                    "message": serializers.CharField(),
                    "refresh": serializers.CharField(),
                    "access": serializers.CharField(),
                },
            ),
            400: inline_serializer(
                name="LoginError",
                fields={"error": serializers.CharField()},
            ),
        },
        description="Authenticates a user via email and password, returning JWT tokens and profile data."
    )
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

        # Enforce role-based access and branch assignment
        client = serializer.validated_data.get("client", "web")
        try:
            AuthService.validate_user_access(user, client)
        except exceptions.AuthenticationFailed as e:
            return Response({"error": str(e.detail)}, status=status.HTTP_403_FORBIDDEN)

        # Update user status fields
        user.last_login_at = timezone.now()
        user.last_seen_at = timezone.now()
        user.is_online = True
        user.save(update_fields=["last_login_at", "last_seen_at", "is_online"])

        # Create real-time notification
        RealTimeService.broadcast_user_login(user)

        # Record login history
        UserLoginHistory.objects.create(
            user=user,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT"),
        )

        # Generate JWT token pair for the authenticated user
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Login successful",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user, context={"request": request}).data,
        })


class RequestOTPView(APIView):
    """
    Request an OTP to be sent to the given email address.
    Used for passwordless login flow.
    """
    permission_classes = [AllowAny]

    serializer_class = OTPRequestSerializer

    @extend_schema(
        request=OTPRequestSerializer,
        responses={
            200: inline_serializer(
                name="OTPRequestSuccess",
                fields={"message": serializers.CharField()},
            ),
            400: inline_serializer(
                name="OTPRequestError",
                fields={"error": serializers.CharField()},
            ),
        },
        description="Sends a one-time password (OTP) to the provided email address if the user exists."
    )
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            AuthService.send_otp(serializer.validated_data["email"])
            return Response({"message": "OTP sent to your email address."})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Handle any other server-side errors
            return Response({"error": f"Failed to send OTP: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyOTPView(APIView):
    """
    Verify the OTP sent to the email and return JWT tokens if valid.
    """
    permission_classes = [AllowAny]
    serializer_class = OTPVerifySerializer

    @extend_schema(
        request=OTPVerifySerializer,
        responses={
            200: inline_serializer(
                name="OTPVerifyResponse",
                fields={
                    "message": serializers.CharField(),
                    "refresh": serializers.CharField(),
                    "access": serializers.CharField(),
                },
            ),
            400: inline_serializer(
                name="OTPVerifyError",
                fields={"error": serializers.CharField()},
            ),
        },
        description="Verifies the OTP sent to the email and returns JWT tokens if valid."
    )
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = AuthService.verify_otp(
                serializer.validated_data["email"],
                serializer.validated_data["otp"],
            )

            # Enforce role-based access and branch assignment
            client = serializer.validated_data.get("client", "web")
            AuthService.validate_user_access(user, client)

            # Update user status fields
            user.last_login_at = timezone.now()
            user.last_seen_at = timezone.now()
            user.is_online = True
            user.save(update_fields=["last_login_at", "last_seen_at", "is_online"])

            # Create real-time notification
            RealTimeService.broadcast_user_login(user)

            # Record login history
            UserLoginHistory.objects.create(
                user=user,
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT"),
            )

            refresh = RefreshToken.for_user(user)

            return Response({
                "message": "Login successful",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user, context={"request": request}).data,
            })
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


# ─── User Management Views ────────────────────────────────────────────────────

class RequestPhoneOTPView(APIView):
    """
    Request an OTP to be sent to the user's registered phone number.

    This is additive and does not affect email/password or email OTP login.
    """
    permission_classes = [AllowAny]
    serializer_class = PhoneOTPRequestSerializer

    @extend_schema(
        request=PhoneOTPRequestSerializer,
        responses={
            200: inline_serializer(
                name="PhoneOTPRequestSuccess",
                fields={"message": serializers.CharField()},
            ),
            400: inline_serializer(
                name="PhoneOTPRequestError",
                fields={"error": serializers.CharField()},
            ),
        },
        description="Sends a one-time password (OTP) to the registered phone number if the user exists."
    )
    def post(self, request):
        serializer = PhoneOTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            AuthService.send_phone_otp(serializer.validated_data["phone_number"])
            return Response({"message": "OTP sent to your phone number."})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to send OTP: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyPhoneOTPView(APIView):
    """
    Verify the phone OTP and return JWT tokens if valid.
    """
    permission_classes = [AllowAny]
    serializer_class = PhoneOTPVerifySerializer

    @extend_schema(
        request=PhoneOTPVerifySerializer,
        responses={
            200: inline_serializer(
                name="PhoneOTPVerifyResponse",
                fields={
                    "message": serializers.CharField(),
                    "refresh": serializers.CharField(),
                    "access": serializers.CharField(),
                },
            ),
            400: inline_serializer(
                name="PhoneOTPVerifyError",
                fields={"error": serializers.CharField()},
            ),
        },
        description="Verifies the OTP sent to the phone number and returns JWT tokens if valid."
    )
    def post(self, request):
        serializer = PhoneOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = AuthService.verify_phone_otp(
                serializer.validated_data["phone_number"],
                serializer.validated_data["otp"],
            )

            client = serializer.validated_data.get("client", "web")
            AuthService.validate_user_access(user, client)

            user.last_login_at = timezone.now()
            user.last_seen_at = timezone.now()
            user.is_online = True
            user.save(update_fields=["last_login_at", "last_seen_at", "is_online"])

            RealTimeService.broadcast_user_login(user)

            UserLoginHistory.objects.create(
                user=user,
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT"),
            )

            refresh = RefreshToken.for_user(user)

            return Response({
                "message": "Login successful",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user, context={"request": request}).data,
            })
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD for User management.

    Access Rules:
        - Only admin and super_admin can access this viewset.
        - A super_admin can create/manage users of any role.
        - An admin can create spa_manager users and assign branches.
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

    @extend_schema(
        summary="List Users",
        description="List all users with search and filtering for roles and branches.",
        parameters=[
            OpenApiParameter("search", type=str, description="Search by name, email, or phone"),
            OpenApiParameter("role", type=str, description="Filter by user role"),
            OpenApiParameter("branch", type=str, description="Filter by branch UUID"),
            OpenApiParameter("is_active", type=bool, description="Filter by active status"),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Create User")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Retrieve User")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Update User")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partial Update User")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete User")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return all users for admin/super_admin.
        Apply optional search filters.
        """
        queryset = User.objects.select_related("branch").prefetch_related("area_branches").all().order_by("-created_at")

        # Search by email, phone, or full name
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                models.Q(email__icontains=search) |
                models.Q(phone_number__icontains=search) |
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
        role = serializer.validated_data.get("role", "spa_manager")

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


class OnlineUsersView(APIView):
    """
    Get a list of users currently online.
    Filter: is_online = True
    """
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    @extend_schema(
        summary="List Online Users",
        description="Returns a list of users currently marked as online.",
        responses={200: inline_serializer(
            name="OnlineUserListItem",
            many=True,
            fields={
                "id": serializers.UUIDField(),
                "full_name": serializers.CharField(),
                "role": serializers.CharField(),
                "branch": serializers.CharField(),
                "last_login_at": serializers.DateTimeField(),
            }
        )}
    )
    def get(self, request):
        online_users = User.objects.filter(is_online=True).select_related("branch").only(
            "id", "full_name", "role", "branch", "last_login_at"
        )
        
        data = [{
            "id": str(u.id),
            "full_name": u.full_name,
            "role": u.role,
            "branch": u.branch.spa_name if u.branch else "N/A",
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        } for u in online_users]
        
        return Response(data)


class UserLoginHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Viewset to see login history.
    Admin/SuperAdmin can see all logs.
    Branch Manager can only see their own logs (optionally).
    """
    serializer_class = UserLoginHistorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    @extend_schema(
        summary="List Login History",
        parameters=[
            OpenApiParameter("user", type=str, description="Filter history by user UUID")
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Retrieve Login History Item")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        queryset = UserLoginHistory.objects.select_related(
            "user", "user__branch"
        ).all().order_by("-login_at")

        user_id = self.request.query_params.get("user")
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        return queryset

class UpdateProfileView(APIView):
    """
    Allows the authenticated user to update their own profile information.
    Currently used by branch managers on Android to register their FCM token.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Update Current User Profile",
        description="Updates the profile of the currently logged-in user. Used for FCM token registration.",
        request=inline_serializer(
            name="UpdateProfileRequest",
            fields={
                "fcm_token": serializers.CharField(required=False),
                "full_name": serializers.CharField(required=False),
            }
        ),
        responses={200: inline_serializer(
            name="UpdateProfileResponse",
            fields={"status": serializers.CharField()}
        )}
    )
    def patch(self, request):
        user = request.user
        data = request.data

        if "fcm_token" in data:
            user.fcm_token = data["fcm_token"]
        if "full_name" in data:
            user.full_name = data["full_name"]
        
        user.save()
        return Response({"status": "profile updated"})

    @extend_schema(
        summary="Get Current User Profile",
        description="Returns the profile details of the currently authenticated user.",
        responses={200: UserSerializer}
    )
    def get(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data)
