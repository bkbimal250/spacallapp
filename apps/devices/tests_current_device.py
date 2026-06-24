from django.test import TestCase
from rest_framework.test import APIClient

from apps.branches.models import Branch, BranchGroups
from apps.devices.models import Device
from apps.monitoring.models import DeviceHealth


class CurrentDeviceViewTests(TestCase):
    def setUp(self):
        group = BranchGroups.objects.create(name="Current Device Group")
        branch = Branch.objects.create(
            spa_name="Current Device Branch",
            code="CUR-01",
            city="Pune",
            state="Maharashtra",
            area="Central",
            postal_code=411001,
            address="Test address",
            branch_group=group,
        )
        self.device = Device.objects.create(
            branch=branch,
            device_id="DEV-CURRENT-01",
            secret_key="current-secret",
            phone_name="Front Desk Phone",
            sim_1_number="1111111111",
            is_registered=True,
        )
        DeviceHealth.objects.update_or_create(
            device=self.device,
            defaults={
                "sim_1_number": "9999999999",
                "sim_2_number": "8888888888",
            },
        )
        self.client = APIClient()

    def test_returns_crm_phone_name_and_latest_heartbeat_sim_numbers(self):
        response = self.client.get(
            "/api/v1/devices/me/",
            HTTP_X_DEVICE_ID=self.device.device_id,
            HTTP_X_DEVICE_SECRET=self.device.secret_key,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["phone_name"], "Front Desk Phone")
        self.assertEqual(response.data["sim_1_number"], "9999999999")
        self.assertEqual(response.data["sim_2_number"], "8888888888")
