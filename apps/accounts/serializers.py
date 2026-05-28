"""
Serializers for the Accounts app.

Handles:
    - Login via email + password.
    - OTP request and verification.
    - User CRUD (admin creates users, assigns branches).
"""

from rest_framework import serializers

from .models.user import User
from .models.otp import EmailOTP
from .models.user_history import UserLoginHistory


# ─── Auth Serializers ─────────────────────────────────────────────────────────

class UserLoginHistorySerializer(serializers.ModelSerializer):
    """Serializer for login audit logs."""
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_role = serializers.CharField(source="user.role", read_only=True)
    branch_name = serializers.CharField(source="user.branch.spa_name", default="N/A", read_only=True)

    class Meta:
        model = UserLoginHistory
        fields = (
            "id",
            "user",
            "user_name",
            "user_email",
            "user_role",
            "branch_name",
            "ip_address",
            "user_agent",
            "login_at",
            "status",
        )
        read_only_fields = ("id", "login_at")


class LoginSerializer(serializers.Serializer):
    """Validates email + password for JWT login."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    client = serializers.CharField(required=False, default="android")


class OTPRequestSerializer(serializers.Serializer):
    """Validates the email address for OTP request."""
    email = serializers.EmailField()


class OTPVerifySerializer(serializers.Serializer):
    """Validates email + OTP code for OTP-based login."""
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    client = serializers.CharField(required=False, default="android")


class PhoneOTPRequestSerializer(serializers.Serializer):
    """Validates the phone number for phone OTP request."""
    phone_number = serializers.CharField(max_length=20)

    def validate_phone_number(self, value):
        normalized = User.normalize_phone_number(value)
        if not normalized:
            raise serializers.ValidationError("phone_number is required.")
        if len(normalized) < 10 or len(normalized) > 15:
            raise serializers.ValidationError("Enter a valid phone number.")
        return normalized


class PhoneOTPVerifySerializer(serializers.Serializer):
    """Validates phone number + OTP code for OTP-based login."""
    phone_number = serializers.CharField(max_length=20)
    otp = serializers.CharField(max_length=6)
    client = serializers.CharField(required=False, default="android")

    def validate_phone_number(self, value):
        normalized = User.normalize_phone_number(value)
        if not normalized:
            raise serializers.ValidationError("phone_number is required.")
        if len(normalized) < 10 or len(normalized) > 15:
            raise serializers.ValidationError("Enter a valid phone number.")
        return normalized


# ─── User Serializer ──────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    """
    Full user serializer for create, update, and list operations.

    Notes:
        - first_name and last_name are virtual write-only fields that get
          combined into full_name on save.
        - branch_name is a read-only display field for the assigned branch.
        - Only admin and super_admin users should be able to create/update users.
    """

    # Virtual fields for UI compatibility (first_name + last_name → full_name)
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)

    # Read-only display fields
    branch_name = serializers.CharField(source="branch.spa_name", read_only=True)
    area_branch_names = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "phone_number",
            "first_name",       # Write-only, virtual
            "last_name",        # Write-only, virtual
            "full_name",        # Read-only, stored
            "role",
            "branch",           # FK (UUID of the assigned branch)
            "branch_name",      # Read-only display name
            "area_branches",    # M2M branch list for area_manager
            "area_branch_names",
            "is_active",
            "created_at",
            "password",
            "password_plain",
        )
        read_only_fields = ("id", "created_at", "full_name")
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
            "area_branches": {"required": False},
        }

    def get_area_branch_names(self, obj):
        return list(obj.area_branches.values_list("spa_name", flat=True))

    def to_representation(self, instance):
        """
        Add first_name and last_name to response by splitting full_name.
        """
        ret = super().to_representation(instance)
        full_name = instance.full_name or ""
        parts = full_name.split(" ", 1)
        ret["first_name"] = parts[0]
        ret["last_name"] = parts[1] if len(parts) > 1 else ""

        # Only super_admin should see the plain password in the response
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            if request.user.role != "super_admin":
                ret.pop("password_plain", None)
        else:
            # For non-authenticated requests (like login where request context might be different)
            # or if context is missing, be safe and pop it.
            ret.pop("password_plain", None)

        return ret

    def validate_role(self, value):
        """Ensure only valid roles are assigned."""
        valid_roles = [r[0] for r in User.ROLE_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"Invalid role. Choose from: {', '.join(valid_roles)}"
            )
        return value

    def validate_phone_number(self, value):
        if value in (None, ""):
            return None

        normalized = User.normalize_phone_number(value)
        if not normalized:
            return None
        if len(normalized) < 10 or len(normalized) > 15:
            raise serializers.ValidationError("Enter a valid phone number.")

        queryset = User.objects.filter(phone_number=normalized)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A user with this phone number already exists.")

        return normalized

    def validate(self, attrs):
        """
        Business rule: spa_manager must have a branch assigned.
        """
        role = attrs.get("role", getattr(self.instance, "role", None))
        branch = attrs.get("branch", getattr(self.instance, "branch", None))
        area_branches = attrs.get("area_branches")
        area_branches_provided = "area_branches" in attrs

        if role == "spa_manager" and not branch:
            raise serializers.ValidationError(
                {"branch": "A branch must be assigned when creating a SPA Manager."}
            )
        if role != "area_manager" and area_branches:
            raise serializers.ValidationError(
                {"area_branches": "SPA branches can only be assigned to an Area Manager."}
            )

        if role == "area_manager":
            has_existing_area_branches = (
                self.instance is not None
                and self.instance.role == "area_manager"
                and self.instance.area_branches.exists()
            )
            if area_branches_provided and not area_branches:
                raise serializers.ValidationError(
                    {"area_branches": "At least one SPA branch must be assigned to an Area Manager."}
                )
            if not area_branches_provided and not has_existing_area_branches:
                raise serializers.ValidationError(
                    {"area_branches": "At least one SPA branch must be assigned when creating an Area Manager."}
                )

        if role != "spa_manager" and branch:
            raise serializers.ValidationError(
                {"branch": "A single branch can only be assigned to a SPA Manager."}
            )
        return attrs

    def create(self, validated_data):
        """
        Create a new user.
        Combines first_name + last_name into full_name.
        Sets password securely via set_password().
        """
        password = validated_data.pop("password", None)
        first_name = validated_data.pop("first_name", "")
        last_name = validated_data.pop("last_name", "")
        area_branches = validated_data.pop("area_branches", None)
        role = validated_data.get("role")

        if role != "spa_manager":
            validated_data["branch"] = None

        # Combine full name
        validated_data["full_name"] = f"{first_name} {last_name}".strip()

        user = User(**validated_data)
        if password:
            user.set_password(password)
            user.password_plain = password  # Store plain text as requested
        else:
            user.set_unusable_password()
        user.save()
        if user.role == "area_manager" and area_branches is not None:
            user.area_branches.set(area_branches)
        else:
            user.area_branches.clear()
        return user

    def update(self, instance, validated_data):
        """
        Update an existing user.
        Handles partial name updates and optional password change.
        """
        password = validated_data.pop("password", None)
        first_name = validated_data.pop("first_name", None)
        last_name = validated_data.pop("last_name", None)
        area_branches = validated_data.pop("area_branches", None)

        # Update full_name only if at least one name part was provided
        if first_name is not None or last_name is not None:
            current_full = (instance.full_name or "").split(" ", 1)
            current_first = current_full[0] if len(current_full) > 0 else ""
            current_last = current_full[1] if len(current_full) > 1 else ""

            new_first = first_name if first_name is not None else current_first
            new_last = last_name if last_name is not None else current_last
            validated_data["full_name"] = f"{new_first} {new_last}".strip()

        # Apply all other field updates
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if instance.role != "spa_manager":
            instance.branch = None

        # Safely update password if provided
        if password:
            instance.set_password(password)
            instance.password_plain = password  # Update plain text as requested

        instance.save()
        if instance.role == "area_manager" and area_branches is not None:
            instance.area_branches.set(area_branches)
        elif instance.role != "area_manager":
            instance.area_branches.clear()
        return instance
