from django.test import override_settings
from io import StringIO
from django.core.management import call_command
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.branches.models import Branch
from apps.devices.models import Device
from apps.locations.models import Area, City, LocationGroup, LocationGroupArea, State

from .models import (
    DoubleTickAreaAlias,
    DoubleTickChannel,
    DoubleTickConversation,
    DoubleTickCustomer,
    DoubleTickLead,
    DoubleTickLeadArea,
    DoubleTickLeadAreaBranch,
    DoubleTickLeadVisibility,
    DoubleTickMessage,
    DoubleTickTeamMemberMapping,
)
from .services import CRMLocationMatchEngine, DoubleTickConversationService, LeadQualificationService


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
            "receivedAt": "2026-06-14T10:18:40.750Z",
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

    def test_hello_creates_pending_unassigned_lead_without_raw_area(self):
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
        self.assertEqual(conversation.raw_area, "")
        lead = DoubleTickLead.objects.get()
        self.assertEqual(lead.status, DoubleTickLead.Status.UNASSIGNED)
        self.assertIsNone(lead.matched_area)
        self.assertEqual(conversation.current_lead, lead)

    def test_location_match_engine_classifies_required_examples(self):
        state = State.objects.create(name="Maharashtra")
        city = City.objects.create(name="NAVI MUMBAI", state=state)
        LocationGroup.objects.create(name="Panvel To Seawoods", city=city)
        Area.objects.create(name="Belapur", city=city)

        self.assertEqual(CRMLocationMatchEngine.classify_message("hi")["classification"], "greeting")
        self.assertEqual(CRMLocationMatchEngine.classify_message("job chahiye")["classification"], "job_inquiry")
        self.assertEqual(CRMLocationMatchEngine.classify_message("Explore Services")["classification"], "service_action")
        city_result = CRMLocationMatchEngine.classify_message("NAVI MUMBAI")
        self.assertEqual(city_result["classification"], "city")
        self.assertEqual(city_result["raw_city"], "NAVI MUMBAI")
        self.assertEqual(city_result["raw_area"], "")
        group_result = CRMLocationMatchEngine.classify_message("Panvel To Seawoods")
        self.assertEqual(group_result["classification"], "location_group")
        self.assertEqual(group_result["raw_group"], "Panvel To Seawoods")
        area_result = CRMLocationMatchEngine.classify_message("Belapur")
        self.assertEqual(area_result["classification"], "area")
        self.assertEqual(area_result["raw_area"], "Belapur")

    def test_okay_updates_same_conversation(self):
        for message_id, text in [("m1", "Hello"), ("m2", "Okay")]:
            self.client.post(
                "/api/v1/doubletick/webhook/",
                self.webhook_payload(message_id=message_id, text=text, area=""),
                format="json",
                HTTP_X_DOUBLETICK_SECRET="test-secret",
            )

        self.assertEqual(DoubleTickConversation.objects.count(), 1)
        self.assertEqual(DoubleTickMessage.objects.filter(direction=DoubleTickMessage.Direction.INBOUND).count(), 2)
        self.assertEqual(DoubleTickLead.objects.count(), 1)
        self.assertEqual(DoubleTickLead.objects.get().status, DoubleTickLead.Status.UNASSIGNED)

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
        self.assertEqual(DoubleTickLead.objects.count(), 1)
        self.assertEqual(DoubleTickLead.objects.get().status, DoubleTickLead.Status.UNASSIGNED)

    def test_associate_status_events_create_and_update_one_outbound_message(self):
        self.client.post(
            "/api/v1/doubletick/webhook/",
            self.webhook_payload(message_id="customer-hello", text="Hello", area=""),
            format="json",
            HTTP_X_DOUBLETICK_SECRET="test-secret",
        )
        DoubleTickTeamMemberMapping.objects.create(doubletick_phone="919833365697", display_name="Dhanraj Jadhav")
        payload = {
            "to": "+91 98765 43210",
            "sentBy": "919833365697",
            "status": "SENT",
            "message": {"text": "Please provide your city and nearest area.", "type": "TEXT"},
            "messageId": "associate-1",
            "assignedTo": "919833365697",
            "wabaNumber": "918976822803",
            "customerName": "Ravi Kumar",
            "statusTimestamp": "2026-06-14T10:18:55.000Z",
        }

        for provider_status in ["SENT", "DELIVERED", "READ"]:
            payload["status"] = provider_status
            response = self.client.post(
                "/api/v1/doubletick/webhook/",
                payload,
                format="json",
                HTTP_X_DOUBLETICK_SECRET="test-secret",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        outbound = DoubleTickMessage.objects.get(message_id="associate-1")
        self.assertEqual(outbound.direction, DoubleTickMessage.Direction.OUTBOUND)
        self.assertEqual(outbound.origin, DoubleTickMessage.Origin.AGENT)
        self.assertEqual(outbound.sender_display_name, "Dhanraj Jadhav")
        self.assertEqual(outbound.status, DoubleTickMessage.Status.READ)
        self.assertEqual(DoubleTickMessage.objects.filter(message_id="associate-1").count(), 1)
        self.assertEqual(DoubleTickLead.objects.count(), 1)

    def test_messages_api_returns_inbound_and_outbound_chronologically(self):
        self.client.post(
            "/api/v1/doubletick/webhook/",
            self.webhook_payload(message_id="customer-hello-2", text="Hello", area=""),
            format="json",
            HTTP_X_DOUBLETICK_SECRET="test-secret",
        )
        self.client.post(
            "/api/v1/doubletick/webhook/",
            {
                "to": "+91 98765 43210",
                "sentBy": "API",
                "status": "DELIVERED",
                "message": {"text": "Please provide your city and nearest area.", "type": "TEXT"},
                "messageId": "api-1",
                "wabaNumber": "918976822803",
                "statusTimestamp": "2026-06-14T10:19:55.000Z",
            },
            format="json",
            HTTP_X_DOUBLETICK_SECRET="test-secret",
        )
        conversation = DoubleTickConversation.objects.get()

        self.client.force_authenticate(self.admin)
        response = self.client.get(f"/api/v1/doubletick/conversations/{conversation.id}/messages/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["direction"], "inbound")
        self.assertTrue(any(item["sender"]["type"] == "api" for item in response.data))

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

    def test_reprocess_location_matches_dry_run_does_not_persist_area(self):
        customer = DoubleTickCustomer.objects.create(
            phone_number="+91 99999 77777",
            normalized_phone="9999977777",
        )
        conversation = DoubleTickConversation.objects.create(
            customer=customer,
            channel=None,
            status=DoubleTickConversation.Status.AREA_UNMATCHED,
            raw_city="Mumbai",
            raw_area="Bandra",
        )
        output = StringIO()
        call_command("reprocess_doubletick_location_matches", "--dry-run", "--only-unmatched", stdout=output)

        conversation.refresh_from_db()
        self.assertIn("dry_run=True", output.getvalue())
        self.assertIsNone(conversation.matched_area)
        self.assertFalse(conversation.area_confirmed)

    def test_reprocess_location_matches_commit_matches_crm_location(self):
        state = State.objects.create(name="Maharashtra")
        city = City.objects.create(name="Mumbai", state=state)
        Area.objects.create(name="Bandra", city=city)

        customer = DoubleTickCustomer.objects.create(
            phone_number="+91 99999 88888",
            normalized_phone="9999988888",
        )
        conversation = DoubleTickConversation.objects.create(
            customer=customer,
            channel=None,
            status=DoubleTickConversation.Status.AREA_UNMATCHED,
            raw_city="Mumbai",
            raw_area="Bandra",
        )

        output = StringIO()
        call_command("reprocess_doubletick_location_matches", "--commit", "--only-unmatched", stdout=output)

        conversation.refresh_from_db()
        self.assertIn("dry_run=False", output.getvalue())
        self.assertTrue(conversation.area_confirmed)
        self.assertIsNotNone(conversation.matched_area)
        self.assertEqual(conversation.status, DoubleTickConversation.Status.DISTRIBUTED)
        self.assertEqual(DoubleTickLead.objects.filter(conversation=conversation).count(), 1)
        self.assertTrue(DoubleTickLeadVisibility.objects.filter(lead__conversation=conversation).exists())

    def test_fuzzy_location_match_exact_and_fuzzy_thresholds(self):
        state = State.objects.create(name="Maharashtra")
        city = City.objects.create(name="Navi Mumbai", state=state)
        area = Area.objects.create(name="Belapur", city=city)

        # 1. Test Exact match
        result = CRMLocationMatchEngine.classify_message("Belapur")
        self.assertEqual(result["classification"], "area")
        self.assertEqual(result["confidence"], 1.0)
        self.assertEqual(result["reason"], "area_exact")
        self.assertEqual(result["raw_area"], "Belapur")

        # 2. Test High confidence fuzzy match (should auto-apply)
        result2 = CRMLocationMatchEngine.classify_message("Belapurr")
        self.assertEqual(result2["classification"], "area")
        self.assertGreaterEqual(result2["confidence"], 0.92)
        self.assertIsNotNone(result2["matched_area"])

        # 3. Test Suggestion confidence fuzzy match (score 80-91)
        result3 = CRMLocationMatchEngine.classify_message("Balapur")
        self.assertEqual(result3["classification"], "area")
        self.assertIsNone(result3["matched_area"])
        self.assertIn("suggested_match", result3)
        self.assertEqual(result3["suggested_match"]["name"], "Belapur")
        self.assertGreaterEqual(result3["suggested_match"]["confidence"], 0.8)
        self.assertLess(result3["suggested_match"]["confidence"], 0.92)

        # 4. Test Low confidence fuzzy match (score < 80)
        result4 = CRMLocationMatchEngine.classify_message("RandomGibberishLocation")
        self.assertEqual(result4["classification"], "unknown")
        self.assertIsNone(result4["matched_area"])
        self.assertNotIn("suggested_match", result4)

        # Suggestions must not leak unconfirmed text into distributable fields.
        self.assertEqual(result3["raw_area"], "")
        self.assertEqual(result3["raw_city"], "")

    def test_location_match_links_routing_profile_to_master_area(self):
        state = State.objects.create(name="Gujarat")
        city = City.objects.create(name="Ahmedabad", state=state)
        area = Area.objects.create(name="Bodakdev", city=city)

        result = CRMLocationMatchEngine.classify_message("Bodakdev")

        self.assertEqual(result["classification"], "area")
        self.assertIsNotNone(result["matched_area"])
        self.assertEqual(result["matched_area"].location_area_id, area.id)

    def test_mobile_available_queue_is_paginated_clean_and_visibility_scoped(self):
        state = State.objects.create(name="Karnataka")
        city = City.objects.create(name="Bengaluru", state=state)
        group = LocationGroup.objects.create(name="Central Bengaluru", city=city)
        area = Area.objects.create(name="Indiranagar", city=city)
        LocationGroupArea.objects.create(group=group, area=area)
        routing_profile = DoubleTickLeadArea.objects.create(
            name="Indiranagar",
            state="Karnataka",
            city="Bengaluru",
            normalized_name="indiranagar",
            location_area=area,
        )
        DoubleTickLeadAreaBranch.objects.create(lead_area=routing_profile, branch=self.branch)
        lead = DoubleTickLead.objects.create(
            customer_name="Mobile Customer",
            phone_number="9999999999",
            latest_customer_message="Need an appointment",
            matched_area=routing_profile,
            status=DoubleTickLead.Status.AVAILABLE,
        )
        DoubleTickLeadVisibility.objects.create(
            lead=lead,
            branch=self.branch,
            user=self.spa_manager,
        )
        hidden = DoubleTickLead.objects.create(
            customer_name="Hidden Customer",
            phone_number="8888888888",
            matched_area=routing_profile,
            status=DoubleTickLead.Status.AVAILABLE,
        )
        DoubleTickLeadVisibility.objects.create(
            lead=hidden,
            branch=self.other_branch,
            user=self.other_spa_manager,
        )

        self.client.force_authenticate(self.spa_manager)
        response = self.client.get("/api/v1/doubletick/mobile/leads/available/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        payload = response.data["results"][0]
        self.assertEqual(payload["lead_id"], str(lead.id))
        self.assertEqual(payload["city_name"], "Bengaluru")
        self.assertEqual(payload["group_name"], "Central Bengaluru")
        self.assertEqual(payload["area_name"], "Indiranagar")
        self.assertEqual(payload["branch_name"], "Vashi Spa")
        self.assertEqual(payload["owner_name"], "Unclaimed")
        self.assertEqual(payload["device_name"], "-")
        self.assertTrue(payload["is_unclaimed"])
        self.assertEqual(payload["android_visibility_status"], "visible")
        self.assertNotIn("raw_payload", payload)
        self.assertNotIn("visibilities", payload)

    def test_mobile_queue_never_returns_unmatched_visible_lead_to_spa_manager(self):
        lead = DoubleTickLead.objects.create(
            customer_name="Pending Customer",
            phone_number="7777777777",
            status=DoubleTickLead.Status.UNASSIGNED,
        )
        DoubleTickLeadVisibility.objects.create(
            lead=lead,
            branch=self.branch,
            user=self.spa_manager,
        )

        self.client.force_authenticate(self.spa_manager)
        response = self.client.get("/api/v1/doubletick/mobile/leads/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_mobile_routing_audit_command_runs(self):
        output = StringIO()
        call_command("audit_mobile_lead_routing", stdout=output)
        report = output.getvalue()
        self.assertIn("Total matched leads", report)
        self.assertIn("DoubleTickLeadArea without locations.Area link", report)
        self.assertIn("Failed distribution audits", report)

    def test_upsert_customer_returns_canonical_when_duplicates_exist(self):
        channel = DoubleTickChannel.objects.create(name="Main WABA", waba_number="918976822803")
        canonical = DoubleTickCustomer.objects.create(
            dt_customer_id="dt-dup-1",
            phone_number="+91 98765 43210",
            normalized_phone="+919876543210",
            customer_name="Ravi Kumar",
            channel=channel,
        )
        duplicate = DoubleTickCustomer.objects.create(
            dt_customer_id="dt-dup-1",
            phone_number="+91 98765 43210",
            normalized_phone="+919876543210",
            channel=channel,
        )

        customer, created = DoubleTickConversationService._upsert_customer(
            {
                "doubletick_customer_id": "dt-dup-1",
                "phone_number": "+91 98765 43210",
                "normalized_phone": "+919876543210",
                "customer_name": "Ravi Updated",
                "whatsapp_name": "Ravi WA",
            },
            {"customer": {"id": "dt-dup-1", "name": "Ravi Updated"}},
            channel,
        )

        self.assertFalse(created)
        self.assertEqual(customer.id, canonical.id)
        customer.refresh_from_db()
        duplicate.refresh_from_db()
        self.assertEqual(customer.customer_name, "Ravi Updated")
        self.assertEqual(duplicate.customer_name, "")

    def test_duplicate_customer_same_phone_channel_does_not_crash_webhook(self):
        channel = DoubleTickChannel.objects.create(name="Main WABA", waba_number="918976822803")
        canonical = DoubleTickCustomer.objects.create(
            phone_number="+91 98765 43210",
            normalized_phone="+919876543210",
            customer_name="Ravi Kumar",
            channel=channel,
        )
        DoubleTickCustomer.objects.create(
            phone_number="+91 98765 43210",
            normalized_phone="+919876543210",
            channel=channel,
        )
        payload = self.webhook_payload(message_id="dup-customer-1")
        payload["wabaNumber"] = "918976822803"
        payload["customer"]["phone"] = "+91 98765 43210"
        payload["customer"]["id"] = "dt-webhook-dup"

        response = self.client.post(
            "/api/v1/doubletick/webhook/",
            payload,
            format="json",
            HTTP_X_DOUBLETICK_SECRET="test-secret",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        conversation = DoubleTickConversation.objects.get(dt_conversation_id="chat-1")
        message = DoubleTickMessage.objects.get(dt_message_id="dup-customer-1")
        lead = DoubleTickLead.objects.get(conversation=conversation)
        self.assertEqual(conversation.customer_id, canonical.id)
        self.assertEqual(message.customer_id, canonical.id)
        self.assertEqual(lead.customer_id, canonical.id)
        self.assertTrue(DoubleTickLeadVisibility.objects.filter(lead=lead, branch=self.branch).exists())

    def test_new_message_after_runtime_reset_creates_fresh_lead(self):
        customer = DoubleTickCustomer.objects.create(
            phone_number="+91 98765 43210",
            normalized_phone="+919876543210",
        )
        DoubleTickConversation.objects.create(
            customer=customer,
            dt_conversation_id="old-reset-chat",
            status=DoubleTickConversation.Status.CLOSED,
        )
        payload = self.webhook_payload(message_id="after-reset-1")
        payload["chat"]["id"] = "fresh-chat-after-reset"

        response = self.client.post(
            "/api/v1/doubletick/webhook/",
            payload,
            format="json",
            HTTP_X_DOUBLETICK_SECRET="test-secret",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        conversation = DoubleTickConversation.objects.get(dt_conversation_id="fresh-chat-after-reset")
        self.assertIsNotNone(conversation.current_lead_id)
        self.assertTrue(DoubleTickLeadVisibility.objects.filter(lead=conversation.current_lead, branch=self.branch).exists())

    def test_closed_lost_current_lead_remessage_creates_new_active_lead(self):
        customer = DoubleTickCustomer.objects.create(
            phone_number="+91 98765 43210",
            normalized_phone="+919876543210",
        )
        conversation = DoubleTickConversation.objects.create(
            customer=customer,
            status=DoubleTickConversation.Status.DISTRIBUTED,
            dt_conversation_id="active-chat-with-lost-lead",
        )
        old_lead = DoubleTickLead.objects.create(
            conversation=conversation,
            customer=customer,
            phone_number="+91 98765 43210",
            normalized_phone="+919876543210",
            status=DoubleTickLead.Status.LOST,
        )
        conversation.current_lead = old_lead
        conversation.save(update_fields=["current_lead"])

        payload = self.webhook_payload(message_id="lost-remessage-1")
        payload["chat"]["id"] = "active-chat-with-lost-lead"

        response = self.client.post(
            "/api/v1/doubletick/webhook/",
            payload,
            format="json",
            HTTP_X_DOUBLETICK_SECRET="test-secret",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        conversation.refresh_from_db()
        old_lead.refresh_from_db()
        self.assertNotEqual(conversation.current_lead_id, old_lead.id)
        self.assertEqual(old_lead.status, DoubleTickLead.Status.LOST)
        self.assertEqual(conversation.current_lead.status, DoubleTickLead.Status.AVAILABLE)
        self.assertTrue(DoubleTickLeadVisibility.objects.filter(lead=conversation.current_lead, branch=self.branch).exists())

    def test_dedupe_doubletick_customers_dry_run_does_not_change_db(self):
        channel = DoubleTickChannel.objects.create(name="Main WABA", waba_number="918976822803")
        canonical = DoubleTickCustomer.objects.create(
            phone_number="+91 98765 43210",
            normalized_phone="+919876543210",
            customer_name="Ravi Kumar",
            channel=channel,
        )
        duplicate = DoubleTickCustomer.objects.create(
            phone_number="+91 98765 43210",
            normalized_phone="+919876543210",
            channel=channel,
        )
        conversation = DoubleTickConversation.objects.create(customer=duplicate)
        lead = DoubleTickLead.objects.create(
            conversation=conversation,
            customer=duplicate,
            phone_number="+91 98765 43210",
            normalized_phone="+919876543210",
        )
        DoubleTickMessage.objects.create(
            conversation=conversation,
            lead=lead,
            customer=duplicate,
            dt_message_id="dry-run-msg",
            direction=DoubleTickMessage.Direction.INBOUND,
            origin=DoubleTickMessage.Origin.CUSTOMER,
        )

        output = StringIO()
        call_command("dedupe_doubletick_customers", "--dry-run", stdout=output)

        self.assertIn("Dry run only", output.getvalue())
        self.assertEqual(DoubleTickCustomer.objects.count(), 2)
        conversation.refresh_from_db()
        lead.refresh_from_db()
        self.assertEqual(conversation.customer_id, duplicate.id)
        self.assertEqual(lead.customer_id, duplicate.id)
        self.assertTrue(DoubleTickCustomer.objects.filter(id=canonical.id).exists())

    def test_dedupe_doubletick_customers_commit_reassigns_related_rows(self):
        channel = DoubleTickChannel.objects.create(name="Main WABA", waba_number="918976822803")
        canonical = DoubleTickCustomer.objects.create(
            phone_number="+91 98765 43210",
            normalized_phone="+919876543210",
            customer_name="Ravi Kumar",
            channel=channel,
        )
        duplicate = DoubleTickCustomer.objects.create(
            phone_number="+91 98765 43210",
            normalized_phone="+919876543210",
            whatsapp_name="Ravi WA",
            channel=channel,
        )
        conversation = DoubleTickConversation.objects.create(customer=duplicate)
        lead = DoubleTickLead.objects.create(
            conversation=conversation,
            customer=duplicate,
            phone_number="+91 98765 43210",
            normalized_phone="+919876543210",
        )
        message = DoubleTickMessage.objects.create(
            conversation=conversation,
            lead=lead,
            customer=duplicate,
            dt_message_id="commit-msg",
            direction=DoubleTickMessage.Direction.INBOUND,
            origin=DoubleTickMessage.Origin.CUSTOMER,
        )

        output = StringIO()
        call_command("dedupe_doubletick_customers", "--commit", stdout=output)

        self.assertIn("Duplicate DoubleTick customers merged", output.getvalue())
        self.assertEqual(DoubleTickCustomer.objects.count(), 1)
        conversation.refresh_from_db()
        lead.refresh_from_db()
        message.refresh_from_db()
        self.assertEqual(conversation.customer_id, canonical.id)
        self.assertEqual(lead.customer_id, canonical.id)
        self.assertEqual(message.customer_id, canonical.id)

    def test_generic_messages_never_become_area_candidates(self):
        for text in [
            "hi",
            "hello",
            "ok",
            "more info",
            "Hindi me message kijiye",
            "job chahiye",
            "Explore Services",
        ]:
            result = CRMLocationMatchEngine.classify_message(text)
            self.assertEqual(result["raw_area"], "", text)
            self.assertIsNone(result["matched_area"], text)

    def test_manual_correction_api(self):
        state = State.objects.create(name="Maharashtra")
        city = City.objects.create(name="Navi Mumbai", state=state)
        area = Area.objects.create(name="Belapur", city=city)
        customer = DoubleTickCustomer.objects.create(phone_number="+91 99999 55555", normalized_phone="9999955555")
        conversation = DoubleTickConversation.objects.create(
            customer=customer,
            status=DoubleTickConversation.Status.AREA_UNMATCHED,
            raw_city="Navi Mumbai",
            raw_area="UnknownArea",
        )

        self.client.force_authenticate(self.admin)

        # 1. Correct as City
        response = self.client.post(
            f"/api/v1/doubletick/conversations/{conversation.id}/manual-correct/",
            {"action": "correct_city", "city_name": "Mumbai"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        conversation.refresh_from_db()
        self.assertEqual(conversation.raw_city, "Mumbai")
        self.assertEqual(conversation.raw_area, "")
        self.assertEqual(conversation.status, DoubleTickConversation.Status.AWAITING_LOCATION)

        # 2. Correct as Area
        response = self.client.post(
            f"/api/v1/doubletick/conversations/{conversation.id}/manual-correct/",
            {"action": "correct_area", "area_id": str(area.id)},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        conversation.refresh_from_db()
        self.assertEqual(conversation.raw_area, "Belapur")
        self.assertEqual(conversation.raw_city, "Navi Mumbai")
        self.assertEqual(conversation.status, DoubleTickConversation.Status.QUALIFIED)
        self.assertTrue(conversation.area_confirmed)

        # 3. Add Alias
        response = self.client.post(
            f"/api/v1/doubletick/conversations/{conversation.id}/manual-correct/",
            {"action": "add_alias", "area_id": str(area.id), "alias_text": "Belapoor"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alias_exists = DoubleTickAreaAlias.objects.filter(alias="Belapoor").exists()
        self.assertTrue(alias_exists)

        # 4. Save and Send
        # First qualify it as lead
        lead = LeadQualificationService.ensure_conversation_lead(conversation, distribute=False)
        self.assertEqual(lead.status, DoubleTickLead.Status.QUALIFIED)

        response = self.client.post(
            f"/api/v1/doubletick/conversations/{conversation.id}/manual-correct/",
            {"action": "save_and_send"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        conversation.refresh_from_db()
        self.assertEqual(conversation.status, DoubleTickConversation.Status.DISTRIBUTED)
        lead.refresh_from_db()
        self.assertEqual(lead.status, DoubleTickLead.Status.AVAILABLE)
