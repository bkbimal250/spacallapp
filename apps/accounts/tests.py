from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class LoginTestCase(APITestCase):
    """
    Test suite for User Login functionality.
    """

    def setUp(self):
        self.email = "dos.bimal@gmail.com"
        self.password = "Dos@2026"
        self.login_url = "/api/v1/auth/login/"

        # Create a test user
        self.user = User.objects.create_user(
            email=self.email,
            password=self.password,
            full_name="Bimal Dos",
            role="super_admin"
        )

    def test_login_success(self):
        """Test login with valid credentials."""
        data = {
            "email": self.email,
            "password": self.password
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Login successful")
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_password(self):
        """Test login with incorrect password."""
        data = {
            "email": self.email,
            "password": "WrongPassword123"
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_login_non_existent_user(self):
        """Test login with an email that doesn't exist."""
        data = {
            "email": "notfound@gmail.com",
            "password": self.password
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
