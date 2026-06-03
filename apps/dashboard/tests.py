from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.branches.models import Branch
from apps.calllogs.models import CallLog
from apps.devices.models import Device


class DashboardOverviewDeviceFilterTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            email="admin@example.com",
            password="pass1234",
            full_name="Admin User",
        )

        self.branch = Branch.objects.create(
            spa_name="Test Branch",
            code="TB-01",
            city="Pune",
            state="Maharashtra",
            postal_code=411001,
        )

        self.device_a = Device.objects.create(
            branch=self.branch,
            device_id="SPA-A30F18-49031A",
            is_registered=True,
        )
        self.device_b = Device.objects.create(
            branch=self.branch,
            device_id="SPA-B30F18-49031B",
            is_registered=True,
        )

        now = timezone.now()
        CallLog.objects.create(
            branch=self.branch,
            device=self.device_a,
            phone_number="1234567890",
            call_type="incoming",
            duration=30,
            sim_slot=1,
            call_time=now - timedelta(minutes=10),
            call_hash="dashboard_hash_a1",
        )
        CallLog.objects.create(
            branch=self.branch,
            device=self.device_a,
            phone_number="1234567891",
            call_type="missed",
            duration=0,
            sim_slot=1,
            call_time=now - timedelta(minutes=5),
            call_hash="dashboard_hash_a2",
        )
        CallLog.objects.create(
            branch=self.branch,
            device=self.device_b,
            phone_number="1234567892",
            call_type="outgoing",
            duration=45,
            sim_slot=1,
            call_time=now - timedelta(minutes=20),
            call_hash="dashboard_hash_b1",
        )
        CallLog.objects.create(
            branch=self.branch,
            device=self.device_b,
            phone_number="1234567893",
            call_type="rejected",
            duration=0,
            sim_slot=1,
            call_time=now - timedelta(minutes=2),
            call_hash="dashboard_hash_b2",
        )

    def test_dashboard_overview_keeps_branch_level_counts_without_device(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("dashboard-overview"), {"quick_date": "today"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "total": 4,
            "incoming": 1,
            "outgoing": 1,
            "missed": 1,
            "rejected": 1,
        })

    def test_dashboard_overview_filters_counts_by_device_uid(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("dashboard-overview"),
            {"quick_date": "today", "device": self.device_a.device_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "total": 2,
            "incoming": 1,
            "outgoing": 0,
            "missed": 1,
            "rejected": 0,
        })
