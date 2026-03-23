from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

User = get_user_model()


class UserAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="harsh@example.com",
            password="wapxj380",
            role=User.Role.ADMIN,
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="password123",
            role=User.Role.DESIGNER,
        )
        self.token = Token.objects.create(user=self.user)
        self.list_url = reverse("user-list")
        self.login_url = reverse("auth-login")

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_create_user_signup(self):
        payload = {
            "email": "newuser@example.com",
            "password": "strongpass123",
            "role": User.Role.ACCOUNT_PLANNER,
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_login_with_email_and_password(self):
        payload = {
            "email": "harsh@example.com",
            "password": "wapxj380",
        }
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["email"], "harsh@example.com")

    def test_login_invalid_credentials(self):
        payload = {
            "email": "harsh@example.com",
            "password": "wrong-password",
        }
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_requires_auth(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_users_authenticated(self):
        self.authenticate()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_retrieve_self_allowed(self):
        self.authenticate()
        response = self.client.get(reverse("user-detail", args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "harsh@example.com")

    def test_retrieve_other_forbidden(self):
        self.authenticate()
        response = self.client.get(reverse("user-detail", args=[self.other_user.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_self(self):
        self.authenticate()
        payload = {"first_name": "Harsh", "last_name": "Jain"}
        response = self.client.patch(reverse("user-detail", args=[self.user.id]), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Harsh")

    def test_delete_self(self):
        self.authenticate()
        response = self.client.delete(reverse("user-detail", args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.user.id).exists())
