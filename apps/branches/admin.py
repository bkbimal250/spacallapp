from django.contrib import admin
from .models import Branch

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("spa_name", "code", "city", "state", "is_active", "created_at")
    list_filter = ("is_active", "state", "city")
    search_fields = ("spa_name", "code", "city")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
