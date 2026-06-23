from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import Area, City, LocationGroup, LocationGroupArea, State


class LocationGroupAreaSyncTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="locations-admin@example.com",
            password="pass",
            full_name="Locations Admin",
            role="admin",
            is_active=True,
        )
        self.client.force_authenticate(self.admin)
        self.state = State.objects.create(name="Maharashtra")
        self.city = City.objects.create(name="Navi Mumbai", state=self.state)
        self.other_city = City.objects.create(name="Mumbai", state=self.state)
        self.group = LocationGroup.objects.create(name="Panvel To Seawoods", city=self.city)
        self.panvel = Area.objects.create(name="Panvel", city=self.city)
        self.kharghar = Area.objects.create(name="Kharghar", city=self.city)
        self.belapur = Area.objects.create(name="Belapur", city=self.city)
        self.bandra = Area.objects.create(name="Bandra", city=self.other_city)

    def sync_url(self):
        return f"/api/v1/locations/groups/{self.group.id}/sync-areas/"

    def test_sync_areas_creates_mappings_and_ignores_duplicate_ids(self):
        response = self.client.post(
            self.sync_url(),
            {"area_ids": [str(self.panvel.id), str(self.kharghar.id), str(self.panvel.id)]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(LocationGroupArea.objects.filter(group=self.group, is_deleted=False).count(), 2)
        self.assertTrue(LocationGroupArea.objects.filter(group=self.group, area=self.panvel, is_deleted=False).exists())
        self.assertTrue(LocationGroupArea.objects.filter(group=self.group, area=self.kharghar, is_deleted=False).exists())
        self.assertEqual(response.data["area_count"], 2)

    def test_sync_areas_rejects_areas_from_another_city(self):
        response = self.client.post(
            self.sync_url(),
            {"area_ids": [str(self.panvel.id), str(self.bandra.id)]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Selected areas must belong to the same city", str(response.data))
        self.assertEqual(LocationGroupArea.objects.filter(group=self.group, is_deleted=False).count(), 0)

    def test_sync_areas_soft_removes_deselected_mappings_without_deleting_area(self):
        LocationGroupArea.objects.create(group=self.group, area=self.panvel)
        LocationGroupArea.objects.create(group=self.group, area=self.kharghar)

        response = self.client.post(
            self.sync_url(),
            {"area_ids": [str(self.kharghar.id), str(self.belapur.id)]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(LocationGroupArea.objects.filter(group=self.group, area=self.panvel, is_deleted=False).exists())
        self.assertTrue(LocationGroupArea.objects.filter(group=self.group, area=self.kharghar, is_deleted=False).exists())
        self.assertTrue(LocationGroupArea.objects.filter(group=self.group, area=self.belapur, is_deleted=False).exists())
        self.assertTrue(Area.objects.filter(id=self.panvel.id, is_deleted=False).exists())

    def test_compact_location_lists_omit_nested_payloads(self):
        LocationGroupArea.objects.create(group=self.group, area=self.panvel)

        city_response = self.client.get("/api/v1/locations/cities/", {"all": "true", "compact": "true"})
        area_response = self.client.get("/api/v1/locations/areas/", {"all": "true", "compact": "true"})
        group_response = self.client.get("/api/v1/locations/groups/", {"all": "true", "compact": "true"})

        self.assertEqual(city_response.status_code, status.HTTP_200_OK)
        self.assertEqual(area_response.status_code, status.HTTP_200_OK)
        self.assertEqual(group_response.status_code, status.HTTP_200_OK)

        self.assertNotIn("aliases", city_response.data[0])
        self.assertNotIn("state_detail", city_response.data[0])
        self.assertNotIn("aliases", area_response.data[0])
        self.assertNotIn("city_detail", area_response.data[0])
        self.assertNotIn("group_areas", group_response.data[0])
        self.assertNotIn("city_detail", group_response.data[0])
        self.assertIn("area_count", group_response.data[0])

    def test_location_options_endpoints_are_minimal_and_support_group_filter(self):
        LocationGroupArea.objects.create(group=self.group, area=self.belapur)

        state_options = self.client.get("/api/v1/locations/states/options/")
        city_options = self.client.get("/api/v1/locations/cities/options/", {"state_id": str(self.state.id)})
        group_options = self.client.get("/api/v1/locations/groups/options/", {"city_id": str(self.city.id)})
        area_options = self.client.get(
            "/api/v1/locations/areas/options/",
            {"city_id": str(self.city.id), "group": str(self.group.id)},
        )

        self.assertEqual(state_options.status_code, status.HTTP_200_OK)
        self.assertEqual(city_options.status_code, status.HTTP_200_OK)
        self.assertEqual(group_options.status_code, status.HTTP_200_OK)
        self.assertEqual(area_options.status_code, status.HTTP_200_OK)

        self.assertTrue(isinstance(state_options.data, list))
        self.assertTrue(isinstance(city_options.data, list))
        self.assertTrue(isinstance(group_options.data, list))
        self.assertTrue(isinstance(area_options.data, list))

        self.assertIn("id", state_options.data[0])
        self.assertIn("value", state_options.data[0])
        self.assertIn("label", state_options.data[0])
        self.assertIn("name", state_options.data[0])
        self.assertIn("is_active", state_options.data[0])
        self.assertNotIn("slug", state_options.data[0])
        self.assertNotIn("code", state_options.data[0])

        self.assertNotIn("aliases", city_options.data[0])
        self.assertNotIn("state_detail", city_options.data[0])
        self.assertNotIn("slug", city_options.data[0])

        self.assertNotIn("group_areas", group_options.data[0])
        self.assertNotIn("city_detail", group_options.data[0])
        self.assertNotIn("slug", group_options.data[0])

        self.assertEqual(len(area_options.data), 1)
        self.assertEqual(area_options.data[0]["id"], str(self.belapur.id))
        self.assertNotIn("aliases", area_options.data[0])
        self.assertNotIn("city_detail", area_options.data[0])
        self.assertNotIn("slug", area_options.data[0])
