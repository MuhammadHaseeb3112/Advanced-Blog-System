from django.test import TestCase, override_settings

from .factories import make_user


@override_settings(DEMO_MODE=True)
class DemoModeTests(TestCase):
    def test_login_page_offers_one_click_demo_accounts(self):
        response = self.client.get("/accounts/login/")
        self.assertContains(response, "sara@demo.blog")
        self.assertContains(response, "reader@demo.blog")

    def test_demo_button_signs_in(self):
        make_user(email="sara@demo.blog", password="DemoPass123!", role="author")
        self.client.post("/accounts/login/", {"username": "sara@demo.blog", "password": "DemoPass123!"})
        self.assertIn("_auth_user_id", self.client.session)

    def test_signup_and_admin_are_blocked(self):
        self.assertRedirects(self.client.get("/accounts/signup/"), "/accounts/login/",
                             fetch_redirect_response=False)
        self.assertEqual(self.client.get("/admin/").status_code, 302)

    def test_profile_changes_are_blocked(self):
        user = make_user(username="sara")
        self.client.force_login(user)
        self.client.post("/profile/", {"username": "changed", "email": "x@example.com"})
        user.refresh_from_db()
        self.assertEqual(user.username, "sara")

    def test_api_registration_is_blocked(self):
        response = self.client.post(
            "/api/register/", {"username": "a", "email": "a@example.com", "password": "pass12345!"}
        )
        self.assertEqual(response.status_code, 403)

    def test_writing_posts_still_works(self):
        self.client.force_login(make_user(role="author"))
        self.client.post("/create-post/", {"title": "Demo post", "content": "x", "status": "published"})
        self.assertTrue(self.client.get("/my-posts/").content.count(b"Demo post"))


class NormalModeTests(TestCase):
    def test_login_page_has_no_demo_box_and_signup_is_open(self):
        self.assertNotContains(self.client.get("/accounts/login/"), "demo-btn")
        self.assertEqual(self.client.get("/accounts/signup/").status_code, 200)
