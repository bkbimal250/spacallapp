"""
Django Admin configuration for the Accounts app.

Registers User and EmailOTP models with clean admin interfaces.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models.user import User
from .models.otp import EmailOTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin view for the User model.
    Shows role, branch, and active status clearly.
    """
    list_display = ("email", "phone_number", "full_name", "role", "branch", "is_active", "created_at")
    list_filter = ("role", "is_active", "branch")
    search_fields = ("email", "phone_number", "full_name", "branch__spa_name")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("email", "phone_number", "password")}),
        ("Personal Info", {"fields": ("full_name", "branch", "area_branches")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "created_at")}),
    )
    readonly_fields = ("created_at", "updated_at", "last_login")

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "phone_number", "full_name", "password1", "password2", "role", "branch", "area_branches"),
        }),
    )


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    """Read-only admin view for OTP records — for debugging only."""
    list_display = ("user", "otp", "is_verified", "created_at", "expires_at")
    list_filter = ("is_verified", "created_at")
    search_fields = ("user__email",)
    readonly_fields = ("otp", "created_at", "expires_at")

    def has_add_permission(self, request):
        """OTPs are system-generated — disallow manual creation."""
        return False
