from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.branches.models import Branch
from apps.calllogs.models import CallLog
from apps.devices.models import Device
from apps.monitoring.models import APIRequestMetric


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

    def test_android_dashboard_overview_uses_authenticated_device_not_branch_totals(self):
        User = get_user_model()
        manager = User.objects.create_user(
            email="spa-manager@example.com",
            password="pass1234",
            full_name="SPA Manager",
            role="spa_manager",
            branch=self.branch,
        )
        new_device = Device.objects.create(
            branch=self.branch,
            device_id="SPA-070F28-F55345",
            secret_key="new-device-secret",
            is_registered=True,
        )
        token = str(RefreshToken.for_user(manager).access_token)

        response = self.client.get(
            reverse("dashboard-overview"),
            {"quick_date": "today"},
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_DEVICE_ID=new_device.device_id,
            HTTP_X_DEVICE_SECRET=new_device.secret_key,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "total": 0,
            "incoming": 0,
            "outgoing": 0,
            "missed": 0,
            "rejected": 0,
        })

    def test_android_dashboard_overview_does_not_trust_device_query_param(self):
        User = get_user_model()
        manager = User.objects.create_user(
            email="spa-manager-query@example.com",
            password="pass1234",
            full_name="SPA Manager",
            role="spa_manager",
            branch=self.branch,
        )
        self.device_a.secret_key = "device-a-secret"
        self.device_a.save(update_fields=["secret_key"])
        token = str(RefreshToken.for_user(manager).access_token)

        response = self.client.get(
            reverse("dashboard-overview"),
            {"quick_date": "today", "device": self.device_b.device_id},
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_DEVICE_ID=self.device_a.device_id,
            HTTP_X_DEVICE_SECRET=self.device_a.secret_key,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "total": 0,
            "incoming": 0,
            "outgoing": 0,
            "missed": 0,
            "rejected": 0,
        })

    def test_dashboard_summary_returns_only_card_metrics(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("dashboard-summary"), {"quick_date": "today"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total_calls"], 4)
        self.assertEqual(payload["missed_calls"], 1)
        self.assertEqual(payload["today_total_calls"], 4)
        self.assertNotIn("call_volume_trends", payload)
        self.assertNotIn("branch_performance", payload)

    def test_dashboard_stats_keeps_legacy_response_shape(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("dashboard-stats"), {"quick_date": "today"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        expected_keys = {
            "total_calls",
            "active_devices",
            "total_devices",
            "missed_calls",
            "total_leads",
            "total_branches",
            "total_contacts",
            "total_users",
            "total_exports",
            "today_total_calls",
            "today_incoming_calls",
            "today_outgoing_calls",
            "today_missed_calls",
            "avg_duration",
            "call_volume_trends",
            "branch_performance",
        }
        self.assertTrue(expected_keys.issubset(payload.keys()))
        self.assertEqual(payload["total_calls"], 4)
        self.assertEqual(payload["branch_performance"][0]["calls"], 4)

    def test_branch_performance_defaults_to_today_top_20(self):
        now = timezone.now()
        yesterday = now - timedelta(days=1)

        old_branch = Branch.objects.create(
            spa_name="Yesterday Only Branch",
            code="YB-01",
            city="Pune",
            state="Maharashtra",
            postal_code=411001,
        )
        old_device = Device.objects.create(
            branch=old_branch,
            device_id="SPA-YESTERDAY",
            is_registered=True,
        )
        for index in range(3):
            CallLog.objects.create(
                branch=old_branch,
                device=old_device,
                phone_number=f"90000000{index:02d}",
                call_type="incoming",
                duration=30,
                sim_slot=1,
                call_time=yesterday,
                call_hash=f"dashboard_yesterday_{index}",
            )

        for branch_index in range(25):
            branch = Branch.objects.create(
                spa_name=f"Today Branch {branch_index:02d}",
                code=f"TBR-{branch_index:02d}",
                city="Pune",
                state="Maharashtra",
                postal_code=411001,
            )
            device = Device.objects.create(
                branch=branch,
                device_id=f"SPA-TODAY-{branch_index:02d}",
                is_registered=True,
            )
            for call_index in range(branch_index + 1):
                CallLog.objects.create(
                    branch=branch,
                    device=device,
                    phone_number=f"800{branch_index:02d}{call_index:04d}",
                    call_type="incoming",
                    duration=30,
                    sim_slot=1,
                    call_time=now,
                    call_hash=f"dashboard_today_{branch_index}_{call_index}",
                )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("dashboard-branches"))

        self.assertEqual(response.status_code, 200)
        rows = response.json()["branch_performance"]
        self.assertEqual(len(rows), 20)
        self.assertEqual(rows[0]["name"], "Today Branch 24")
        self.assertEqual(rows[0]["calls"], 25)
        self.assertTrue(all(row["calls"] >= 6 for row in rows))

    def test_dashboard_v2_summary_is_additive_route(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("dashboard-v2-summary"), {"quick_date": "today"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total_calls"], 4)
        self.assertNotIn("branch_performance", payload)

    def test_dashboard_request_records_observability_metric(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("dashboard-summary"), {"quick_date": "today"}, HTTP_X_REQUEST_ID="test-request-id")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Request-ID"], "test-request-id")
        metric = APIRequestMetric.objects.filter(request_id="test-request-id").latest("created_at")
        self.assertEqual(metric.path, "/api/v1/dashboard/summary/")
        self.assertEqual(metric.status_code, 200)
        self.assertGreaterEqual(metric.sql_count, 1)
