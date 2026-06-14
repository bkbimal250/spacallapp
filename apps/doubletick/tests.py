from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.branches.models import Branch
from apps.devices.models import Device

from .models import DoubleTickLead


@override_settings(DOUBLETICK_WEBHOOK_SECRET="test-secret")
class DoubleTickLeadTests(APITestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            spa_name="Koramangala Spa",
            code="KOR-001",
            state="Karnataka",
            city="Bengaluru",
            area="Koramangala",
            postal_code=560034,
            address="Demo address",
            is_active=True,
        )
        self.other_branch = Branch.objects.create(
            spa_name="Indiranagar Spa",
            code="IND-001",
            state="Karnataka",
            city="Bengaluru",
            area="Indiranagar",
            postal_code=560038,
            address="Demo address",
            is_active=True,
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="pass",
            full_name="Admin User",
            role="admin",
            is_active=True,
        )
        self.area_manager = User.objects.create_user(
            email="area@example.com",
            password="pass",
            full_name="Area Manager",
            role="area_manager",
            is_active=True,
        )
        self.area_manager.area_branches.add(self.branch)
        self.spa_manager = User.objects.create_user(
            email="spa@example.com",
            password="pass",
            full_name="SPA Manager",
            role="spa_manager",
            branch=self.branch,
            is_active=True,
        )
        self.other_spa_manager = User.objects.create_user(
            email="other@example.com",
            password="pass",
            full_name="Other SPA Manager",
            role="spa_manager",
            branch=self.other_branch,
            is_active=True,
        )
        self.device = Device.objects.create(
            branch=self.branch,
            device_id="SPA-TEST-001",
            secret_key="device-secret",
            is_registered=True,
            is_active=True,
        )

    def webhook_payload(self, message_id="msg-1", area="Koramangala"):
        return {
            "event": "message.created",
            "customer": {
                "name": "Ravi Kumar",
                "phone": "+91 98765 43210",
            },
            "message": {
                "id": message_id,
                "text": "Need massage appointment",
            },
            "chat": {"id": "chat-1"},
            "city": "Bengaluru",
            "area": area,
            "service": "Massage",
        }

    def test_webhook_with_valid_secret_creates_and_assigns_lead(self):
        response = self.client.post(
            "/api/v1/doubletick/webhook/",
            self.webhook_payload(),
            format="json",
            HTTP_X_DOUBLETICK_SECRET="test-secret",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        lead = DoubleTickLead.objects.get()
        self.assertEqual(lead.assigned_branch, self.branch)
        self.assertEqual(lead.assigned_user, self.spa_manager)
        self.assertEqual(lead.status, DoubleTickLead.Status.ASSIGNED)

    def test_webhook_with_invalid_secret_returns_403(self):
        response = self.client.post(
            "/api/v1/doubletick/webhook/",
            self.webhook_payload(),
            format="json",
            HTTP_X_DOUBLETICK_SECRET="wrong",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(DoubleTickLead.objects.count(), 0)

    def test_spa_manager_sees_only_own_branch_leads(self):
        DoubleTickLead.objects.create(
            customer_name="Own",
            phone_number="111",
            assigned_branch=self.branch,
            assigned_user=self.spa_manager,
            status=DoubleTickLead.Status.ASSIGNED,
        )
        DoubleTickLead.objects.create(
            customer_name="Other",
            phone_number="222",
            assigned_branch=self.other_branch,
            assigned_user=self.other_spa_manager,
            status=DoubleTickLead.Status.ASSIGNED,
        )

        self.client.force_authenticate(self.spa_manager)
        response = self.client.get("/api/v1/doubletick/leads/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.data.get("results", response.data)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["customer_name"], "Own")

    def test_area_manager_sees_only_area_branches(self):
        DoubleTickLead.objects.create(
            customer_name="Area",
            phone_number="111",
            assigned_branch=self.branch,
            status=DoubleTickLead.Status.ASSIGNED,
        )
        DoubleTickLead.objects.create(
            customer_name="Other",
            phone_number="222",
            assigned_branch=self.other_branch,
            status=DoubleTickLead.Status.ASSIGNED,
        )

        self.client.force_authenticate(self.area_manager)
        response = self.client.get("/api/v1/doubletick/leads/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.data.get("results", response.data)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["customer_name"], "Area")

    def test_admin_sees_all_leads(self):
        DoubleTickLead.objects.create(customer_name="One", phone_number="111")
        DoubleTickLead.objects.create(customer_name="Two", phone_number="222")

        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/v1/doubletick/leads/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.data.get("results", response.data)
        self.assertEqual(len(payload), 2)

    def test_mobile_device_list_returns_only_assigned_device_leads(self):
        DoubleTickLead.objects.create(
            customer_name="Device Lead",
            phone_number="111",
            assigned_branch=self.branch,
            assigned_device=self.device,
            status=DoubleTickLead.Status.ASSIGNED,
        )
        DoubleTickLead.objects.create(
            customer_name="User Lead",
            phone_number="222",
            assigned_branch=self.branch,
            assigned_user=self.spa_manager,
            status=DoubleTickLead.Status.ASSIGNED,
        )

        self.client.credentials(
            HTTP_X_DEVICE_ID="SPA-TEST-001",
            HTTP_X_DEVICE_SECRET="device-secret",
        )
        response = self.client.get("/api/v1/doubletick/mobile/leads/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.data.get("results", response.data)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["customer_name"], "Device Lead")

    def test_duplicate_webhook_does_not_create_duplicate_lead(self):
        for _ in range(2):
            response = self.client.post(
                "/api/v1/doubletick/webhook/",
                self.webhook_payload(message_id="same-message"),
                format="json",
                HTTP_X_DOUBLETICK_SECRET="test-secret",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(DoubleTickLead.objects.count(), 1)
