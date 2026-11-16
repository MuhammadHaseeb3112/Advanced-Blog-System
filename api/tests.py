from django.core import mail
from rest_framework.test import APITestCase

from blog.models import BlogPost, Comment
from blog.tests.factories import make_category, make_post, make_user


class AuthApiTests(APITestCase):
    def test_register_sends_verification_email(self):
        response = self.client.post(
            "/api/register/",
            {"username": "apiuser", "email": "api@example.com", "password": "pass12345!"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)

    def test_register_rejects_duplicate_email(self):
        make_user(email="api@example.com")
        response = self.client.post(
            "/api/register/",
            {"username": "other", "email": "api@example.com", "password": "pass12345!"},
        )
        self.assertEqual(response.status_code, 400)

    def test_token_requires_verified_email(self):
        make_user(email="unverified@example.com", verified=False)
        response = self.client.post(
            "/api/token/", {"email": "unverified@example.com", "password": "pass12345!"}
        )
        self.assertEqual(response.status_code, 400)

    def test_token_includes_user_role(self):
        make_user(email="author@example.com", role="author")
        response = self.client.post(
            "/api/token/", {"email": "author@example.com", "password": "pass12345!"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertEqual(response.data["user"]["role"], "author")

    def test_logout_blacklists_refresh_token(self):
        make_user(email="out@example.com")
        tokens = self.client.post(
            "/api/token/", {"email": "out@example.com", "password": "pass12345!"}
        ).data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        self.client.post("/api/logout/", {"refresh": tokens["refresh"]})
        reuse = self.client.post("/api/token/refresh/", {"refresh": tokens["refresh"]})
        self.assertEqual(reuse.status_code, 401)


class BlogApiVisibilityTests(APITestCase):
    def setUp(self):
        self.author = make_user(role="author")
        self.published = make_post(author=self.author, title="Public post")
        self.draft = make_post(author=self.author, title="Hidden draft", status="draft")

    def titles(self):
        return [p["title"] for p in self.client.get("/api/blogs/").data["results"]]

    def test_anonymous_sees_only_published(self):
        self.assertEqual(self.titles(), ["Public post"])

    def test_anonymous_cannot_open_draft(self):
        self.assertEqual(self.client.get(f"/api/blogs/{self.draft.slug}/").status_code, 404)

    def test_other_user_cannot_see_draft(self):
        self.client.force_authenticate(make_user(role="author"))
        self.assertNotIn("Hidden draft", self.titles())

    def test_author_sees_own_draft(self):
        self.client.force_authenticate(self.author)
        self.assertIn("Hidden draft", self.titles())

    def test_detail_counts_views(self):
        self.client.get(f"/api/blogs/{self.published.slug}/")
        self.published.refresh_from_db()
        self.assertEqual(self.published.views, 1)


class BlogApiWriteTests(APITestCase):
    def setUp(self):
        self.author = make_user(role="author")
        self.category = make_category()

    def test_author_can_create_post(self):
        self.client.force_authenticate(self.author)
        response = self.client.post(
            "/api/blogs/",
            {"title": "From the API", "content": "Body", "status": "published", "category": self.category.id},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(BlogPost.objects.get().author, self.author)

    def test_reader_cannot_create_post(self):
        self.client.force_authenticate(make_user(role="user"))
        response = self.client.post("/api/blogs/", {"title": "x", "content": "y"})
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_create_post(self):
        response = self.client.post("/api/blogs/", {"title": "x", "content": "y"})
        self.assertEqual(response.status_code, 401)

    def test_author_cannot_edit_someone_elses_post(self):
        post = make_post(author=make_user(role="author"))
        self.client.force_authenticate(self.author)
        response = self.client.patch(f"/api/blogs/{post.slug}/", {"title": "Hacked"})
        self.assertEqual(response.status_code, 403)

    def test_author_can_edit_own_post(self):
        post = make_post(author=self.author)
        self.client.force_authenticate(self.author)
        response = self.client.patch(f"/api/blogs/{post.slug}/", {"title": "Updated"})
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.title, "Updated")

    def test_like_action_toggles(self):
        post = make_post()
        reader = make_user()
        self.client.force_authenticate(reader)
        self.client.post(f"/api/blogs/{post.slug}/like/")
        self.assertTrue(post.likes.filter(pk=reader.pk).exists())
        self.client.post(f"/api/blogs/{post.slug}/like/")
        self.assertFalse(post.likes.filter(pk=reader.pk).exists())

    def test_comment_api_sets_author(self):
        post = make_post()
        reader = make_user()
        self.client.force_authenticate(reader)
        response = self.client.post("/api/comments/", {"post": post.id, "content": "API comment", "rating": 4})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Comment.objects.get().author, reader)

    def test_reader_cannot_create_category(self):
        self.client.force_authenticate(make_user(role="user"))
        self.assertEqual(self.client.post("/api/categories/", {"name": "New"}).status_code, 403)


class DocsTests(APITestCase):
    def test_openapi_schema_and_docs_load(self):
        self.assertEqual(self.client.get("/api/schema/").status_code, 200)
        self.assertEqual(self.client.get("/api/docs/").status_code, 200)
        self.assertEqual(self.client.get("/api/redoc/").status_code, 200)
