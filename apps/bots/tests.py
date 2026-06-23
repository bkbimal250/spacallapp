from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.branches.models import Branch
from apps.doubletick.models import (
    DoubleTickAreaAlias,
    DoubleTickChannel,
    DoubleTickConversation,
    DoubleTickLead,
    DoubleTickLeadArea,
    DoubleTickLeadAreaBranch,
    DoubleTickLeadVisibility,
    DoubleTickMessage,
)

from .models import BotExecutionLog, BotSession


@override_settings(DOUBLETICK_WEBHOOK_SECRET="test-secret", DOUBLETICK_API_KEY="")
class BotDoubleTickIntegrationTests(APITestCase):
    def setUp(self):
        self.channel, _ = DoubleTickChannel.objects.get_or_create(
            waba_number="918976822800",
            defaults={"name": "Main WABA"},
        )
        self.branch = Branch.objects.create(
            spa_name="Andheri Spa",
            code="AND-001",
            state="Maharashtra",
            city="Mumbai",
            area="Andheri",
            postal_code=400053,
            address="Andheri West",
            is_active=True,
        )
        self.lead_area = DoubleTickLeadArea.objects.create(
            name="Andheri",
            state="Maharashtra",
            city="Mumbai",
            normalized_name="andheri",
        )
        DoubleTickAreaAlias.objects.create(lead_area=self.lead_area, alias="Andheri", normalized_alias="andheri")
        DoubleTickLeadAreaBranch.objects.create(lead_area=self.lead_area, branch=self.branch)
        self.admin = User.objects.create_user(
            email="admin-bot@example.com",
            password="pass",
            full_name="Admin Bot",
            role="admin",
            is_active=True,
        )

    def webhook_payload(self, message_id="bot-msg-1", text="Hello", area=""):
        return {
            "eventType": "MESSAGE_RECEIVED",
            "lastMessageOrigin": "CUSTOMER",
            "customer": {"name": "Asha", "phone": "+91 98765 43210"},
            "message": {"id": message_id, "text": text, "type": "text"},
            "chat": {"id": "bot-chat-1"},
            "wabaNumber": "918976822800",
            "receivedAt": "2026-06-14T10:18:40.750Z",
            "city": "Mumbai" if area else "",
            "area": area,
        }

    def post_webhook(self, payload):
        return self.client.post(
            "/api/v1/doubletick/webhook/",
            payload,
            format="json",
            HTTP_X_DOUBLETICK_SECRET="test-secret",
        )

    def test_first_inbound_message_starts_bot_and_sends_greeting_once(self):
        response = self.post_webhook(self.webhook_payload())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BotSession.objects.count(), 1)
        self.assertEqual(DoubleTickLead.objects.count(), 1)
        self.assertEqual(DoubleTickMessage.objects.filter(direction=DoubleTickMessage.Direction.OUTBOUND, origin=DoubleTickMessage.Origin.BOT).count(), 2)
        self.assertEqual(BotExecutionLog.objects.filter(status=BotExecutionLog.Status.SENT).count(), 2)

        retry = self.post_webhook(self.webhook_payload())
        self.assertEqual(retry.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DoubleTickMessage.objects.filter(direction=DoubleTickMessage.Direction.OUTBOUND, origin=DoubleTickMessage.Origin.BOT).count(), 2)

    def test_area_text_matches_area_and_creates_visibility(self):
        response = self.post_webhook(self.webhook_payload(message_id="area-1", text="Andheri", area=""))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        lead = DoubleTickLead.objects.get()
        self.assertEqual(lead.matched_area, self.lead_area)
        self.assertTrue(DoubleTickLeadVisibility.objects.filter(lead=lead, branch=self.branch).exists())

    def test_job_inquiry_stays_unassigned_manual_queue(self):
        response = self.post_webhook(self.webhook_payload(message_id="job-1", text="job chahiye", area=""))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session = BotSession.objects.get()
        lead = DoubleTickLead.objects.get()
        conversation = DoubleTickConversation.objects.get()
        self.assertEqual(session.intent, "job_inquiry")
        self.assertEqual(lead.status, DoubleTickLead.Status.UNASSIGNED)
        self.assertTrue(conversation.requires_manual_attention)

    def test_manual_reply_api_saves_outbound_message(self):
        self.post_webhook(self.webhook_payload(message_id="reply-1", text="Hello", area=""))
        lead = DoubleTickLead.objects.get()
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            f"/api/v1/doubletick/leads/{lead.id}/reply/",
            {"text": "We will help you shortly."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(DoubleTickMessage.objects.filter(lead=lead, direction=DoubleTickMessage.Direction.OUTBOUND, text="We will help you shortly.").exists())

    def test_unmatched_lead_visible_in_mobile_pending_queue_for_admin(self):
        self.post_webhook(self.webhook_payload(message_id="unknown-1", text="Unknown place", area=""))
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/v1/doubletick/mobile/leads/?unmatched=true")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.data.get("results", response.data)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["status"], DoubleTickLead.Status.UNASSIGNED)
