from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class AuthAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="operator", password="Pc5-Secure-Pass!")
        self.login_url = reverse("auth-login")
        self.logout_url = reverse("auth-logout")
        self.me_url = reverse("auth-me")

    def test_me_when_anonymous(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["authenticated"])
        self.assertIn("csrftoken", response.cookies)

    def test_login_success_starts_session(self):
        response = self.client.post(self.login_url, {"username": "operator", "password": "Pc5-Secure-Pass!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], "operator")

        me = self.client.get(self.me_url)
        self.assertTrue(me.data["authenticated"])

    def test_login_wrong_password(self):
        response = self.client.post(self.login_url, {"username": "operator", "password": "wrong"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])

    def test_login_missing_fields(self):
        response = self.client.post(self.login_url, {"username": "operator"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_ends_session(self):
        self.client.force_login(self.user)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.client.get(self.me_url).data["authenticated"])

    def test_protected_endpoints_require_login(self):
        self.assertEqual(self.client.post(reverse("chat"), {"message": "hi"}, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(reverse("document-list")).status_code, status.HTTP_403_FORBIDDEN)

    def test_csrf_enforced_for_session_writes(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(reverse("chat"), {"message": "hi"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
