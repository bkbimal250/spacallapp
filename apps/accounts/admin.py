from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models.user import User
from .models.otp import EmailOTP

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "full_name", "role", "branch", "is_active", "created_at")
    list_filter = ("role", "is_active", "branch")
    search_fields = ("email", "full_name", "branch__name")
    ordering = ("-created_at",)
    
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("full_name", "branch")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "created_at")}),
    )
    readonly_fields = ("created_at", "updated_at", "last_login")
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "password", "role", "branch"),
        }),
    )

@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "otp", "is_verified", "created_at", "expires_at")
    list_filter = ("is_verified", "created_at")
    search_fields = ("user__email",)
    readonly_fields = ("otp", "created_at", "expires_at")
    
    def has_add_permission(self, request):
        return False
