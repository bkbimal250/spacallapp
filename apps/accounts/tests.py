from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserDeviceSession
from apps.branches.models import Branch
from apps.devices.models import Device


class UserDeviceSessionRefreshTests(APITestCase):
    def test_logout_revokes_login_session_and_immediately_blocks_access_token(self):
        User = get_user_model()
        user = User.objects.create_user(
            email="admin@example.com",
            password="password",
            full_name="Admin User",
            role="admin",
        )

        login_response = self.client.post(
            "/api/v1/auth/login/",
            {"email": user.email, "password": "password", "client": "web"},
            format="json",
        )

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access = login_response.data["access"]
        refresh = login_response.data["refresh"]

        profile_response = self.client.get(
            "/api/v1/auth/profile/",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

        logout_response = self.client.post(
            "/api/v1/auth/logout/",
            {"refresh": refresh},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        blocked_response = self.client.get(
            "/api/v1/auth/profile/",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )
        self.assertEqual(blocked_response.status_code, status.HTTP_401_UNAUTHORIZED)

        session = UserDeviceSession.objects.get(user=user)
        self.assertFalse(session.is_active)
        self.assertEqual(session.status, UserDeviceSession.STATUS_REVOKED)

    def test_token_refresh_updates_access_hash_and_binds_valid_empty_session_device(self):
        User = get_user_model()
        branch = Branch.objects.create(
            spa_name="Navi Mumbai",
            code="NM-01",
            city="Navi Mumbai",
            state="Maharashtra",
            postal_code=400001,
        )
        device = Device.objects.create(
            branch=branch,
            device_id="SPA-070F28-F55345",
            secret_key="device-secret",
            is_registered=True,
        )
        user = User.objects.create_user(
            email="manager@example.com",
            password="password",
            full_name="SPA Manager",
            role="spa_manager",
            branch=branch,
        )
        refresh = RefreshToken.for_user(user)
        session = UserDeviceSession.objects.create(
            user=user,
            device_id="",
            refresh_token_hash=UserDeviceSession.hash_token(str(refresh)),
            access_token_hash="",
            is_active=True,
            status=UserDeviceSession.STATUS_ACTIVE,
            last_login=timezone.now(),
            last_activity=timezone.now(),
        )

        response = self.client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": str(refresh)},
            format="json",
            HTTP_X_DEVICE_ID=device.device_id,
            HTTP_X_DEVICE_SECRET=device.secret_key,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.device_id, device.device_id)
        self.assertEqual(session.access_token_hash, UserDeviceSession.hash_token(response.data["access"]))
