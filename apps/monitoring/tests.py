from datetime import timedelta
import importlib
from unittest.mock import patch

from django.db import connection
from django.test import TestCase, override_settings
from django.test import TransactionTestCase
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
        self.area_manager = User.objects.create_user(
            email="area-manager@example.com",
            password="testpass123",
            full_name="Area Manager",
            role="area_manager",
            fcm_token="area-manager-token",
        )
        self.area_manager.area_branches.add(self.branch)

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
        self.assertNotIn(self.area_manager, recipients)

    @patch("apps.notifications.services.NotificationService.send_push", return_value=True)
    def test_raise_event_dedupes_active_alert(self, send_push):
        MonitoringAlertService.raise_event(self.device, "offline", "Device went offline. Last seen: Never")
        MonitoringAlertService.raise_event(self.device, "offline", "Device went offline. Last seen: Never")

        self.assertEqual(DeviceEvent.objects.filter(device=self.device, event_type="offline").count(), 1)
        self.assertEqual(send_push.call_count, 2)  # one event, sent to device and manager

    @patch("apps.notifications.services.NotificationService.send_push", return_value=True)
    def test_resolved_event_receiving_new_occurrence_creates_active_event(self, send_push):
        DeviceEvent.objects.create(
            device=self.device,
            event_type="offline",
            description="Old offline alert",
            resolved=True,
            resolved_at=timezone.now(),
        )

        event = MonitoringAlertService.raise_event(self.device, "offline", "Device offline again")

        self.assertFalse(event.resolved)
        self.assertEqual(
            DeviceEvent.objects.filter(device=self.device, event_type="offline", resolved=False).count(),
            1,
        )
        self.assertEqual(
            DeviceEvent.objects.filter(device=self.device, event_type="offline", resolved=True).count(),
            1,
        )

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

    def test_device_compliance_admin_alert_is_marked_as_crm_delivered(self):
        admin = User.objects.create_user(
            email="admin-monitoring@example.com",
            password="testpass123",
            full_name="Admin Monitoring",
            role="admin",
            is_active=True,
        )

        created = DeviceComplianceService.create_crm_alert(
            self.device,
            DeviceComplianceService.SUSPECTED_UNINSTALLED,
            "FCM token invalid",
        )

        self.assertEqual(created, 1)
        notification = admin.notifications.get(title="Device App Alert")
        self.assertTrue(notification.is_sent)


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

    @patch("apps.monitoring.views.MonitoringAlertService.raise_event", side_effect=RuntimeError("alert failure"))
    def test_heartbeat_returns_success_if_alert_processing_fails(self, raise_event):
        response = self.client.post(
            "/api/v1/monitoring/heartbeat/",
            {
                "battery_level": 10,
                "signal_strength": -75,
                "app_version": "1.0.0",
                "storage_used_mb": 20.0,
                "android_id": self.device.android_id,
            },
            format="json",
            **self.headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "heartbeat acknowledged")
        self.device.refresh_from_db()
        self.assertIsNotNone(self.device.last_heartbeat)
        raise_event.assert_called()

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


@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
class DeviceEventDuplicateHandlingTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.branch = Branch.objects.create(
            spa_name="Duplicate Monitoring Branch",
            code="MON-DUP-01",
            city="Pune",
            state="Maharashtra",
            area="Koregaon Park",
            postal_code=411001,
            address="Test address",
        )
        self.device = Device.objects.create(
            branch=self.branch,
            device_id="DEV-DUP-01",
            secret_key="secret-dup",
            phone_name="Duplicate Phone",
            is_registered=True,
            android_id=None,
        )
        self.constraint = next(
            constraint for constraint in DeviceEvent._meta.constraints
            if constraint.name == "uniq_active_device_event_type"
        )

    def _remove_constraint(self):
        with connection.schema_editor() as schema_editor:
            schema_editor.remove_constraint(DeviceEvent, self.constraint)

    def _add_constraint(self):
        with connection.schema_editor() as schema_editor:
            schema_editor.add_constraint(DeviceEvent, self.constraint)

    def test_no_matching_device_event_creates_new_event(self):
        event = MonitoringAlertService.raise_event(self.device, "battery_low", "Battery low", notify=False)

        self.assertFalse(event.resolved)
        self.assertEqual(DeviceEvent.objects.filter(device=self.device, event_type="battery_low").count(), 1)

    def test_exactly_one_matching_event_updates_description(self):
        event = DeviceEvent.objects.create(
            device=self.device,
            event_type="sync_failure",
            description="Old description",
        )

        updated = MonitoringAlertService.raise_event(self.device, "sync_failure", "New description", notify=False)

        self.assertEqual(updated.id, event.id)
        updated.refresh_from_db()
        self.assertEqual(updated.description, "New description")
        self.assertEqual(DeviceEvent.objects.filter(device=self.device, event_type="sync_failure", resolved=False).count(), 1)

    def test_two_duplicate_matching_events_are_merged(self):
        self._remove_constraint()
        try:
            first = DeviceEvent.objects.create(device=self.device, event_type="offline", description="First")
            second = DeviceEvent.objects.create(device=self.device, event_type="offline", description="Second")

            event = MonitoringAlertService.raise_event(self.device, "offline", "Latest", notify=False)

            self.assertEqual(event.id, first.id)
            self.assertFalse(DeviceEvent.objects.filter(id=second.id).exists())
            self.assertEqual(DeviceEvent.objects.filter(device=self.device, event_type="offline", resolved=False).count(), 1)
            event.refresh_from_db()
            self.assertEqual(event.description, "Latest")
        finally:
            DeviceEvent.objects.filter(device=self.device, event_type="offline").exclude(id=first.id).delete()
            self._add_constraint()

    def test_more_than_two_duplicate_matching_events_are_merged(self):
        self._remove_constraint()
        try:
            first = DeviceEvent.objects.create(device=self.device, event_type="network_weak", description="First")
            duplicate_ids = [
                DeviceEvent.objects.create(device=self.device, event_type="network_weak", description=f"Duplicate {index}").id
                for index in range(3)
            ]

            event = MonitoringAlertService.raise_event(self.device, "network_weak", "Weak now", notify=False)

            self.assertEqual(event.id, first.id)
            self.assertFalse(DeviceEvent.objects.filter(id__in=duplicate_ids).exists())
            self.assertEqual(DeviceEvent.objects.filter(device=self.device, event_type="network_weak", resolved=False).count(), 1)
        finally:
            DeviceEvent.objects.filter(device=self.device, event_type="network_weak").exclude(id=first.id).delete()
            self._add_constraint()

    def test_migration_duplicate_cleanup_uses_same_identity(self):
        self._remove_constraint()
        try:
            first = DeviceEvent.objects.create(device=self.device, event_type="storage_full", description="First")
            second = DeviceEvent.objects.create(device=self.device, event_type="storage_full", description="Second")
            migration = importlib.import_module("apps.monitoring.migrations.0010_dedupe_active_device_events")

            migration.merge_active_device_event_duplicates(
                type("Apps", (), {"get_model": staticmethod(lambda app_label, model_name: DeviceEvent)})(),
                connection.schema_editor(),
            )

            self.assertTrue(DeviceEvent.objects.filter(id=first.id).exists())
            self.assertFalse(DeviceEvent.objects.filter(id=second.id).exists())
            self.assertEqual(DeviceEvent.objects.filter(device=self.device, event_type="storage_full", resolved=False).count(), 1)
        finally:
            DeviceEvent.objects.filter(device=self.device, event_type="storage_full").exclude(id=first.id).delete()
            self._add_constraint()
