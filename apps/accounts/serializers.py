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


# ─── Auth Serializers ─────────────────────────────────────────────────────────

class LoginSerializer(serializers.Serializer):
    """Validates email + password for JWT login."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class OTPRequestSerializer(serializers.Serializer):
    """Validates the email address for OTP request."""
    email = serializers.EmailField()


class OTPVerifySerializer(serializers.Serializer):
    """Validates email + OTP code for OTP-based login."""
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


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

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",       # Write-only, virtual
            "last_name",        # Write-only, virtual
            "full_name",        # Read-only, stored
            "role",
            "branch",           # FK (UUID of the assigned branch)
            "branch_name",      # Read-only display name
            "is_active",
            "created_at",
            "password",
        )
        read_only_fields = ("id", "created_at", "full_name")
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
        }

    def to_representation(self, instance):
        """
        Add first_name and last_name to response by splitting full_name.
        """
        ret = super().to_representation(instance)
        full_name = instance.full_name or ""
        parts = full_name.split(" ", 1)
        ret["first_name"] = parts[0]
        ret["last_name"] = parts[1] if len(parts) > 1 else ""
        return ret

    def validate_role(self, value):
        """Ensure only valid roles are assigned."""
        valid_roles = [r[0] for r in User.ROLE_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"Invalid role. Choose from: {', '.join(valid_roles)}"
            )
        return value

    def validate(self, attrs):
        """
        Business rule: branch_manager must have a branch assigned.
        """
        role = attrs.get("role", getattr(self.instance, "role", None))
        branch = attrs.get("branch", getattr(self.instance, "branch", None))

        if role == "branch_manager" and not branch:
            raise serializers.ValidationError(
                {"branch": "A branch must be assigned when creating a Branch Manager."}
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

        # Combine full name
        validated_data["full_name"] = f"{first_name} {last_name}".strip()

        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        """
        Update an existing user.
        Handles partial name updates and optional password change.
        """
        password = validated_data.pop("password", None)
        first_name = validated_data.pop("first_name", None)
        last_name = validated_data.pop("last_name", None)

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

        # Safely update password if provided
        if password:
            instance.set_password(password)

        instance.save()
        return instance
