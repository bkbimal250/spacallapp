from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.branches.models import Branch
from apps.devices.models import Device

from .models import (
    DoubleTickAreaAlias,
    DoubleTickConversation,
    DoubleTickLead,
    DoubleTickLeadArea,
    DoubleTickLeadAreaBranch,
    DoubleTickLeadVisibility,
    DoubleTickMessage,
)


@override_settings(DOUBLETICK_WEBHOOK_SECRET="test-secret", DOUBLETICK_API_KEY="")
class DoubleTickBackendTests(APITestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            spa_name="Vashi Spa",
            code="VSH-001",
            state="Maharashtra",
            city="Navi Mumbai",
            area="Vashi",
            postal_code=400703,
            address="Demo address",
            is_active=True,
        )
        self.other_branch = Branch.objects.create(
            spa_name="Bandra Spa",
            code="BAN-001",
            state="Maharashtra",
            city="Mumbai",
            area="Bandra",
            postal_code=400050,
            address="Demo address",
            is_active=True,
        )
        self.lead_area = DoubleTickLeadArea.objects.create(
            name="Vashi",
            state="Maharashtra",
            city="Navi Mumbai",
            normalized_name="vashi",
        )
        DoubleTickAreaAlias.objects.create(lead_area=self.lead_area, alias="Vashi", normalized_alias="vashi")
        DoubleTickLeadAreaBranch.objects.create(lead_area=self.lead_area, branch=self.branch)

        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="pass",
            full_name="Admin User",
            role="admin",
            is_active=True,
        )
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
        self.area_manager = User.objects.create_user(
            email="area@example.com",
            password="pass",
            full_name="Area Manager",
            role="area_manager",
            is_active=True,
        )
        self.area_manager.area_branches.add(self.branch)
        self.device = Device.objects.create(
            branch=self.branch,
            device_id="SPA-TEST-001",
            secret_key="device-secret",
            is_registered=True,
            is_active=True,
        )

    def webhook_payload(self, message_id="msg-1", text="Vashi", area="Vashi", phone="+91 98765 43210"):
        return {
            "eventType": "MESSAGE_RECEIVED",
            "lastMessageOrigin": "CUSTOMER",
            "customer": {"name": "Ravi Kumar", "phone": phone},
            "message": {"id": message_id, "text": text},
            "chat": {"id": "chat-1"},
            "city": "Navi Mumbai",
            "area": area,
            "service": "Massage",
        }

    def test_valid_webhook_with_confirmed_area_creates_distributed_lead(self):
        response = self.client.post(
            "/api/v1/doubletick/webhook/",
            self.webhook_payload(),
            format="json",
            HTTP_X_DOUBLETICK_SECRET="test-secret",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        lead = DoubleTickLead.objects.get()
        self.assertEqual(lead.matched_area, self.lead_area)
        self.assertEqual(lead.status, DoubleTickLead.Status.AVAILABLE)
        self.assertTrue(DoubleTickLeadVisibility.objects.filter(lead=lead, branch=self.branch).exists())

    def test_webhook_without_trailing_slash_is_accepted(self):
        response = self.client.post(
            "/api/v1/doubletick/webhook",
            self.webhook_payload(message_id="no-slash"),
            format="json",
            HTTP_X_DOUBLETICK_SECRET="test-secret",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_webhook_with_invalid_secret_returns_403(self):
        response = self.client.post(
            "/api/v1/doubletick/webhook/",
            self.webhook_payload(),
            format="json",
            HTTP_X_DOUBLETICK_SECRET="wrong",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(DoubleTickLead.objects.count(), 0)

    def test_hello_creates_pending_conversation_not_available_lead(self):
        payload = self.webhook_payload(message_id="hello-1", text="Hello", area="")
        response = self.client.post(
            "/api/v1/doubletick/webhook/",
            payload,
            format="json",
            HTTP_X_DOUBLETICK_SECRET="test-secret",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        conversation = DoubleTickConversation.objects.get()
        self.assertEqual(conversation.status, DoubleTickConversation.Status.AWAITING_LOCATION)
        self.assertEqual(conversation.pending_reason, DoubleTickConversation.PendingReason.GREETING_ONLY)
        self.assertEqual(DoubleTickLead.objects.count(), 0)

    def test_okay_updates_same_conversation(self):
        for message_id, text in [("m1", "Hello"), ("m2", "Okay")]:
            self.client.post(
                "/api/v1/doubletick/webhook/",
                self.webhook_payload(message_id=message_id, text=text, area=""),
                format="json",
                HTTP_X_DOUBLETICK_SECRET="test-secret",
            )

        self.assertEqual(DoubleTickConversation.objects.count(), 1)
        self.assertEqual(DoubleTickMessage.objects.count(), 2)
        self.assertEqual(DoubleTickLead.objects.count(), 0)

    def test_status_event_updates_message_without_creating_lead(self):
        self.client.post(
            "/api/v1/doubletick/webhook/",
            self.webhook_payload(message_id="out-1", text="Hello", area=""),
            format="json",
            HTTP_X_DOUBLETICK_SECRET="test-secret",
        )
        response = self.client.post(
            "/api/v1/doubletick/webhook/",
            {"eventType": "DELIVERED", "messageId": "out-1", "status": "DELIVERED"},
            format="json",
            HTTP_X_DOUBLETICK_SECRET="test-secret",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DoubleTickLead.objects.count(), 0)

    def test_spa_manager_sees_only_visible_branch_leads(self):
        lead = DoubleTickLead.objects.create(
            customer_name="Own",
            phone_number="111",
            matched_area=self.lead_area,
            status=DoubleTickLead.Status.AVAILABLE,
        )
        DoubleTickLeadVisibility.objects.create(lead=lead, branch=self.branch, user=self.spa_manager)
        other = DoubleTickLead.objects.create(customer_name="Other", phone_number="222", status=DoubleTickLead.Status.AVAILABLE)
        DoubleTickLeadVisibility.objects.create(lead=other, branch=self.other_branch, user=self.other_spa_manager)

        self.client.force_authenticate(self.spa_manager)
        response = self.client.get("/api/v1/doubletick/leads/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.data.get("results", response.data)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["customer_name"], "Own")

    def test_first_manager_claims_and_second_gets_conflict(self):
        lead = DoubleTickLead.objects.create(
            customer_name="Claim",
            phone_number="111",
            matched_area=self.lead_area,
            status=DoubleTickLead.Status.AVAILABLE,
        )
        DoubleTickLeadVisibility.objects.create(lead=lead, branch=self.branch, user=self.spa_manager)

        self.client.force_authenticate(self.spa_manager)
        first = self.client.post(f"/api/v1/doubletick/mobile/leads/{lead.id}/claim/")
        second = self.client.post(f"/api/v1/doubletick/mobile/leads/{lead.id}/claim/")

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_409_CONFLICT)

    def test_admin_reply_records_failed_outbound_message_when_api_key_missing(self):
        self.client.post(
            "/api/v1/doubletick/webhook/",
            self.webhook_payload(message_id="hello-reply", text="Hello", area=""),
            format="json",
            HTTP_X_DOUBLETICK_SECRET="test-secret",
        )
        conversation = DoubleTickConversation.objects.get()
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            f"/api/v1/doubletick/conversations/{conversation.id}/reply/",
            {"message_type": "text", "text": "Please share your city and nearest area."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(DoubleTickMessage.objects.filter(direction=DoubleTickMessage.Direction.OUTBOUND, status=DoubleTickMessage.Status.FAILED).exists())
