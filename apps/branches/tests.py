from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import User
from apps.branches.models import Branch, BranchGroups

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
