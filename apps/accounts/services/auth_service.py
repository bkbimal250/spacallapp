import random
import logging
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.utils.module_loading import import_string
from rest_framework.exceptions import AuthenticationFailed

from ..models.user import User
from ..models.otp import EmailOTP


logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))

    @staticmethod
    def _create_otp(user, ttl_minutes=5):
        otp_code = AuthService.generate_otp()

        # Keep one active login OTP per user across email/phone channels.
        EmailOTP.objects.filter(user=user).delete()

        EmailOTP.objects.create(
            user=user,
            otp=otp_code,
            expires_at=timezone.now() + timedelta(minutes=ttl_minutes),
        )
        return otp_code

    @staticmethod
    def send_otp(email):
        # Normalize and trim email
        email = (email or "").strip().lower()

        user = User.objects.filter(email=email).first()
        if not user:
            # We raise a ValueError here to be handled by the caller as a validation failure
            raise ValueError(f"No active account found with email: {email}")

        otp_code = AuthService._create_otp(user, ttl_minutes=5)

        send_mail(
            subject="Your Login OTP",
            message=f"Your OTP is {otp_code}",
            from_email=None,
            recipient_list=[email],
        )

    @staticmethod
    def send_phone_otp(phone_number):
        phone_number = User.normalize_phone_number(phone_number)
        if not phone_number:
            raise ValueError("Phone number is required.")

        user = User.objects.filter(phone_number=phone_number, is_active=True).first()
        if not user:
            raise ValueError("No active account found with this phone number.")

        sender_path = getattr(settings, "PHONE_OTP_SENDER", "")
        if not sender_path:
            logger.error("Phone OTP sender is not configured")
            raise ValueError("Phone OTP sender is not configured.")

        sender = import_string(sender_path)
        otp_code = AuthService._create_otp(user, ttl_minutes=1)

        # The configured sender should use the already approved SMS/OTP template.
        # Signature: sender(phone_number=..., otp=..., user=...)
        sender(phone_number=phone_number, otp=otp_code, user=user)

    @staticmethod
    def verify_phone_otp(phone_number, otp):
        phone_number = User.normalize_phone_number(phone_number)
        otp = (otp or "").strip()

        user = User.objects.filter(phone_number=phone_number, is_active=True).first()
        if not user:
            raise ValueError("No active account found with this phone number.")

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
        otp_obj.save(update_fields=["is_verified"])

        return user

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
        otp_obj.save(update_fields=["is_verified"])

        return user

    @staticmethod
    def validate_user_access(user, client='web'):
        """
        Enforce role-based access control for different clients (Web vs Android).
        
        Rules:
        1. SuperAdmin & Admin: Only allowed on 'web'.
        2. SPA Manager: Only allowed on 'android', and MUST have an assigned branch.
        """
        if not user.is_active:
            raise AuthenticationFailed("Account Deactivated: Your account has been disabled. Please contact system support.")

        if user.role == 'spa_manager':
            if not user.branch:
                raise AuthenticationFailed("Branch Missing: No spa branch has been assigned to your account. Please contact an Administrator.")
            if client == 'web':
                raise AuthenticationFailed("Access Restricted: SPA Manager accounts can only log in via the Mobile App.")
        
        elif user.role in ['admin', 'super_admin']:
            if client == 'android':
                raise AuthenticationFailed("Access Restricted: Administrator accounts can only log in via the Web Dashboard.")

        elif user.role == 'area_manager':
            if client == 'android':
                raise AuthenticationFailed("Access Restricted: Area Manager accounts can only log in via the Web Dashboard.")
            if not user.area_branches.exists():
                raise AuthenticationFailed("Area Missing: No spa branches have been assigned to your area manager account. Please contact an Administrator.")
        
        return True
