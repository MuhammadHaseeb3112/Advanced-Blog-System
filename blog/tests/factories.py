"""Small helpers to build test data without a factory library."""
from itertools import count

from django.utils import timezone

from accounts.models import CustomUser
from blog.models import BlogPost, Category, Tag

_seq = count(1)


def make_user(role="user", verified=True, **extra):
    n = next(_seq)
    return CustomUser.objects.create_user(
        username=extra.pop("username", f"user{n}"),
        email=extra.pop("email", f"user{n}@example.com"),
        password=extra.pop("password", "pass12345!"),
        role=role,
        email_verified=verified,
        **extra,
    )


def make_category(name=None):
    return Category.objects.create(name=name or f"Category {next(_seq)}")


def make_tag(name=None):
    return Tag.objects.create(name=name or f"Tag {next(_seq)}")


def make_post(author=None, status="published", **extra):
    n = next(_seq)
    if status == "published":
        extra.setdefault("publish_at", timezone.now() - timezone.timedelta(minutes=1))
    return BlogPost.objects.create(
        title=extra.pop("title", f"Post number {n}"),
        content=extra.pop("content", "Some content for the post."),
        author=author or make_user(role="author"),
        status=status,
        **extra,
    )
