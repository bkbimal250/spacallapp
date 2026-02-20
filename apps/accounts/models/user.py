import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from core.models.timestamped import TimeStampedModel
from ..managers.user_manager import UserManager

class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """
    Custom User Model using Email as username
    """

    ROLE_CHOICES = (
        ("super_admin", "Super Admin"),
        ("regional_manager", "Regional Manager"),
        ("branch_manager", "Branch Manager"),
        ("viewer", "Viewer"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)

    role = models.CharField(max_length=30, choices=ROLE_CHOICES)

    branch = models.ForeignKey(
        "branches.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
