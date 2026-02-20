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
        user = User.objects.filter(email=email).first()
        if not user:
            raise AuthenticationFailed("User not found")

        otp_code = AuthService.generate_otp()

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
        user = User.objects.filter(email=email).first()
        if not user:
            raise AuthenticationFailed("User not found")

        otp_obj = (
            EmailOTP.objects.filter(user=user, otp=otp, is_verified=False)
            .order_by("-created_at")
            .first()
        )

        if not otp_obj:
            raise AuthenticationFailed("Invalid OTP")

        if otp_obj.is_expired():
            raise AuthenticationFailed("OTP expired")

        otp_obj.is_verified = True
        otp_obj.save()

        return user
