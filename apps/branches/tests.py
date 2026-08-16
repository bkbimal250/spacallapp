from django.urls import reverse
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, time
from zoneinfo import ZoneInfo
from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import User
from apps.branches.models import Branch, BranchGroups, BranchOperatingHours
from apps.branches.services import BranchOperatingHoursService

class BranchAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="Password123",
            role="admin"
        )
        self.group = BranchGroups.objects.create(name="Test Group")
        self.branch = Branch.objects.create(
            spa_name="Test Branch",
            code="TB-01",
            city="Pune",
            state="Maharashtra",
            postal_code=411001,
            branch_group=self.group
        )
        self.client.force_authenticate(user=self.user)

    def test_list_branches_optimized(self):
        url = reverse('branch-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify essential fields are present
        results = response.data['results']
        self.assertTrue(len(results) > 0)
        branch_data = results[0]
        self.assertIn('spa_name', branch_data)
        self.assertIn('branch_group_name', branch_data)
        self.assertEqual(branch_data['branch_group_name'], self.group.name)
        
        # Test caching
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, response2.data)

    def test_branch_create_update_exposes_phone_and_shared_link(self):
        url = reverse("branch-list")
        payload = {
            "spa_name": "Map Spa",
            "code": "MAP-01",
            "state": "Maharashtra",
            "city": "Mumbai",
            "area": "Bandra",
            "postal_code": 400050,
            "address": "Map Address",
            "phone": "+919000000001",
            "shared_link": "https://maps.app.goo.gl/testbranch",
        }

        create_response = self.client.post(url, payload, format="json")

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["phone"], payload["phone"])
        self.assertEqual(create_response.data["shared_link"], payload["shared_link"])

        detail_url = reverse("branch-detail", kwargs={"pk": create_response.data["id"]})
        update_response = self.client.patch(
            detail_url,
            {"shared_link": "https://maps.app.goo.gl/updatedbranch"},
            format="json",
        )

        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data["shared_link"], "https://maps.app.goo.gl/updatedbranch")

    def test_open_24_hours_filter_uses_operating_hours(self):
        branch_24 = Branch.objects.create(
            spa_name="Always Open Spa",
            code="OPEN-24",
            city="Pune",
            state="Maharashtra",
            postal_code=411002,
            address="Always Open Address",
        )
        BranchOperatingHours.objects.create(
            branch=branch_24,
            weekday=BranchOperatingHours.Weekday.MONDAY,
            is_24_hours=True,
            timezone="Asia/Kolkata",
        )

        response = self.client.get(reverse("branch-list"), {"open_24_hours": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        codes = {row["code"] for row in response.data["results"]}
        self.assertIn("OPEN-24", codes)
        self.assertNotIn(self.branch.code, codes)

    def test_weekly_operating_hours_supports_overnight_closed_and_24_hour(self):
        url = reverse("branch-operating-hours", kwargs={"pk": self.branch.id})
        payload = {
            "timezone": "Asia/Kolkata",
            "operating_hours": [
                {"weekday": 0, "is_closed": False, "is_24_hours": False, "opens_at": "10:00", "closes_at": "03:00", "timezone": "Asia/Kolkata"},
                {"weekday": 1, "is_closed": True, "is_24_hours": False, "opens_at": None, "closes_at": None, "timezone": "Asia/Kolkata"},
                {"weekday": 2, "is_closed": False, "is_24_hours": True, "opens_at": None, "closes_at": None, "timezone": "Asia/Kolkata"},
                {"weekday": 3, "is_closed": False, "is_24_hours": False, "opens_at": "10:00", "closes_at": "22:00", "timezone": "Asia/Kolkata"},
                {"weekday": 4, "is_closed": False, "is_24_hours": False, "opens_at": "10:00", "closes_at": "22:00", "timezone": "Asia/Kolkata"},
                {"weekday": 5, "is_closed": False, "is_24_hours": False, "opens_at": "10:00", "closes_at": "22:00", "timezone": "Asia/Kolkata"},
                {"weekday": 6, "is_closed": False, "is_24_hours": False, "opens_at": "10:00", "closes_at": "22:00", "timezone": "Asia/Kolkata"},
            ],
        }

        response = self.client.put(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        monday = response.data["operating_hours"][0]
        tuesday = response.data["operating_hours"][1]
        wednesday = response.data["operating_hours"][2]
        self.assertTrue(monday["is_overnight"])
        self.assertTrue(tuesday["is_closed"])
        self.assertIsNone(tuesday["opens_at"])
        self.assertTrue(wednesday["is_24_hours"])
        self.assertEqual(response.data["timezone"], "Asia/Kolkata")

    def test_weekly_operating_hours_put_creates_then_updates_schedule(self):
        url = reverse("branch-operating-hours", kwargs={"pk": self.branch.id})
        rows = [
            {"weekday": weekday, "is_closed": False, "is_24_hours": False, "opens_at": "10:00", "closes_at": "22:00", "timezone": "Asia/Kolkata"}
            for weekday in range(7)
        ]

        create_response = self.client.put(url, {"timezone": "Asia/Kolkata", "operating_hours": rows}, format="json")
        rows[0]["closes_at"] = "03:00"
        update_response = self.client.put(url, {"timezone": "Asia/Kolkata", "operating_hours": rows}, format="json")

        self.assertEqual(create_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(BranchOperatingHours.objects.filter(branch=self.branch).count(), 7)
        self.assertTrue(update_response.data["operating_hours"][0]["is_overnight"])

    def test_weekly_operating_hours_rejects_equal_open_close_times(self):
        url = reverse("branch-operating-hours", kwargs={"pk": self.branch.id})
        rows = [
            {"weekday": weekday, "is_closed": False, "is_24_hours": False, "opens_at": "10:00", "closes_at": "22:00", "timezone": "Asia/Kolkata"}
            for weekday in range(7)
        ]
        rows[0]["closes_at"] = "10:00"

        response = self.client.put(url, {"timezone": "Asia/Kolkata", "operating_hours": rows}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(BranchOperatingHours.objects.filter(branch=self.branch).exists())

    def test_spa_manager_can_view_but_not_update_operating_hours(self):
        spa_manager = User.objects.create_user(
            email="spa-hours@example.com",
            password="Password123",
            full_name="Spa Manager",
            role="spa_manager",
            branch=self.branch,
        )
        self.client.force_authenticate(spa_manager)
        url = reverse("branch-operating-hours", kwargs={"pk": self.branch.id})

        read_response = self.client.get(url)
        write_response = self.client.put(url, {"timezone": "Asia/Kolkata", "operating_hours": []}, format="json")

        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.assertEqual(write_response.status_code, status.HTTP_403_FORBIDDEN)


class BranchOperatingHoursServiceTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            spa_name="Night Spa",
            code="NS-01",
            city="Navi Mumbai",
            state="Maharashtra",
            postal_code=400001,
            address="Test Address",
            is_active=True,
        )
        self.tz = ZoneInfo("Asia/Kolkata")

    def aware(self, year, month, day, hour, minute=0):
        return timezone.make_aware(datetime(year, month, day, hour, minute), self.tz)

    def test_missing_hours_is_closed(self):
        self.assertFalse(BranchOperatingHoursService.is_branch_open(self.branch, self.aware(2026, 8, 10, 12)))

    def test_normal_same_day_hours(self):
        BranchOperatingHours.objects.create(
            branch=self.branch,
            weekday=BranchOperatingHours.Weekday.MONDAY,
            opens_at=time(10, 0),
            closes_at=time(22, 0),
            timezone="Asia/Kolkata",
        )

        self.assertTrue(BranchOperatingHoursService.is_branch_open(self.branch, self.aware(2026, 8, 10, 11)))
        self.assertFalse(BranchOperatingHoursService.is_branch_open(self.branch, self.aware(2026, 8, 10, 23)))

    def test_overnight_hours_span_midnight(self):
        BranchOperatingHours.objects.create(
            branch=self.branch,
            weekday=BranchOperatingHours.Weekday.MONDAY,
            opens_at=time(10, 0),
            closes_at=time(3, 0),
            timezone="Asia/Kolkata",
        )

        self.assertTrue(BranchOperatingHoursService.is_branch_open(self.branch, self.aware(2026, 8, 10, 23, 30)))
        self.assertTrue(BranchOperatingHoursService.is_branch_open(self.branch, self.aware(2026, 8, 11, 1, 0)))
        self.assertTrue(BranchOperatingHoursService.is_branch_open(self.branch, self.aware(2026, 8, 11, 2, 30)))
        self.assertFalse(BranchOperatingHoursService.is_branch_open(self.branch, self.aware(2026, 8, 11, 3, 30)))

    def test_24_hour_branch_is_open_for_configured_day(self):
        BranchOperatingHours.objects.create(
            branch=self.branch,
            weekday=BranchOperatingHours.Weekday.WEDNESDAY,
            is_24_hours=True,
            timezone="Asia/Kolkata",
        )

        self.assertTrue(BranchOperatingHoursService.is_branch_open(self.branch, self.aware(2026, 8, 12, 4)))
        self.assertFalse(BranchOperatingHoursService.is_branch_open(self.branch, self.aware(2026, 8, 13, 4)))

    def test_closed_day_is_not_open(self):
        BranchOperatingHours.objects.create(
            branch=self.branch,
            weekday=BranchOperatingHours.Weekday.FRIDAY,
            is_closed=True,
            timezone="Asia/Kolkata",
        )

        self.assertFalse(BranchOperatingHoursService.is_branch_open(self.branch, self.aware(2026, 8, 14, 12)))
