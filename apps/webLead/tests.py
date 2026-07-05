from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from apps.branches.models import Branch

from .analytics import overview, website_analytics
from .models import (
    WebsiteFormConfiguration,
    WebsiteLead,
    WebsiteLeadRoutingStatus,
    WebsiteLeadStatus,
)


class WebsiteLeadFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.branch = Branch.objects.create(
            spa_name="Auric Spa Vadodara",
            code="AURIC-VAD",
            state="Gujarat",
            city="Vadodara",
            area="Alkapuri",
            postal_code=390007,
            address="Alkapuri, Vadodara",
            is_active=True,
        )
        User = get_user_model()
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="pass123",
            full_name="Admin User",
            role="admin",
        )
        self.manager = User.objects.create_user(
            email="manager@example.com",
            password="pass123",
            full_name="Branch Manager",
            role="spa_manager",
            branch=self.branch,
        )

    _DEFAULT_BRANCH = object()

    def make_config(self, index, branch=_DEFAULT_BRANCH, is_active=True):
        return WebsiteFormConfiguration.objects.create(
            branch=self.branch if branch is self._DEFAULT_BRANCH else branch,
            website_name=f"Auric Website {index}",
            website_url=f"https://auric{index}.example.com",
            form_key=f"frm_auric_{index:06d}",
            is_active=is_active,
        )

    @patch("apps.webLead.services.send_website_lead_notification", return_value=True)
    def test_same_branch_can_have_many_website_forms_and_route_source_wise(self, _notify):
        configs = [self.make_config(i) for i in range(10)]

        for index, config in enumerate(configs):
            response = self.client.post(
                "/api/v1/web-leads/submit/",
                {
                    "form_key": config.form_key,
                    "name": f"Rahul {index}",
                    "phone": f"98765432{index:02d}",
                    "address": "Alkapuri",
                    "notes": "Today",
                },
                format="json",
            )
            self.assertEqual(response.status_code, 201)
            self.assertTrue(response.data["success"])

        leads = WebsiteLead.objects.order_by("website_name")
        self.assertEqual(leads.count(), 10)
        self.assertEqual(set(leads.values_list("branch_id", flat=True)), {self.branch.id})
        self.assertEqual(leads.values("website_name").distinct().count(), 10)
        self.assertEqual(leads.values("website_url").distinct().count(), 10)

        self.client.force_authenticate(self.manager)
        response = self.client.get("/api/v1/web-leads/leads/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 10)

        totals = overview(WebsiteLead.objects.all())
        self.assertEqual(totals["total_website_leads"], 10)
        self.assertEqual(len(website_analytics(WebsiteLead.objects.all())), 10)

    def test_public_config_exposes_safe_fields_only(self):
        config = self.make_config(1)
        response = self.client.get(f"/api/v1/web-leads/config/{config.form_key}/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("form_key", response.data)
        self.assertIn("website_name", response.data)
        self.assertNotIn("branch", response.data)
        self.assertNotIn("created_by", response.data)

    def test_address_and_notes_length_are_enforced(self):
        config = self.make_config(1)
        payload = {
            "form_key": config.form_key,
            "name": "Rahul",
            "phone": "9876543210",
            "address": "This address is too long",
            "notes": "Today",
        }
        response = self.client.post("/api/v1/web-leads/submit/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("address", response.data)

        payload["address"] = "Alkapuri"
        payload["notes"] = "This note is too long"
        response = self.client.post("/api/v1/web-leads/submit/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("notes", response.data)

    def test_invalid_and_inactive_form_key_reject_submission(self):
        response = self.client.post(
            "/api/v1/web-leads/submit/",
            {"form_key": "frm_missing_1234", "name": "Rahul", "phone": "9876543210", "address": "Alkapuri"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

        config = self.make_config(2, is_active=False)
        response = self.client.post(
            "/api/v1/web-leads/submit/",
            {"form_key": config.form_key, "name": "Rahul", "phone": "9876543210", "address": "Alkapuri"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("apps.webLead.services.send_website_lead_notification", return_value=True)
    def test_duplicate_same_form_is_marked_but_different_form_is_allowed(self, _notify):
        first = self.make_config(1)
        second = self.make_config(2)
        payload = {"name": "Rahul", "phone": "9876543210", "address": "Alkapuri"}

        for form_key in [first.form_key, first.form_key, second.form_key]:
            response = self.client.post(
                "/api/v1/web-leads/submit/",
                {**payload, "form_key": form_key},
                format="json",
            )
            self.assertEqual(response.status_code, 201)

        self.assertEqual(WebsiteLead.objects.count(), 3)
        self.assertEqual(
            WebsiteLead.objects.get(form_key=first.form_key, status=WebsiteLeadStatus.DUPLICATE).phone,
            "9876543210",
        )
        self.assertEqual(
            WebsiteLead.objects.filter(form_key=second.form_key, status=WebsiteLeadStatus.NEW).count(),
            1,
        )

    def test_pending_unassigned_fallback_when_branch_missing(self):
        config = self.make_config(1, branch=None)
        response = self.client.post(
            "/api/v1/web-leads/submit/",
            {"form_key": config.form_key, "name": "Rahul", "phone": "9876543210", "address": "Alkapuri"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        lead = WebsiteLead.objects.get()
        self.assertIsNone(lead.branch)
        self.assertEqual(lead.routing_status, WebsiteLeadRoutingStatus.PENDING_CONFIGURATION)

    @patch("apps.webLead.services.send_website_lead_notification", return_value=True)
    def test_branch_user_cannot_see_other_branch_leads(self, _notify):
        other_branch = Branch.objects.create(
            spa_name="Other Spa",
            code="OTHER",
            state="Gujarat",
            city="Vadodara",
            area="Gotri",
            postal_code=390021,
            address="Gotri",
            is_active=True,
        )
        own_config = self.make_config(1)
        other_config = self.make_config(2, branch=other_branch)

        for config in [own_config, other_config]:
            response = self.client.post(
                "/api/v1/web-leads/submit/",
                {"form_key": config.form_key, "name": "Rahul", "phone": "9876543210", "address": "Alkapuri"},
                format="json",
            )
            self.assertEqual(response.status_code, 201)

        self.client.force_authenticate(self.manager)
        response = self.client.get("/api/v1/web-leads/leads/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(str(response.data["results"][0]["branch"]), str(self.branch.id))
