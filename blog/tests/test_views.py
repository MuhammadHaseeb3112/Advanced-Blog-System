from django.test import TestCase

from blog.models import BlogPost, Comment, Notification

from .factories import make_category, make_post, make_user


class PublicPageTests(TestCase):
    def setUp(self):
        self.post = make_post(title="Learning Django Channels")
        self.draft = make_post(title="Secret draft", status="draft")

    def test_home_page_loads(self):
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_blog_list_shows_published_posts_only(self):
        response = self.client.get("/blogs/")
        self.assertContains(response, "Learning Django Channels")
        self.assertNotContains(response, "Secret draft")

    def test_blog_search(self):
        make_post(title="Celery background jobs")
        response = self.client.get("/blogs/", {"search": "Celery"})
        self.assertContains(response, "Celery background jobs")
        self.assertNotContains(response, "Learning Django Channels")

    def test_detail_page_counts_one_view_per_session(self):
        url = f"/blogs/{self.post.slug}/"
        self.client.get(url)
        self.client.get(url)
        self.post.refresh_from_db()
        self.assertEqual(self.post.views, 1)

    def test_draft_detail_is_404(self):
        self.assertEqual(self.client.get(f"/blogs/{self.draft.slug}/").status_code, 404)

    def test_filter_by_category(self):
        category = make_category("Backend")
        make_post(title="In backend", category=category)
        response = self.client.get("/blogs/", {"category": category.slug})
        self.assertContains(response, "In backend")
        self.assertNotContains(response, "Learning Django Channels")


class InteractionTests(TestCase):
    def setUp(self):
        self.author = make_user(role="author")
        self.reader = make_user()
        self.post = make_post(author=self.author)
        self.client.force_login(self.reader)

    def test_like_toggles(self):
        url = f"/blogs/{self.post.slug}/like/"
        first = self.client.post(url).json()
        second = self.client.post(url).json()
        self.assertTrue(first["liked"])
        self.assertEqual(first["total_likes"], 1)
        self.assertFalse(second["liked"])
        self.assertEqual(second["total_likes"], 0)

    def test_like_requires_post_method(self):
        self.assertEqual(self.client.get(f"/blogs/{self.post.slug}/like/").status_code, 400)

    def test_like_requires_login(self):
        self.client.logout()
        response = self.client.post(f"/blogs/{self.post.slug}/like/")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.post.likes.exists())

    def test_bookmark_toggles(self):
        url = f"/blogs/{self.post.slug}/bookmark/"
        self.assertTrue(self.client.post(url).json()["bookmarked"])
        self.assertIn(self.post, self.reader.bookmarked_posts.all())
        self.assertFalse(self.client.post(url).json()["bookmarked"])

    def test_comment_creates_comment_and_notifies_author(self):
        response = self.client.post(
            f"/blogs/{self.post.slug}/comment/", {"content": "Great read", "rating": "4"}
        )
        self.assertTrue(response.json()["success"])
        self.assertEqual(Comment.objects.get().rating, 4)
        self.assertTrue(
            Notification.objects.filter(receiver=self.author, notification_type="comment").exists()
        )

    def test_comment_without_rating_defaults_to_five(self):
        self.client.post(f"/blogs/{self.post.slug}/comment/", {"content": "No stars given"})
        self.assertEqual(Comment.objects.get().rating, 5)

    def test_comment_rating_is_clamped(self):
        self.client.post(f"/blogs/{self.post.slug}/comment/", {"content": "x", "rating": "99"})
        self.assertEqual(Comment.objects.get().rating, 5)

    def test_empty_comment_rejected(self):
        response = self.client.post(f"/blogs/{self.post.slug}/comment/", {"content": ""})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Comment.objects.exists())

    def test_cannot_interact_with_draft(self):
        draft = make_post(author=self.author, status="draft")
        self.assertEqual(self.client.post(f"/blogs/{draft.slug}/like/").status_code, 404)


class AuthoringTests(TestCase):
    def setUp(self):
        self.author = make_user(role="author")
        self.client.force_login(self.author)

    def test_author_can_create_post(self):
        response = self.client.post(
            "/create-post/",
            {"title": "Brand new post", "content": "Body", "status": "published"},
        )
        self.assertRedirects(response, "/my-posts/", fetch_redirect_response=False)
        post = BlogPost.objects.get(title="Brand new post")
        self.assertEqual(post.author, self.author)
        self.assertIsNotNone(post.publish_at)

    def test_title_and_content_required(self):
        self.client.post("/create-post/", {"title": "", "content": ""})
        self.assertFalse(BlogPost.objects.exists())

    def test_regular_user_cannot_create_post(self):
        self.client.force_login(make_user(role="user"))
        response = self.client.post("/create-post/", {"title": "Nope", "content": "x"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(BlogPost.objects.exists())

    def test_author_cannot_delete_someone_elses_post(self):
        other = make_post(author=make_user(role="author"))
        self.client.post(f"/delete-post/{other.slug}/")
        self.assertTrue(BlogPost.objects.filter(pk=other.pk).exists())

    def test_author_can_delete_own_post(self):
        mine = make_post(author=self.author)
        self.client.post(f"/delete-post/{mine.slug}/")
        self.assertFalse(BlogPost.objects.filter(pk=mine.pk).exists())

    def test_my_posts_lists_drafts_too(self):
        make_post(author=self.author, title="My draft", status="draft")
        self.assertContains(self.client.get("/my-posts/"), "My draft")


class StaffPageTests(TestCase):
    def test_manage_pages_need_staff(self):
        self.client.force_login(make_user(role="author"))
        for url in ("/manage-categories/", "/manage-tags/", "/manage-comments/", "/users/"):
            self.assertEqual(self.client.get(url).status_code, 302, url)

    def test_superuser_can_open_manage_pages(self):
        self.client.force_login(make_user(role="admin", is_staff=True, is_superuser=True))
        for url in ("/manage-categories/", "/manage-tags/", "/manage-comments/", "/users/"):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_signed_in_pages_load(self):
        self.client.force_login(make_user(role="author"))
        for url in ("/dashboard/", "/saved-posts/", "/liked-posts/", "/commented-posts/", "/notifications/"):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_notifications_page_is_for_authors_only(self):
        self.client.force_login(make_user(role="user"))
        self.assertEqual(self.client.get("/notifications/").status_code, 302)
