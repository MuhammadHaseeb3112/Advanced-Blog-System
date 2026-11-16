from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from blog.models import BlogPost, Comment, Notification

from .factories import make_category, make_post, make_tag, make_user


class SlugTests(TestCase):
    def test_category_and_tag_get_slugs(self):
        self.assertEqual(make_category("Web Development").slug, "web-development")
        self.assertEqual(make_tag("Django REST").slug, "django-rest")

    def test_post_slug_is_generated_from_title(self):
        post = make_post(title="Hello Django World")
        self.assertTrue(post.slug.startswith("hello-django-world"))

    def test_posts_with_same_title_get_unique_slugs(self):
        a = make_post(title="Same Title")
        b = make_post(title="Same Title")
        self.assertNotEqual(a.slug, b.slug)


class PublishedQuerySetTests(TestCase):
    def test_published_excludes_drafts_and_future_posts(self):
        live = make_post()
        make_post(status="draft")
        make_post(status="published", publish_at=timezone.now() + timedelta(days=1))
        self.assertEqual(list(BlogPost.objects.published()), [live])

    def test_published_includes_posts_without_publish_date(self):
        post = make_post(publish_at=None)
        self.assertIn(post, BlogPost.objects.published())

    def test_by_author_and_drafts(self):
        author = make_user(role="author")
        mine = make_post(author=author, status="draft")
        make_post(status="draft")
        self.assertEqual(list(BlogPost.objects.drafts().by_author(author)), [mine])


class LikeSignalTests(TestCase):
    def setUp(self):
        self.author = make_user(role="author")
        self.reader = make_user()
        self.post = make_post(author=self.author)

    def test_like_creates_one_notification_for_author(self):
        self.post.likes.add(self.reader)
        self.post.likes.add(self.reader)
        self.assertEqual(
            Notification.objects.filter(receiver=self.author, notification_type="like").count(), 1
        )

    def test_unlike_removes_notification(self):
        self.post.likes.add(self.reader)
        self.post.likes.remove(self.reader)
        self.assertFalse(Notification.objects.exists())

    def test_author_liking_own_post_gets_no_notification(self):
        self.post.likes.add(self.author)
        self.assertFalse(Notification.objects.exists())


class CommentModelTests(TestCase):
    def test_comment_defaults_to_five_star_rating(self):
        post = make_post()
        comment = Comment.objects.create(post=post, author=make_user(), content="Nice")
        self.assertEqual(comment.rating, 5)
