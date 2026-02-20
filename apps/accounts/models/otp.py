from django.db import models
from django.conf import settings
from django.utils import timezone

from core.models.timestamped import TimeStampedModel

class EmailOTP(TimeStampedModel):
    """
    Email OTP Model
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="otps",
    )

    otp = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user.email} - {self.otp}"
