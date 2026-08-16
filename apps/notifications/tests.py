from unittest.mock import call, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.branches.models import Branch
from apps.devices.models import Device

from .models import Notification
from .services import NotificationService


class NotificationBroadcastTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            spa_name="Broadcast Spa",
            code="BCAST-001",
            state="Gujarat",
            city="Vadodara",
            area="Alkapuri",
            postal_code=390007,
            address="Demo address",
            is_active=True,
        )
        self.other_branch = Branch.objects.create(
            spa_name="Other Spa",
            code="OTHER-001",
            state="Gujarat",
            city="Surat",
            area="Adajan",
            postal_code=395009,
            address="Demo address",
            is_active=True,
        )
        self.device = Device.objects.create(
            branch=self.branch,
            device_id="SPA-BCAST-001",
            is_registered=True,
            is_active=True,
        )
        User = get_user_model()
        self.area_manager = User.objects.create_user(
            email="area-broadcast@example.com",
            password="pass",
            full_name="Area Broadcast",
            role="area_manager",
            is_active=True,
        )
        self.area_manager.area_branches.add(self.branch)
        self.other_area_manager = User.objects.create_user(
            email="other-area-broadcast@example.com",
            password="pass",
            full_name="Other Area Broadcast",
            role="area_manager",
            is_active=True,
        )
        self.other_area_manager.area_branches.add(self.other_branch)
        self.spa_manager = User.objects.create_user(
            email="spa-broadcast@example.com",
            password="pass",
            full_name="SPA Broadcast",
            role="spa_manager",
            branch=self.branch,
            fcm_token="spa-token",
            is_active=True,
        )
        self.admin = User.objects.create_user(
            email="admin-broadcast@example.com",
            password="pass",
            full_name="Admin Broadcast",
            role="admin",
            is_active=True,
        )

    @patch("apps.notifications.services.async_to_sync", side_effect=lambda fn: fn)
    @patch("apps.notifications.services.get_channel_layer")
    def test_branch_notification_broadcasts_to_matching_area_managers(self, get_channel_layer, _async_to_sync):
        notification = Notification.objects.create(
            device=self.device,
            title="New WhatsApp Lead",
            body="Customer - Area - Service",
            notification_type="doubletick_lead",
            is_sent=True,
        )
        channel_layer = get_channel_layer.return_value

        NotificationService._broadcast_notification(notification)

        sent_groups = [item.args[0] for item in channel_layer.group_send.call_args_list]
        self.assertIn("crm_dashboard", sent_groups)
        self.assertIn(f"branch_{self.branch.id}", sent_groups)
        self.assertIn(f"area_manager_{self.area_manager.id}", sent_groups)
        self.assertNotIn(f"area_manager_{self.other_area_manager.id}", sent_groups)
        self.assertEqual(len(sent_groups), len(set(sent_groups)))

    @patch("apps.notifications.services.async_to_sync", side_effect=lambda fn: fn)
    @patch("apps.notifications.services.get_channel_layer")
    def test_branch_refresh_broadcasts_to_matching_area_managers(self, get_channel_layer, _async_to_sync):
        channel_layer = get_channel_layer.return_value

        NotificationService._broadcast_refresh(str(self.branch.id))

        channel_layer.group_send.assert_has_calls(
            [
                call("crm_dashboard", {
                    "type": "broadcast_message",
                    "message": {"type": "refresh_notifications"},
                }),
                call(f"branch_{self.branch.id}", {
                    "type": "broadcast_message",
                    "message": {"type": "refresh_notifications"},
                }),
                call(f"area_manager_{self.area_manager.id}", {
                    "type": "broadcast_message",
                    "message": {"type": "refresh_notifications"},
                }),
            ],
            any_order=True,
        )

    @patch("apps.notifications.views.NotificationService.send_push", return_value=True)
    def test_manual_alert_user_targets_only_spa_managers(self, send_push):
        self.area_manager.fcm_token = "area-token"
        self.area_manager.save(update_fields=["fcm_token"])
        client = APIClient()
        client.force_authenticate(self.admin)

        response = client.post(
            "/api/v1/notifications/send-manual/",
            {
                "target_type": "users",
                "user_ids": [str(self.spa_manager.id), str(self.area_manager.id)],
                "title": "Device App Alert",
                "body": "Alert body",
                "type": "alert",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_count"], 1)
        self.assertEqual(send_push.call_count, 1)
        self.assertEqual(send_push.call_args.args[0], self.spa_manager)

    def test_alert_push_service_skips_non_spa_manager_users_without_failed_log(self):
        self.area_manager.fcm_token = "area-token"
        self.area_manager.save(update_fields=["fcm_token"])

        sent = NotificationService.send_push(
            recipient=self.area_manager,
            title="Device App Alert",
            body="Alert body",
            notification_type="alert",
        )

        self.assertFalse(sent)
        self.assertFalse(Notification.objects.filter(user=self.area_manager, title="Device App Alert").exists())
