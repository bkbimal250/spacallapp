import random
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from rest_framework.exceptions import AuthenticationFailed

from ..models.user import User
from ..models.otp import EmailOTP

class AuthService:

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))

    @staticmethod
    def send_otp(email):
        # Normalize and trim email
        email = (email or "").strip().lower()

        user = User.objects.filter(email=email).first()
        if not user:
            # We raise a ValueError here to be handled by the caller as a validation failure
            raise ValueError(f"No active account found with email: {email}")

        otp_code = AuthService.generate_otp()
        
        # Clean up old OTPs for this user
        EmailOTP.objects.filter(user=user).delete()

        EmailOTP.objects.create(
            user=user,
            otp=otp_code,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        send_mail(
            subject="Your Login OTP",
            message=f"Your OTP is {otp_code}",
            from_email=None,
            recipient_list=[email],
        )

    @staticmethod
    def verify_otp(email, otp):
        # Normalize and trim email
        email = (email or "").strip().lower()
        otp = (otp or "").strip()

        user = User.objects.filter(email=email).first()
        if not user:
            raise ValueError(f"No account found with email: {email}")

        otp_obj = (
            EmailOTP.objects.filter(user=user, otp=otp, is_verified=False)
            .order_by("-created_at")
            .first()
        )

        if not otp_obj:
            raise ValueError("Invalid verification code. Please try again.")

        if otp_obj.is_expired():
            raise ValueError("This verification code has expired. Please request a new one.")

        otp_obj.is_verified = True
        otp_obj.save()

        return user
