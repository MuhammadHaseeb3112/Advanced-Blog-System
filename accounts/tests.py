import re

from django.core import mail
from django.test import TestCase

from accounts.models import CustomUser
from blog.tests.factories import make_user


class SignupAndActivationTests(TestCase):
    def signup(self):
        return self.client.post(
            "/accounts/signup/",
            {
                "username": "newwriter",
                "email": "new@example.com",
                "password1": "Str0ng-pass-123",
                "password2": "Str0ng-pass-123",
            },
        )

    def activation_link(self):
        return re.search(r"/accounts/activate/[^/]+/[^/\"']+/", mail.outbox[0].body).group(0)

    def test_signup_creates_inactive_user_and_sends_email(self):
        response = self.signup()
        self.assertEqual(response.status_code, 200)
        user = CustomUser.objects.get(email="new@example.com")
        self.assertFalse(user.is_active)
        self.assertFalse(user.email_verified)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["new@example.com"])

    def test_activation_link_activates_and_sends_welcome_email(self):
        self.signup()
        self.client.get(self.activation_link())
        user = CustomUser.objects.get(email="new@example.com")
        self.assertTrue(user.is_active)
        self.assertTrue(user.email_verified)
        self.assertEqual(len(mail.outbox), 2)  # activation + welcome (Celery task)

    def test_bad_activation_token_is_rejected(self):
        self.signup()
        user = CustomUser.objects.get(email="new@example.com")
        link = self.activation_link().rsplit("/", 2)[0] + "/wrong-token/"
        self.client.get(link)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_duplicate_email_is_rejected(self):
        make_user(email="new@example.com")
        self.signup()
        self.assertEqual(CustomUser.objects.filter(email="new@example.com").count(), 1)


class LoginTests(TestCase):
    def test_login_with_email(self):
        make_user(email="writer@example.com", password="pass12345!")
        response = self.client.post(
            "/accounts/login/", {"username": "writer@example.com", "password": "pass12345!"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_wrong_password_fails(self):
        make_user(email="writer@example.com", password="pass12345!")
        self.client.post("/accounts/login/", {"username": "writer@example.com", "password": "nope"})
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_password_reset_sends_email(self):
        make_user(email="forgot@example.com")
        self.client.post("/accounts/password-reset/", {"email": "forgot@example.com"})
        self.assertEqual(len(mail.outbox), 1)
