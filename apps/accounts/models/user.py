"""
User model for the CallLog SPA Management System.

Roles:
    - super_admin  : Full system access, creates admins.
    - admin        : Creates users and assigns branches. Full data access.
    - spa_manager  : Restricted to their single assigned branch only.

Branch Assignment Rules:
    - A spa_manager is assigned ONE branch at a time (via `branch` FK).
    - Admin can later re-assign the spa_manager to a different branch.
    - An area_manager can be assigned MANY branches via `area_branches`.
"""

import re
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
        spa_manager    → Can only access data for their single assigned branch.
        aerea_manager   → Can access multiple branches assigned via area_branches M2M.
    Branch Assignment:
    - Each spa_manager is assigned to exactly one branch via `branch` FK.
    """

    ROLE_CHOICES = (
        ("super_admin", "Super Admin"),       # Full system access
        ("admin", "Admin"),                   # Manage users, branches, devices
        ("area_manager", "Area Manager"),     # Dashboard access to assigned SPA branches
        ("spa_manager", "SPA Manager"),       # Access limited to one assigned branch
    )

    # Primary key uses UUID for security and scalability
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Authentication field
    email = models.EmailField(unique=True)

    # Optional phone login identifier. Nullable keeps existing email/password
    # and email OTP users working without any migration backfill.
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text="Normalized phone number used for phone + OTP login.",
    )

    # Display name stored as full name; split to first/last in serializer
    full_name = models.CharField(max_length=255)

    # User's system role — controls access level
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, db_index=True)

    # The single active branch a user (spa_manager) is assigned to.
    # Admin assigns this; spa_manager can only see data from this branch.
    branch = models.ForeignKey(
        "branches.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="branch_users",
        help_text="The primary/active branch this user is assigned to.",
    )

    # Separate from BranchGroups: an area manager can be assigned multiple SPA
    # branches and will only see dashboard/call data for those branches.
    area_branches = models.ManyToManyField(
        "branches.Branch",
        blank=True,
        related_name="area_managers",
        help_text="SPA branches this area manager can see.",
    )

    # Firebase Cloud Messaging token for push notifications
    fcm_token = models.TextField(
        null=True, 
        blank=True, 
        help_text="Registration token for Firebase Cloud Messaging for this manager."
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

    @staticmethod
    def normalize_phone_number(phone_number):
        """
        Normalize phone input for login lookup.

        For Indian mobile numbers, both +91XXXXXXXXXX and XXXXXXXXXX are stored
        as the same 10-digit value. Other numeric values are stored digits-only.
        """
        digits = re.sub(r"\D", "", phone_number or "")
        if len(digits) == 12 and digits.startswith("91"):
            return digits[-10:]
        return digits or None

    def save(self, *args, **kwargs):
        if self.phone_number == "":
            self.phone_number = None
        if self.phone_number:
            self.phone_number = self.normalize_phone_number(self.phone_number)
        super().save(*args, **kwargs)

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
    def is_spa_manager(self):
        """Convenience property to check spa_manager role."""
        return self.role == "spa_manager"

    @property
    def is_area_manager(self):
        """Convenience property to check area_manager role."""
        return self.role == "area_manager"
