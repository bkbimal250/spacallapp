import io
import json
import urllib.error
from datetime import datetime, time, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.branches.models import Branch, BranchOperatingHours
from apps.calllogs.models import CallLog
from apps.callrouting.models import (
    RoutingAttempt,
    RoutingCandidate,
    RoutingEvent,
    RoutingRequest,
    RoutingRule,
    RoutingWhatsAppMessage,
)
from apps.callrouting.services import PhoneNormalizationService, RoutingRuleService, RoutingService
from apps.callrouting.tasks import process_call_log_routing, send_routing_whatsapp_message
from apps.contacts.models import Contact
from apps.devices.models import Device
from apps.doubletick.models import DoubleTickConversation, DoubleTickCustomer, DoubleTickMessage
from apps.leadmanagement.models import LeadManagement
from apps.locations.models import Area, BranchCoverageArea, City, LocationGroup, State
from apps.callrouting.whatsapp import RoutingTemplateDataBuilder, RoutingWhatsAppService, RoutingWhatsAppWebhookService
from apps.callrouting.provider import DoubleTickPermanentError, DoubleTickTemplateProvider, DoubleTickTransientError


class CallRoutingModelTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            spa_name="Royal Oak Spa",
            code="RO-01",
            state="Maharashtra",
            city="Navi Mumbai",
            area="Sanpada",
            postal_code=400705,
            address="Sanpada",
        )
        self.candidate_branch = Branch.objects.create(
            spa_name="Green View Spa",
            code="GV-01",
            state="Maharashtra",
            city="Navi Mumbai",
            area="Vashi",
            postal_code=400703,
            address="Vashi",
        )
        self.device = Device.objects.create(branch=self.branch, device_id="device-1", is_registered=True)
        self.call_log = CallLog.objects.create(
            branch=self.branch,
            device=self.device,
            phone_number="9876543210",
            call_type="incoming",
            duration=30,
            sim_slot=1,
            call_time=timezone.now(),
            call_hash="routing-call-1",
        )
        self.rule = RoutingRule.objects.create(name="Night Spa Redirect")

    def create_request(self, call_log=None, **overrides):
        values = {
            "call_log": call_log or self.call_log,
            "routing_rule": self.rule,
            "source_branch": self.branch,
            "source_device": self.device,
            "contact": self.call_log.contact,
            "normalized_phone": "+919876543210",
            "call_time": self.call_log.call_time,
        }
        values.update(overrides)
        return RoutingRequest.objects.create(**values)

    def test_routing_request_has_one_to_one_call_log(self):
        request = self.create_request()
        self.assertEqual(self.call_log.routing_request, request)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_request()

    def test_routing_request_lead_is_nullable_and_attachable(self):
        request = self.create_request()
        self.assertIsNone(request.lead)

        lead = LeadManagement.objects.create(calllog=self.call_log, branch=self.branch)
        request.lead = lead
        request.save(update_fields=["lead", "updated_at"])

        request.refresh_from_db()
        self.assertEqual(request.lead, lead)

    def test_candidate_attempt_and_whatsapp_constraints(self):
        request = self.create_request()
        RoutingCandidate.objects.create(routing_request=request, branch=self.candidate_branch)
        RoutingAttempt.objects.create(routing_request=request, attempt_number=1, started_at=timezone.now())
        RoutingWhatsAppMessage.objects.create(
            routing_request=request,
            recipient_phone="+919876543210",
            template_name="night_spa_redirect",
            idempotency_key="routing-call-1-night",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RoutingCandidate.objects.create(routing_request=request, branch=self.candidate_branch)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RoutingAttempt.objects.create(routing_request=request, attempt_number=1, started_at=timezone.now())
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RoutingWhatsAppMessage.objects.create(
                    routing_request=request,
                    recipient_phone="+919876543210",
                    template_name="night_spa_redirect",
                    idempotency_key="routing-call-1-night-duplicate",
                )


class CallRoutingAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="routing-admin@example.com",
            password="pass",
            full_name="Routing Admin",
            role="admin",
        )
        self.branch = Branch.objects.create(
            spa_name="Royal Oak Spa",
            code="RO-API",
            state="Maharashtra",
            city="Navi Mumbai",
            area="Sanpada",
            postal_code=400705,
            address="Sanpada",
        )
        self.other_branch = Branch.objects.create(
            spa_name="Green View Spa",
            code="GV-API",
            state="Maharashtra",
            city="Mumbai",
            area="Bandra",
            postal_code=400050,
            address="Bandra",
        )
        self.device = Device.objects.create(branch=self.branch, device_id="api-device", is_registered=True)
        self.contact = Contact.objects.create(name="Api Customer", phone_number="9876543210")
        self.call_log = CallLog.objects.create(
            branch=self.branch,
            device=self.device,
            contact=self.contact,
            phone_number="9876543210",
            call_type="incoming",
            duration=18,
            sim_slot=1,
            call_time=timezone.now(),
            call_hash="api-routing-call",
        )
        self.rule = RoutingRule.objects.create(name="API Night Routing")
        self.routing_request = RoutingRequest.objects.create(
            call_log=self.call_log,
            contact=self.contact,
            routing_rule=self.rule,
            source_branch=self.branch,
            source_device=self.device,
            routing_type=RoutingRule.RoutingType.NIGHT,
            status=RoutingRequest.Status.ROUTED,
            normalized_phone="+919876543210",
            source_branch_open=False,
            call_time=self.call_log.call_time,
            completed_at=timezone.now(),
        )
        RoutingCandidate.objects.create(
            routing_request=self.routing_request,
            branch=self.other_branch,
            rank=1,
            relevance_score=900,
            is_open=True,
            is_eligible=True,
            is_selected=True,
        )
        RoutingAttempt.objects.create(
            routing_request=self.routing_request,
            attempt_number=1,
            status=RoutingAttempt.Status.SUCCESS,
            started_at=timezone.now(),
            completed_at=timezone.now(),
        )
        RoutingEvent.objects.create(
            routing_request=self.routing_request,
            event_type=RoutingEvent.EventType.CANDIDATE_SELECTED,
            message="Selected Green View Spa",
        )
        RoutingWhatsAppMessage.objects.create(
            routing_request=self.routing_request,
            recipient_phone="+919876543210",
            template_name="night_spa_redirect",
            template_language="en",
            template_payload={"selected_branches": [{"name": "Green View Spa"}]},
            status=RoutingWhatsAppMessage.Status.QUEUED,
            idempotency_key="api-routing-whatsapp",
        )
        self.client.force_authenticate(self.admin)

    def test_requests_list_uses_real_routing_data_and_masks_phone(self):
        response = self.client.get("/api/v1/callrouting/requests/", {"search": "Api Customer"})

        self.assertEqual(response.status_code, 200)
        row = response.data["results"][0]
        self.assertEqual(row["status"], "routed")
        self.assertEqual(row["customer_name"], "Api Customer")
        self.assertEqual(row["original_spa"], "Royal Oak Spa")
        self.assertEqual(row["phone_masked"], "XXXXX43210")
        self.assertEqual(row["selected_spas"][0]["name"], "Green View Spa")
        self.assertEqual(row["whatsapp_status"], "queued")

    def test_request_detail_includes_audit_objects_and_template_preview_data(self):
        response = self.client.get(f"/api/v1/callrouting/requests/{self.routing_request.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.data["source_branch_id"]), str(self.branch.id))
        self.assertEqual(response.data["call_log"]["phone_normalized"], "9876543210")
        self.assertEqual(response.data["call_log"]["phone_masked"], "XXXXX43210")
        self.assertEqual(response.data["candidates"][0]["branch"]["spa_name"], "Green View Spa")
        self.assertEqual(response.data["candidates"][0]["branch"]["phone"], self.other_branch.phone or "")
        self.assertEqual(response.data["events"][0]["event_type"], "candidate_selected")
        self.assertEqual(response.data["whatsapp_messages"][0]["provider"], "DoubleTick")
        self.assertEqual(response.data["whatsapp_messages"][0]["template_payload"]["selected_branches"][0]["name"], "Green View Spa")

    @override_settings(
        DOUBLETICK_API_KEY="secret-live-key",
        DOUBLETICK_SEND_FROM_WABA_NUMBER="917506359139",
        ENABLE_CALL_ROUTING=True,
        CALL_ROUTING_DRY_RUN=False,
        ENABLE_CALL_ROUTING_WHATSAPP=True,
    )
    def test_integration_status_reports_safe_config_without_api_key(self):
        response = self.client.get("/api/v1/callrouting/requests/integration-status/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["provider"], "DoubleTick")
        self.assertEqual(response.data["template_name"], "night_spa_recommendation")
        self.assertTrue(response.data["api_key_configured"])
        self.assertTrue(response.data["waba_sender_configured"])
        self.assertNotIn("secret-live-key", str(response.data))

    def test_admin_can_delete_routing_request_without_deleting_call_log(self):
        response = self.client.delete(f"/api/v1/callrouting/requests/{self.routing_request.id}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(RoutingRequest.objects.filter(id=self.routing_request.id).exists())
        self.assertTrue(CallLog.objects.filter(id=self.call_log.id).exists())

    def test_non_admin_cannot_delete_routing_request(self):
        manager = User.objects.create_user(
            email="routing-manager@example.com",
            password="pass",
            full_name="Routing Manager",
            role="spa_manager",
            branch=self.branch,
        )
        self.client.force_authenticate(manager)

        response = self.client.delete(f"/api/v1/callrouting/requests/{self.routing_request.id}/")

        self.assertEqual(response.status_code, 403)
        self.assertTrue(RoutingRequest.objects.filter(id=self.routing_request.id).exists())

    def test_summary_respects_filters(self):
        response = self.client.get("/api/v1/callrouting/requests/summary/", {"whatsapp_status": "queued"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["routed"], 1)
        self.assertEqual(response.data["whatsapp_queued"], 1)

    def test_area_manager_only_sees_assigned_source_branches(self):
        area_manager = User.objects.create_user(
            email="routing-area@example.com",
            password="pass",
            full_name="Routing Area",
            role="area_manager",
        )
        area_manager.area_branches.add(self.other_branch)
        self.client.force_authenticate(area_manager)

        response = self.client.get("/api/v1/callrouting/requests/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)


class RoutingEngineTests(TestCase):
    def setUp(self):
        self.tz = ZoneInfo("Asia/Kolkata")
        self.state = State.objects.create(name="Maharashtra")
        self.city = City.objects.create(state=self.state, name="Navi Mumbai")
        self.other_city = City.objects.create(state=self.state, name="Mumbai")
        self.group = LocationGroup.objects.create(city=self.city, name="Sanpada To Vashi")
        self.area = Area.objects.create(city=self.city, name="Sanpada")
        self.vashi = Area.objects.create(city=self.city, name="Vashi")
        self.other_area = Area.objects.create(city=self.other_city, name="Bandra")
        self.source = self.branch("Royal Oak Spa", "RO-01", self.area, self.group)
        self.device = Device.objects.create(branch=self.source, device_id="routing-device", is_registered=True)
        self.rule = RoutingRule.objects.create(
            name="Night Spa Redirect",
            routing_type=RoutingRule.RoutingType.NIGHT,
            start_time=time(22, 0),
            end_time=time(6, 0),
            max_recommendations=3,
            cooldown_minutes=60,
            priority=1,
        )

    def aware(self, year=2026, month=8, day=10, hour=23, minute=30):
        return timezone.make_aware(datetime(year, month, day, hour, minute), self.tz)

    def branch(self, name, code, area, group=None, active=True):
        return Branch.objects.create(
            spa_name=name,
            code=code,
            state=area.city.state.name,
            city=area.city.name,
            area=area.name,
            postal_code=400000,
            address=f"{name} Address",
            is_active=active,
            location_state=area.city.state,
            location_city=area.city,
            location_group=group,
            location_area=area,
        )

    def add_hours(self, branch, weekday=BranchOperatingHours.Weekday.MONDAY, opens=time(10), closes=time(3), **kwargs):
        return BranchOperatingHours.objects.create(
            branch=branch,
            weekday=weekday,
            opens_at=opens,
            closes_at=closes,
            timezone="Asia/Kolkata",
            **kwargs,
        )

    def add_24_hours(self, branch, weekday=BranchOperatingHours.Weekday.MONDAY):
        return BranchOperatingHours.objects.create(
            branch=branch,
            weekday=weekday,
            is_24_hours=True,
            opens_at=None,
            closes_at=None,
            timezone="Asia/Kolkata",
        )

    def call_log(self, phone="9876543210", at_datetime=None, branch=None, call_hash="hash-1"):
        return CallLog.objects.create(
            branch=branch or self.source,
            device=self.device,
            phone_number=phone,
            call_type="incoming",
            duration=30,
            sim_slot=1,
            call_time=at_datetime or self.aware(),
            call_hash=call_hash,
        )

    def prepare_closed_source(self):
        self.add_hours(self.source, opens=time(10), closes=time(22))

    def test_phone_normalization_accepts_indian_formats(self):
        self.assertEqual(PhoneNormalizationService.normalize("9876543210"), "+919876543210")
        self.assertEqual(PhoneNormalizationService.normalize("919876543210"), "+919876543210")
        self.assertEqual(PhoneNormalizationService.normalize("+91 98765 43210"), "+919876543210")
        self.assertEqual(PhoneNormalizationService.normalize("12345"), "")

    def test_rule_matching_supports_normal_overnight_and_boundaries(self):
        self.assertIsNotNone(RoutingRuleService.resolve_rule(self.aware(hour=23)))
        self.assertIsNotNone(RoutingRuleService.resolve_rule(self.aware(day=11, hour=2)))
        self.assertIsNotNone(RoutingRuleService.resolve_rule(self.aware(day=11, hour=5, minute=59)))
        self.assertIsNone(RoutingRuleService.resolve_rule(self.aware(day=11, hour=6)))

        self.rule.start_time = time(9)
        self.rule.end_time = time(18)
        self.rule.save(update_fields=["start_time", "end_time"])
        self.assertIsNotNone(RoutingRuleService.resolve_rule(self.aware(hour=12)))
        self.assertIsNone(RoutingRuleService.resolve_rule(self.aware(hour=20)))

    def test_no_rule_skips_request(self):
        self.rule.enabled = False
        self.rule.save(update_fields=["enabled"])
        request = RoutingService.process_call_log(self.call_log())
        self.assertEqual(request.status, RoutingRequest.Status.SKIPPED)
        self.assertEqual(request.rejection_reason, RoutingRequest.RejectionReason.NO_RULE)
        self.assertTrue(request.events.filter(event_type="no_rule").exists())

    def test_invalid_phone_skips_before_candidates(self):
        request = RoutingService.process_call_log(self.call_log(phone="12345"))
        self.assertEqual(request.status, RoutingRequest.Status.SKIPPED)
        self.assertEqual(request.rejection_reason, RoutingRequest.RejectionReason.INVALID_PHONE)
        self.assertFalse(request.candidates.exists())

    def test_source_open_skips_candidate_search(self):
        self.add_hours(self.source, opens=time(10), closes=time(3))
        request = RoutingService.process_call_log(self.call_log())
        self.assertEqual(request.status, RoutingRequest.Status.SKIPPED)
        self.assertEqual(request.rejection_reason, RoutingRequest.RejectionReason.SOURCE_SPA_OPEN)
        self.assertTrue(request.source_branch_open)
        self.assertFalse(request.candidates.exists())

    def test_source_missing_hours_is_closed_and_can_route(self):
        candidate = self.branch("Green View Spa", "GV-01", self.area, self.group)
        self.add_24_hours(candidate)

        request = RoutingService.process_call_log(self.call_log())

        self.assertEqual(request.status, RoutingRequest.Status.ROUTED)
        self.assertFalse(request.source_branch_open)
        self.assertEqual(request.candidates.filter(is_selected=True).count(), 1)

    def test_source_closed_candidate_must_be_24_hours_to_be_selected(self):
        self.prepare_closed_source()
        overnight = self.branch("Overnight Spa", "ON-01", self.area, self.group)
        always_open = self.branch("24 Hour Spa", "AO-01", self.area, self.group)
        self.add_hours(overnight, opens=time(10), closes=time(3))
        self.add_24_hours(always_open)

        request = RoutingService.process_call_log(self.call_log())

        selected = request.candidates.get(is_selected=True)
        overnight_candidate = request.candidates.get(branch=overnight)
        self.assertEqual(selected.branch, always_open)
        self.assertTrue(selected.is_open)
        self.assertTrue(selected.is_eligible)
        self.assertTrue(overnight_candidate.is_open)
        self.assertFalse(overnight_candidate.is_eligible)
        self.assertEqual(overnight_candidate.rejection_reason, "not_24_hours")

    def test_area_wise_recommends_only_24_hour_spa_town_vashi(self):
        vashi_source = self.branch("Customer Spa Vashi", "CSV-01", self.vashi, self.group)
        vashi_device = Device.objects.create(branch=vashi_source, device_id="routing-device-vashi", is_registered=True)
        self.add_hours(vashi_source, opens=time(10), closes=time(22))

        normal_spa_names = [
            "AVANTARA SPA VASHI",
            "CRYSTAL SPA VASHI",
            "OCEANIC SPA VASHI",
            "SPA BERRY VASHI",
            "THE SPA VASHI",
            "UNICORN SPA VASHI",
            "VIVA SPA VASHI",
        ]
        for index, name in enumerate(normal_spa_names, start=1):
            branch = self.branch(name, f"VASHI-{index:02d}", self.vashi, self.group)
            self.add_hours(branch, opens=time(10), closes=time(22))

        spa_town = self.branch("SPA TOWN VASHI", "VASHI-24", self.vashi, self.group)
        spa_town.phone = "+91 91164 58453"
        spa_town.shared_link = "https://maps.app.goo.gl/caUwXA6orHxycRMv6"
        spa_town.save(update_fields=["phone", "shared_link"])
        self.add_24_hours(spa_town)

        call_log = CallLog.objects.create(
            branch=vashi_source,
            device=vashi_device,
            phone_number="9876543210",
            call_type="incoming",
            duration=30,
            sim_slot=1,
            call_time=self.aware(hour=23, minute=30),
            call_hash="vashi-24-only",
        )

        request = RoutingService.process_call_log(call_log)

        selected = list(request.candidates.filter(is_selected=True).order_by("rank"))
        self.assertEqual(request.status, RoutingRequest.Status.ROUTED)
        self.assertEqual([candidate.branch for candidate in selected], [spa_town])
        self.assertFalse(request.candidates.exclude(branch=spa_town).filter(is_selected=True).exists())

    def test_candidate_closed_is_recorded_and_not_selected(self):
        self.prepare_closed_source()
        self.branch("Closed Candidate", "CL-01", self.area, self.group)

        request = RoutingService.process_call_log(self.call_log())

        candidate = request.candidates.get()
        self.assertFalse(candidate.is_open)
        self.assertFalse(candidate.is_selected)
        self.assertEqual(candidate.rejection_reason, "closed")
        self.assertEqual(request.status, RoutingRequest.Status.SKIPPED)
        self.assertEqual(request.rejection_reason, RoutingRequest.RejectionReason.NO_CANDIDATE)

    def test_inactive_and_source_branch_are_excluded(self):
        self.prepare_closed_source()
        inactive = self.branch("Inactive Spa", "IN-01", self.area, self.group, active=False)
        open_candidate = self.branch("Open Spa", "OP-01", self.area, self.group)
        self.add_24_hours(inactive)
        self.add_24_hours(open_candidate)

        request = RoutingService.process_call_log(self.call_log())

        candidate_branches = set(request.candidates.values_list("branch_id", flat=True))
        self.assertIn(open_candidate.id, candidate_branches)
        self.assertNotIn(inactive.id, candidate_branches)
        self.assertNotIn(self.source.id, candidate_branches)

    def test_candidate_discovery_by_same_group_same_city_and_coverage(self):
        self.prepare_closed_source()
        same_group = self.branch("Same Group", "SG-01", self.vashi, self.group)
        same_city = self.branch("Same City", "SC-01", self.vashi, None)
        coverage_branch = self.branch("Coverage", "CV-01", self.other_area, None)
        for branch in [same_group, same_city, coverage_branch]:
            self.add_24_hours(branch)

        branch_ct = ContentType.objects.get_for_model(Branch)
        BranchCoverageArea.objects.create(content_type=branch_ct, object_id=str(self.source.id), area=self.area)
        BranchCoverageArea.objects.create(content_type=branch_ct, object_id=str(coverage_branch.id), area=self.area)

        request = RoutingService.process_call_log(self.call_log())
        candidate_ids = set(request.candidates.values_list("branch_id", flat=True))

        self.assertIn(same_group.id, candidate_ids)
        self.assertIn(same_city.id, candidate_ids)
        self.assertIn(coverage_branch.id, candidate_ids)

    def test_ranking_and_top_n_are_deterministic(self):
        self.rule.max_recommendations = 2
        self.rule.save(update_fields=["max_recommendations"])
        self.prepare_closed_source()
        same_area = self.branch("Same Area", "B-01", self.area, self.group)
        tie_one = self.branch("Tie One", "A-01", self.vashi, self.group)
        tie_two = self.branch("Tie Two", "A-02", self.vashi, self.group)
        for branch in [same_area, tie_one, tie_two]:
            self.add_24_hours(branch)

        request = RoutingService.process_call_log(self.call_log())
        selected = list(request.candidates.filter(is_selected=True).order_by("rank"))

        self.assertEqual([item.branch for item in selected], [same_area, tie_one])
        self.assertEqual([item.rank for item in selected], [1, 2])

    def test_cooldown_blocks_second_call_with_same_canonical_phone(self):
        self.prepare_closed_source()
        candidate = self.branch("Green View Spa", "GV-01", self.area, self.group)
        self.add_24_hours(candidate)
        self.add_24_hours(candidate, weekday=BranchOperatingHours.Weekday.TUESDAY)

        first = RoutingService.process_call_log(self.call_log(phone="9876543210", call_hash="cooldown-1"))
        second = RoutingService.process_call_log(
            self.call_log(phone="+91 98765 43210", at_datetime=self.aware(hour=23, minute=45), call_hash="cooldown-2")
        )
        third = RoutingService.process_call_log(
            self.call_log(phone="919876543210", at_datetime=self.aware(day=11, hour=0, minute=45), call_hash="cooldown-3")
        )

        self.assertEqual(first.status, RoutingRequest.Status.ROUTED)
        self.assertEqual(second.status, RoutingRequest.Status.SKIPPED)
        self.assertEqual(second.rejection_reason, RoutingRequest.RejectionReason.CUSTOMER_COOLDOWN)
        self.assertEqual(third.status, RoutingRequest.Status.ROUTED)

    def test_same_call_log_processing_is_idempotent(self):
        self.prepare_closed_source()
        candidate = self.branch("Green View Spa", "GV-01", self.area, self.group)
        self.add_24_hours(candidate)
        call_log = self.call_log()

        first = RoutingService.process_call_log(call_log)
        second = RoutingService.process_call_log(call_log)

        self.assertEqual(first.id, second.id)
        self.assertEqual(RoutingRequest.objects.filter(call_log=call_log).count(), 1)
        self.assertEqual(first.candidates.count(), 1)
        self.assertEqual(first.events.count(), second.events.count())

    def test_existing_non_terminal_request_is_reprocessed_without_duplicate_candidates(self):
        self.prepare_closed_source()
        candidate = self.branch("Green View Spa", "GV-01", self.area, self.group)
        self.add_24_hours(candidate)
        call_log = self.call_log()
        request = RoutingRequest.objects.create(call_log=call_log, status=RoutingRequest.Status.PENDING)

        processed = RoutingService.process_call_log(call_log)

        self.assertEqual(processed.id, request.id)
        self.assertEqual(processed.candidates.filter(branch=candidate).count(), 1)
        self.assertEqual(processed.attempts.count(), 1)

    def test_lead_is_attached_when_available_and_missing_lead_is_allowed(self):
        self.prepare_closed_source()
        candidate = self.branch("Green View Spa", "GV-01", self.area, self.group)
        self.add_24_hours(candidate)
        with_lead_log = self.call_log(call_hash="lead-1")
        lead = LeadManagement.objects.create(calllog=with_lead_log, branch=self.source)
        without_lead_log = self.call_log(phone="9876543211", call_hash="lead-2")

        with_lead = RoutingService.process_call_log(with_lead_log)
        without_lead = RoutingService.process_call_log(without_lead_log)

        self.assertEqual(with_lead.lead, lead)
        self.assertIsNone(without_lead.lead)

    def test_failure_marks_routing_failed_without_touching_call_log(self):
        call_log = self.call_log()
        original_hash = call_log.call_hash

        with patch("apps.callrouting.services.PhoneNormalizationService.normalize", side_effect=RuntimeError("boom")), patch(
            "apps.callrouting.services.logger.exception"
        ):
            request = RoutingService.process_call_log(call_log)

        call_log.refresh_from_db()
        self.assertEqual(call_log.call_hash, original_hash)
        self.assertEqual(request.status, RoutingRequest.Status.FAILED)
        self.assertEqual(request.rejection_reason, RoutingRequest.RejectionReason.ERROR)
        self.assertTrue(request.events.filter(event_type="error").exists())

    def test_routing_task_fetches_call_log_and_processes(self):
        self.prepare_closed_source()
        candidate = self.branch("Green View Spa", "GV-01", self.area, self.group)
        self.add_24_hours(candidate)
        call_log = self.call_log(call_hash="task-process-1")

        result = process_call_log_routing(str(call_log.id))

        self.assertEqual(result["call_log_id"], str(call_log.id))
        self.assertEqual(result["status"], RoutingRequest.Status.ROUTED)
        self.assertTrue(RoutingRequest.objects.filter(call_log=call_log).exists())

    def test_routing_task_called_twice_remains_idempotent(self):
        self.prepare_closed_source()
        candidate = self.branch("Green View Spa", "GV-01", self.area, self.group)
        self.add_24_hours(candidate)
        call_log = self.call_log(call_hash="task-idempotent-1")

        first = process_call_log_routing(str(call_log.id))
        second = process_call_log_routing(str(call_log.id))

        self.assertEqual(first["routing_request_id"], second["routing_request_id"])
        self.assertEqual(RoutingRequest.objects.filter(call_log=call_log).count(), 1)
        self.assertEqual(RoutingCandidate.objects.filter(routing_request__call_log=call_log).count(), 1)

    def test_routing_task_failure_does_not_modify_call_log(self):
        call_log = self.call_log(call_hash="task-failure-1")
        original_hash = call_log.call_hash

        with patch("apps.callrouting.tasks.RoutingService.process_call_log", side_effect=RuntimeError("task boom")), patch(
            "apps.callrouting.tasks.logger.exception"
        ):
            with self.assertRaises(RuntimeError):
                process_call_log_routing(str(call_log.id))

        call_log.refresh_from_db()
        self.assertEqual(call_log.call_hash, original_hash)


class RoutingWhatsAppOrchestrationTests(RoutingEngineTests):
    def setUp(self):
        super().setUp()
        self.rule.template_name = "night_spa_recommendation"
        self.rule.template_language = "en"
        self.rule.save(update_fields=["template_name", "template_language"])

    def routed_request(self, selected_count=1):
        self.prepare_closed_source()
        candidates = []
        for index in range(selected_count):
            area = self.area if index == 0 else self.vashi
            branch = self.branch(f"Selected Spa {index + 1}", f"SEL-0{index + 1}", area, self.group)
            branch.phone = f"900000000{index + 1}"
            branch.shared_link = f"https://maps.app.goo.gl/selected{index + 1}"
            branch.save(update_fields=["phone", "shared_link"])
            self.add_24_hours(branch)
            candidates.append(branch)
        call_log = self.call_log(call_hash=f"wa-routing-{selected_count}", phone="9876543210")
        request = RoutingService.process_call_log(call_log)
        self.assertEqual(request.status, RoutingRequest.Status.ROUTED)
        return request, candidates

    def test_template_data_uses_source_and_selected_branch_data(self):
        request, candidates = self.routed_request(selected_count=2)
        data = RoutingTemplateDataBuilder.build(request)

        self.assertEqual(data["source_spa_name"], "Royal Oak Spa")
        self.assertEqual(data["source_spa_location"], "Sanpada, Navi Mumbai")
        self.assertEqual(len(data["recommendations"]), 2)
        self.assertEqual(data["recommendations"][0]["spa_name"], candidates[0].spa_name)
        self.assertEqual(data["recommendations"][0]["phone"], candidates[0].phone)
        self.assertEqual(data["recommendations"][0]["open_until"], "24 by 7 open hr")
        self.assertEqual(data["recommendations"][0]["details_url"], candidates[0].shared_link)
        self.assertEqual(data["template_variables"][0], "Customer")
        self.assertEqual(data["template_variables"][1], "Royal Oak Spa")
        self.assertIn("*Selected Spa 1*", data["template_variables"][2])
        self.assertIn("Open Status: *24 by 7 open hr*", data["template_variables"][2])
        self.assertIn("Phone: *9000000001*", data["template_variables"][2])
        self.assertIn("Map Link: *https://maps.app.goo.gl/selected1*", data["template_variables"][2])

    def test_template_data_does_not_fabricate_details_url_when_link_missing(self):
        request, candidates = self.routed_request(selected_count=1)
        candidates[0].shared_link = ""
        candidates[0].save(update_fields=["shared_link"])

        data = RoutingTemplateDataBuilder.build(request)

        self.assertEqual(data["recommendations"][0]["details_url"], "")
        self.assertNotIn("Map Link:", data["template_variables"][2])

    def test_template_data_uses_only_selected_eligible_candidates(self):
        request, candidates = self.routed_request(selected_count=1)
        rejected = self.branch("Rejected Spa", "REJ-01", self.area, self.group)
        self.add_hours(rejected)
        RoutingCandidate.objects.create(
            routing_request=request,
            branch=rejected,
            rank=2,
            relevance_score=999,
            is_open=True,
            is_eligible=False,
            is_selected=True,
            rejection_reason="test_rejected",
            evaluated_at=timezone.now(),
        )

        data = RoutingTemplateDataBuilder.build(request)

        self.assertIn(candidates[0].spa_name, data["template_variables"][2])
        self.assertNotIn("Rejected Spa", data["template_variables"][2])

    def test_template_data_uses_contact_name_when_available(self):
        request, _ = self.routed_request(selected_count=1)
        contact = Contact.objects.create(name="Priya Customer", phone_number="9876543210")
        request.contact = contact
        request.call_log.contact = contact
        request.call_log.save(update_fields=["contact"])
        request.save(update_fields=["contact", "updated_at"])

        data = RoutingTemplateDataBuilder.build(request)

        self.assertEqual(data["template_variables"][0], "Priya Customer")

    def test_template_data_does_not_fabricate_open_until_when_hours_missing(self):
        request, candidates = self.routed_request(selected_count=1)
        BranchOperatingHours.objects.filter(branch=candidates[0]).delete()

        data = RoutingTemplateDataBuilder.build(request)

        self.assertEqual(data["recommendations"], [])
        self.assertEqual(data["formatted_recommendations"], "")

    @override_settings(CALL_ROUTING_DRY_RUN=True)
    def test_dry_run_creates_queued_routing_whatsapp_message(self):
        request, _ = self.routed_request(selected_count=1)

        message = RoutingWhatsAppService.prepare_for_request(request)

        self.assertEqual(message.status, RoutingWhatsAppMessage.Status.QUEUED)
        self.assertEqual(message.recipient_phone, "+919876543210")
        self.assertEqual(message.template_name, "night_spa_recommendation")
        self.assertTrue(message.queued_at)
        self.assertEqual(message.template_payload["source_spa_name"], "Royal Oak Spa")
        self.assertTrue(request.events.filter(event_type=RoutingEvent.EventType.WHATSAPP_QUEUED).exists())
        str(message.template_payload).encode("ascii")

    @override_settings(CALL_ROUTING_DRY_RUN=True)
    def test_duplicate_prepare_does_not_create_second_message(self):
        request, _ = self.routed_request(selected_count=1)

        first = RoutingWhatsAppService.prepare_for_request(request)
        second = RoutingWhatsAppService.prepare_for_request(request)

        self.assertEqual(first.id, second.id)
        self.assertEqual(request.whatsapp_messages.count(), 1)

    @override_settings(CALL_ROUTING_DRY_RUN=True, CALL_ROUTING_WHATSAPP_RECIPIENT_COOLDOWN_HOURS=24)
    def test_same_recipient_is_not_sent_multiple_routing_whatsapps_within_24_hours(self):
        request, candidates = self.routed_request(selected_count=1)
        self.add_24_hours(candidates[0], weekday=BranchOperatingHours.Weekday.TUESDAY)
        first = RoutingWhatsAppService.prepare_for_request(request)

        second_call_log = self.call_log(
            phone="919876543210",
            at_datetime=self.aware(day=11, hour=1, minute=30),
            call_hash="wa-routing-duplicate-recipient",
        )
        second_request = RoutingService.process_call_log(second_call_log)

        second = RoutingWhatsAppService.prepare_for_request(second_request)

        self.assertEqual(first.status, RoutingWhatsAppMessage.Status.QUEUED)
        self.assertEqual(second_request.status, RoutingRequest.Status.ROUTED)
        self.assertEqual(second.status, RoutingWhatsAppMessage.Status.CANCELLED)
        self.assertEqual(second.failure_reason, "DUPLICATE_RECIPIENT_24H")
        self.assertEqual(RoutingWhatsAppMessage.objects.filter(recipient_phone="+919876543210").count(), 2)

    @override_settings(CALL_ROUTING_DRY_RUN=True, CALL_ROUTING_WHATSAPP_RECIPIENT_COOLDOWN_HOURS=24)
    def test_same_recipient_can_send_again_after_24_hour_whatsapp_window(self):
        request, candidates = self.routed_request(selected_count=1)
        first = RoutingWhatsAppService.prepare_for_request(request)
        RoutingWhatsAppMessage.objects.filter(id=first.id).update(created_at=timezone.now() - timedelta(hours=25))
        second_call_time = self.aware(day=10, hour=23, minute=45)

        second_request = RoutingRequest.objects.create(
            call_log=self.call_log(phone="919876543210", at_datetime=second_call_time, call_hash="wa-routing-after-24h"),
            source_branch=self.source,
            call_time=second_call_time,
            routing_type=RoutingRule.RoutingType.NIGHT,
            routing_rule=self.rule,
            normalized_phone="+919876543210",
            status=RoutingRequest.Status.ROUTED,
        )
        RoutingCandidate.objects.create(
            routing_request=second_request,
            branch=candidates[0],
            rank=1,
            relevance_score=100,
            is_open=True,
            is_eligible=True,
            is_selected=True,
            evaluated_at=timezone.now(),
        )

        second = RoutingWhatsAppService.prepare_for_request(second_request)

        self.assertEqual(second.status, RoutingWhatsAppMessage.Status.QUEUED)
        self.assertNotEqual(first.id, second.id)

    @override_settings(CALL_ROUTING_DRY_RUN=True)
    def test_invalid_recipient_fails_without_provider_call(self):
        request, candidates = self.routed_request(selected_count=1)
        request.normalized_phone = ""
        request.call_log.phone_number = "12345"
        request.call_log.save(update_fields=["phone_number"])
        request.save(update_fields=["normalized_phone", "updated_at"])

        message = RoutingWhatsAppService.prepare_for_request(request)

        self.assertEqual(message.status, RoutingWhatsAppMessage.Status.FAILED)
        self.assertEqual(message.failure_reason, "INVALID_RECIPIENT")
        self.assertEqual(request.status, RoutingRequest.Status.ROUTED)

    @override_settings(CALL_ROUTING_DRY_RUN=False, ENABLE_CALL_ROUTING_WHATSAPP=False)
    def test_whatsapp_feature_flag_disabled_does_not_enqueue_send(self):
        request, _ = self.routed_request(selected_count=1)

        with patch("apps.callrouting.tasks.send_routing_whatsapp_message.apply_async") as apply_async:
            message = RoutingWhatsAppService.prepare_for_request(request)

        self.assertEqual(message.status, RoutingWhatsAppMessage.Status.QUEUED)
        apply_async.assert_not_called()
        request.refresh_from_db()
        self.assertEqual(request.status, RoutingRequest.Status.ROUTED)

    @override_settings(ENABLE_CALL_ROUTING=True, CALL_ROUTING_DRY_RUN=False, ENABLE_CALL_ROUTING_WHATSAPP=True)
    def test_prepare_enqueues_provider_send_when_enabled(self):
        request, _ = self.routed_request(selected_count=1)

        with patch("apps.callrouting.tasks.send_routing_whatsapp_message.apply_async") as apply_async:
            with self.captureOnCommitCallbacks(execute=True):
                message = RoutingWhatsAppService.prepare_for_request(request)

        self.assertEqual(message.status, RoutingWhatsAppMessage.Status.QUEUED)
        apply_async.assert_called_once()

    @override_settings(
        DOUBLETICK_API_KEY="test-key",
        DOUBLETICK_SEND_FROM_WABA_NUMBER="917506359139",
    )
    def test_send_task_success_saves_provider_id_and_doubletick_message(self):
        request, _ = self.routed_request(selected_count=1)
        message = RoutingWhatsAppService.prepare_for_request(request)

        provider_payload = {"status_code": 201, "body": {"status": "SENT", "messageId": "dt-123"}}
        with patch("apps.callrouting.tasks.DoubleTickTemplateProvider.send", return_value={"message_id": "dt-123", "provider_payload": provider_payload}):
            result = send_routing_whatsapp_message(str(message.id))

        message.refresh_from_db()
        self.assertEqual(result["status"], "sent")
        self.assertEqual(message.status, RoutingWhatsAppMessage.Status.SENT)
        self.assertEqual(message.provider_message_id, "dt-123")
        self.assertEqual(message.provider_payload, provider_payload)
        self.assertIsNotNone(message.doubletick_message)
        self.assertEqual(message.doubletick_message.message_id, "dt-123")

    @override_settings(
        DOUBLETICK_API_KEY="test-key",
        DOUBLETICK_SEND_FROM_WABA_NUMBER="917506359139",
    )
    def test_duplicate_send_task_does_not_send_again(self):
        request, _ = self.routed_request(selected_count=1)
        message = RoutingWhatsAppService.prepare_for_request(request)
        message.status = RoutingWhatsAppMessage.Status.SENT
        message.provider_message_id = "dt-existing"
        message.save(update_fields=["status", "provider_message_id", "updated_at"])

        with patch("apps.callrouting.tasks.DoubleTickTemplateProvider.send") as send:
            result = send_routing_whatsapp_message(str(message.id))

        self.assertEqual(result["status"], "already_sent")
        send.assert_not_called()

    def test_provider_payload_uses_confirmed_contract_and_message_id_response(self):
        captured = {}

        class Response:
            status = 201

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({"messageId": "dt-456"}).encode("utf-8")

        def fake_urlopen(request, timeout):
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            captured["authorization"] = request.headers["Authorization"]
            captured["accept"] = request.headers["Accept"]
            captured["timeout"] = timeout
            return Response()

        with override_settings(DOUBLETICK_API_KEY="test-key"), patch("urllib.request.urlopen", side_effect=fake_urlopen):
            result = DoubleTickTemplateProvider.send("+919876543210", "917506359139", ["Customer", "Royal Oak Spa", "Green View Spa"])

        self.assertEqual(result["message_id"], "dt-456")
        self.assertEqual(result["provider_payload"]["status_code"], 201)
        self.assertEqual(result["provider_payload"]["body"]["messageId"], "dt-456")
        self.assertEqual(captured["authorization"], "test-key")
        self.assertEqual(captured["accept"], "application/json")
        self.assertEqual(captured["payload"]["messages"][0]["to"], "919876543210")
        self.assertEqual(captured["payload"]["messages"][0]["from"], "917506359139")
        self.assertEqual(captured["payload"]["messages"][0]["content"]["templateName"], "night_spa_recommendation")
        self.assertEqual(captured["payload"]["messages"][0]["content"]["language"], "en")
        self.assertEqual(captured["payload"]["messages"][0]["content"]["templateData"]["body"]["placeholders"][0], "Customer")

    def test_provider_parses_nested_message_id_response(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({
                    "messages": [
                        {
                            "status": "ENQUEUED",
                            "recipient": "919876543210",
                            "messageId": "dt-nested-123",
                        }
                    ]
                }).encode("utf-8")

        with override_settings(DOUBLETICK_API_KEY="test-key"), patch("urllib.request.urlopen", return_value=Response()):
            result = DoubleTickTemplateProvider.send("+919876543210", "917506359139", ["Customer", "Royal Oak Spa", "Green View Spa"])

        self.assertEqual(result["message_id"], "dt-nested-123")
        self.assertEqual(result["provider_payload"]["body"]["messages"][0]["status"], "ENQUEUED")

    def test_provider_400_401_and_422_are_permanent(self):
        for status_code in [400, 401, 422]:
            error = urllib.error.HTTPError("url", status_code, "bad", {}, io.BytesIO(b'{"error":"bad"}'))
            with override_settings(DOUBLETICK_API_KEY="test-key"), patch("urllib.request.urlopen", side_effect=error):
                with self.assertRaises(DoubleTickPermanentError):
                    DoubleTickTemplateProvider.send("+919876543210", "917506359139", ["Customer", "Royal Oak Spa", "Green View Spa"])

    def test_provider_5xx_timeout_and_network_error_are_transient(self):
        error = urllib.error.HTTPError("url", 503, "down", {}, io.BytesIO(b'{"error":"down"}'))
        with override_settings(DOUBLETICK_API_KEY="test-key"), patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(DoubleTickTransientError):
                DoubleTickTemplateProvider.send("+919876543210", "917506359139", ["Customer", "Royal Oak Spa", "Green View Spa"])

        with override_settings(DOUBLETICK_API_KEY="test-key"), patch("urllib.request.urlopen", side_effect=TimeoutError("timeout")):
            with self.assertRaises(DoubleTickTransientError):
                DoubleTickTemplateProvider.send("+919876543210", "917506359139", ["Customer", "Royal Oak Spa", "Green View Spa"])

        with override_settings(DOUBLETICK_API_KEY="test-key"), patch("urllib.request.urlopen", side_effect=urllib.error.URLError("connection")):
            with self.assertRaises(DoubleTickTransientError):
                DoubleTickTemplateProvider.send("+919876543210", "917506359139", ["Customer", "Royal Oak Spa", "Green View Spa"])

    def test_provider_missing_message_id_is_permanent(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({"ok": True}).encode("utf-8")

        with override_settings(DOUBLETICK_API_KEY="test-key"), patch("urllib.request.urlopen", return_value=Response()):
            with self.assertRaises(DoubleTickPermanentError):
                DoubleTickTemplateProvider.send("+919876543210", "917506359139", ["Customer", "Royal Oak Spa", "Green View Spa"])

    @override_settings(CALL_ROUTING_DRY_RUN=True)
    def test_task_prepares_dry_run_message_after_routing(self):
        self.prepare_closed_source()
        candidate = self.branch("Green View Spa", "GV-01", self.area, self.group)
        self.add_24_hours(candidate)
        call_log = self.call_log(call_hash="wa-task-1")

        process_call_log_routing(str(call_log.id))

        request = RoutingRequest.objects.get(call_log=call_log)
        self.assertEqual(request.whatsapp_messages.count(), 1)
        self.assertEqual(request.whatsapp_messages.get().status, RoutingWhatsAppMessage.Status.QUEUED)

    def doubletick_message(self, provider_id="provider-1", status=DoubleTickMessage.Status.SENT):
        customer = DoubleTickCustomer.objects.create(normalized_phone="+919876543210", phone_number="+919876543210")
        conversation = DoubleTickConversation.objects.create(customer=customer)
        return DoubleTickMessage.objects.create(
            conversation=conversation,
            customer=customer,
            message_id=provider_id,
            dt_message_id=provider_id,
            direction=DoubleTickMessage.Direction.OUTBOUND,
            origin=DoubleTickMessage.Origin.API,
            status=status,
            sent_at=timezone.now() if status == DoubleTickMessage.Status.SENT else None,
            delivered_at=timezone.now() if status == DoubleTickMessage.Status.DELIVERED else None,
            read_at=timezone.now() if status == DoubleTickMessage.Status.READ else None,
            failed_at=timezone.now() if status == DoubleTickMessage.Status.FAILED else None,
            failure_reason="failed" if status == DoubleTickMessage.Status.FAILED else "",
        )

    @override_settings(CALL_ROUTING_DRY_RUN=True)
    def test_webhook_status_update_links_provider_message(self):
        request, _ = self.routed_request(selected_count=1)
        routing_message = RoutingWhatsAppService.prepare_for_request(request)
        routing_message.provider_message_id = "provider-1"
        routing_message.save(update_fields=["provider_message_id", "updated_at"])
        doubletick_message = self.doubletick_message(status=DoubleTickMessage.Status.DELIVERED)

        updated = RoutingWhatsAppWebhookService.sync_from_doubletick_message(doubletick_message)

        self.assertEqual(updated.status, RoutingWhatsAppMessage.Status.DELIVERED)
        self.assertEqual(updated.doubletick_message, doubletick_message)
        self.assertTrue(updated.delivered_at)

    def test_unmatched_provider_message_does_not_crash(self):
        doubletick_message = self.doubletick_message(provider_id="unmatched")

        self.assertIsNone(RoutingWhatsAppWebhookService.sync_from_doubletick_message(doubletick_message))
