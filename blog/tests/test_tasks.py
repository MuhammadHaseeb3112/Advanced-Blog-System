from datetime import timedelta

from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from blog.models import BlogPost, Notification
from blog.tasks import (
    calculate_trending_posts,
    delete_old_notifications,
    publish_scheduled_posts,
    send_welcome_email,
)

from .factories import make_post, make_user


class TaskTests(TestCase):
    def test_publish_scheduled_posts_publishes_due_drafts_only(self):
        due = make_post(status="draft", publish_at=timezone.now() - timedelta(minutes=5))
        later = make_post(status="draft", publish_at=timezone.now() + timedelta(days=1))
        plain_draft = make_post(status="draft")

        self.assertEqual(publish_scheduled_posts(), "1 posts published")
        statuses = dict(BlogPost.objects.values_list("pk", "status"))
        self.assertEqual(statuses[due.pk], "published")
        self.assertEqual(statuses[later.pk], "draft")
        self.assertEqual(statuses[plain_draft.pk], "draft")

    def test_delete_old_notifications(self):
        post = make_post()
        old = Notification.objects.create(
            sender=make_user(), receiver=post.author, post=post, notification_type="comment"
        )
        Notification.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=8))
        Notification.objects.create(
            sender=make_user(), receiver=post.author, post=post, notification_type="comment"
        )
        delete_old_notifications()
        self.assertEqual(Notification.objects.count(), 1)

    def test_trending_ranks_engagement_and_caches_result(self):
        quiet = make_post(title="Quiet")
        popular = make_post(title="Popular")
        for _ in range(3):
            popular.likes.add(make_user())
        calculate_trending_posts()
        ranked = list(cache.get("trending_posts"))
        self.assertEqual(ranked[0], popular)
        self.assertIn(quiet, ranked)

    def test_welcome_email_is_sent(self):
        send_welcome_email.delay("sara", "sara@example.com")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["sara@example.com"])
