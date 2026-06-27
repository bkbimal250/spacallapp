from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.branches.models import Branch, BranchGroups
from apps.devices.models import Device
from apps.monitoring.compliance import DeviceComplianceService
from apps.monitoring.models import DeviceComplianceState, DeviceEvent, DeviceHealth
from apps.monitoring.services import MonitoringAlertService
from apps.monitoring.tasks import check_offline_devices


@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
class MonitoringAlertServiceTests(TestCase):
    def setUp(self):
        self.group = BranchGroups.objects.create(name="Monitoring Group")
        self.branch = Branch.objects.create(
            spa_name="Monitoring Branch",
            code="MON-01",
            city="Pune",
            state="Maharashtra",
            area="Koregaon Park",
            postal_code=411001,
            address="Test address",
            branch_group=self.group,
        )
        self.device = Device.objects.create(
            branch=self.branch,
            device_id="DEV-MON-01",
            phone_name="Reception Phone",
            is_registered=True,
            fcm_token="device-token",
            last_heartbeat=timezone.now(),
        )
        self.manager = User.objects.create_user(
            email="manager@example.com",
            password="testpass123",
            full_name="Branch Manager",
            role="spa_manager",
            branch=self.branch,
            fcm_token="manager-token",
        )

    @patch("apps.notifications.services.NotificationService.send_push", return_value=True)
    def test_raise_event_logs_and_notifies_device_and_manager(self, send_push):
        event = MonitoringAlertService.raise_event(
            device=self.device,
            event_type="battery_low",
            description="Battery critically low: 10%",
        )

        self.assertEqual(event.event_type, "battery_low")
        self.assertFalse(event.resolved)
        self.assertEqual(send_push.call_count, 2)
        notification_types = {call.kwargs["notification_type"] for call in send_push.call_args_list}
        self.assertEqual(notification_types, {"alert"})
        recipients = {call.kwargs["recipient"] for call in send_push.call_args_list}
        self.assertIn(self.device, recipients)
        self.assertIn(self.manager, recipients)

    @patch("apps.notifications.services.NotificationService.send_push", return_value=True)
    def test_raise_event_dedupes_active_alert(self, send_push):
        MonitoringAlertService.raise_event(self.device, "offline", "Device went offline. Last seen: Never")
        MonitoringAlertService.raise_event(self.device, "offline", "Device went offline. Last seen: Never")

        self.assertEqual(DeviceEvent.objects.filter(device=self.device, event_type="offline").count(), 1)
        self.assertEqual(send_push.call_count, 2)  # one event, sent to device and manager

    def test_resolve_events_marks_alert_resolved(self):
        event = DeviceEvent.objects.create(
            device=self.device,
            event_type="network_weak",
            description="Weak signal reported: -110 dBm",
        )

        resolved_count = MonitoringAlertService.resolve_events(self.device, ["network_weak"])

        event.refresh_from_db()
        self.assertEqual(resolved_count, 1)
        self.assertTrue(event.resolved)
        self.assertIsNotNone(event.resolved_at)

    @override_settings(MONITORING_OFFLINE_AFTER_MINUTES=20)
    @patch("apps.notifications.services.NotificationService.send_push", return_value=True)
    def test_check_offline_devices_creates_alert_and_marks_health_offline(self, send_push):
        self.device.last_heartbeat = timezone.now() - timedelta(minutes=25)
        self.device.save(update_fields=["last_heartbeat"])
        DeviceHealth.objects.update_or_create(
            device=self.device,
            defaults={"is_online": True, "last_heartbeat": self.device.last_heartbeat},
        )

        result = check_offline_devices()

        self.assertIn("Affected: 1", result)
        self.assertTrue(DeviceEvent.objects.filter(device=self.device, event_type="offline", resolved=False).exists())
        self.device.health.refresh_from_db()
        self.assertFalse(self.device.health.is_online)
        self.assertEqual(send_push.call_count, 2)

    @override_settings(
        MONITORING_OFFLINE_AFTER_MINUTES=20,
        MONITORING_UNINSTALL_SUSPECT_AFTER_HOURS=24,
    )
    @patch("apps.notifications.services.NotificationService.send_push", return_value=True)
    def test_long_offline_device_creates_possible_uninstall_warning(self, send_push):
        self.device.last_heartbeat = timezone.now() - timedelta(hours=25)
        self.device.save(update_fields=["last_heartbeat"])

        check_offline_devices()

        warning = DeviceEvent.objects.get(
            device=self.device,
            event_type="app_uninstall_suspected",
            resolved=False,
        )
        self.assertIn("Possible reasons", warning.description)
        self.assertIn("app uninstalled", warning.description)


class DeviceHeartbeatClockSkewTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            spa_name="Clock Monitoring Branch",
            code="MON-CLK-01",
            city="Pune",
            state="Maharashtra",
            area="Koregaon Park",
            postal_code=411001,
            address="Test address",
        )
        self.device = Device.objects.create(
            branch=self.branch,
            device_id="DEV-CLOCK-01",
            secret_key="secret-123",
            phone_name="Clock Phone",
            is_registered=True,
            android_id="android-clock-01",
            fcm_token="fcm-token",
        )
        self.client = APIClient()
        self.headers = {
            "HTTP_X_DEVICE_ID": self.device.device_id,
            "HTTP_X_DEVICE_SECRET": self.device.secret_key,
        }

    def test_heartbeat_with_wrong_device_time_marks_device_time_wrong(self):
        future_device_time_ms = int((timezone.now() + timedelta(minutes=12)).timestamp() * 1000)

        response = self.client.post(
            "/api/v1/monitoring/heartbeat/",
            {
                "device_id": self.device.device_id,
                "battery_level": 80,
                "signal_strength": -75,
                "app_version": "1.0.0",
                "storage_used_mb": 20.0,
                "android_id": self.device.android_id,
                "fcm_token": self.device.fcm_token,
                "device_current_time_ms": future_device_time_ms,
                "timezone": "Asia/Kolkata",
            },
            format="json",
            **self.headers,
        )

        self.assertEqual(response.status_code, 200)
        state = DeviceComplianceState.objects.get(device=self.device)
        self.assertTrue(state.device_time_wrong)
        self.assertEqual(state.status, DeviceComplianceService.DEVICE_TIME_WRONG)
        self.assertIn("Automatic Date & Time", state.reason)
        health = DeviceHealth.objects.get(device=self.device)
        self.assertGreater(abs(health.device_time_skew_seconds), 5 * 60)

    @override_settings(
        MONITORING_OFFLINE_AFTER_MINUTES=20,
        MONITORING_UNINSTALL_SUSPECT_AFTER_HOURS=24,
    )
    @patch("apps.notifications.services.NotificationService.send_push", return_value=True)
    def test_short_offline_device_does_not_create_uninstall_warning(self, send_push):
        self.device.last_heartbeat = timezone.now() - timedelta(minutes=25)
        self.device.save(update_fields=["last_heartbeat"])

        check_offline_devices()

        self.assertFalse(
            DeviceEvent.objects.filter(
                device=self.device,
                event_type="app_uninstall_suspected",
            ).exists()
        )
