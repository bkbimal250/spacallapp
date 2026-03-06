from rest_framework import serializers

from .models.user import User
from .models.otp import EmailOTP


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class UserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    branch_name = serializers.CharField(source='branch.spa_name', read_only=True)
    assigned_branches_details = serializers.SerializerMethodField()

    def get_assigned_branches_details(self, obj):
        return [
            {"id": b.id, "spa_name": b.spa_name, "city": b.city} 
            for b in obj.assigned_branches.all()
        ]

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "branch",
            "branch_name",
            "assigned_branches",
            "assigned_branches_details",
            "is_active",
            "created_at",
            "password",
        )
        read_only_fields = ("id", "created_at", "full_name")
        extra_kwargs = {"password": {"write_only": True, "required": False}}

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        full_name = instance.full_name or ""
        parts = full_name.split(" ", 1)
        ret["first_name"] = parts[0]
        ret["last_name"] = parts[1] if len(parts) > 1 else ""
        return ret

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        first_name = validated_data.pop("first_name", "")
        last_name = validated_data.pop("last_name", "")
        
        validated_data["full_name"] = f"{first_name} {last_name}".strip()
        
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        first_name = validated_data.pop("first_name", None)
        last_name = validated_data.pop("last_name", None)
        
        if first_name is not None or last_name is not None:
             # Get current parts
             current_full = (instance.full_name or "").split(" ", 1)
             current_first = current_full[0] if len(current_full) > 0 else ""
             current_last = current_full[1] if len(current_full) > 1 else ""
             
             new_first = first_name if first_name is not None else current_first
             new_last = last_name if last_name is not None else current_last
             validated_data["full_name"] = f"{new_first} {new_last}".strip()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if password:
            instance.set_password(password)
        instance.save()
        return instance

