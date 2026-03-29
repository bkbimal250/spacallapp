from django.db import models
from django.conf import settings
from core.models.timestamped import TimeStampedModel
import uuid

class UserLoginHistory(TimeStampedModel):
    """
    Historical log of user logins.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="login_histories"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    login_at = models.DateTimeField(auto_now_add=True)
    
    # Store additional context
    status = models.CharField(max_length=20, default="success") # success, failed
    
    class Meta:
        ordering = ["-login_at"]
        verbose_name = "User Login History"
        verbose_name_plural = "User Login Histories"
        indexes = [
            models.Index(fields=["user", "login_at"]),
        ]

    def __str__(self):
        return f"{self.user.full_name} logged in at {self.login_at}"
