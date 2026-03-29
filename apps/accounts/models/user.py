"""
User model for the CallLog SPA Management System.

Roles:
    - super_admin  : Full system access, creates admins.
    - admin        : Creates users and assigns branches. Full data access.
    - branch_manager: Restricted to their single assigned branch only.

Branch Assignment Rules:
    - A branch_manager is assigned ONE branch at a time (via `branch` FK).
    - Admin can later re-assign the branch_manager to a different branch.
    - `assigned_branches` M2M is kept for historical tracking / analytics
      of which branches a manager has managed (optional use).
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from core.models.timestamped import TimeStampedModel
from ..managers.user_manager import UserManager


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """
    Custom User Model using Email as the unique identifier (instead of username).

    Three roles are supported:
        super_admin    → God-mode, manages everything.
        admin          → Creates users, assigns branch, manages branches/devices.
        branch_manager → Can only access data for their single assigned branch.
    """

    ROLE_CHOICES = (
        ("super_admin", "Super Admin"),       # Full system access
        ("admin", "Admin"),                   # Manage users, branches, devices
        ("branch_manager", "Branch Manager"), # Access restricted to assigned branch only
    )

    # Primary key uses UUID for security and scalability
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Authentication field
    email = models.EmailField(unique=True)

    # Display name stored as full name; split to first/last in serializer
    full_name = models.CharField(max_length=255)

    # User's system role — controls access level
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, db_index=True)

    # The single active branch a user (branch_manager) is assigned to.
    # Admin assigns this; branch_manager can only see data from this branch.
    branch = models.ForeignKey(
        "branches.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="branch_users",
        help_text="The primary/active branch this user is assigned to.",
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Real-time tracking fields
    last_login_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=False)

    # Optional: store plain text password for admin reference 
    # (Note: Insecure, used as per user requirement)
    password_plain = models.CharField(max_length=255, null=True, blank=True)

    # Django auth settings
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
        ]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.full_name} ({self.email}) — {self.get_role_display()}"

    @property
    def is_super_admin(self):
        """Convenience property to check super_admin role."""
        return self.role == "super_admin"

    @property
    def is_admin(self):
        """Convenience property to check admin role."""
        return self.role == "admin"

    @property
    def is_branch_manager(self):
        """Convenience property to check branch_manager role."""
        return self.role == "branch_manager"
