"""Fill the database with demo authors, posts, comments and likes.

    python manage.py seed_demo           # add demo data if it is missing
    python manage.py seed_demo --reset   # wipe demo data and create it again

Cover images are drawn with Pillow, so no external files are needed.
"""
import random
from datetime import timedelta
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db.models import F
from django.utils import timezone
from PIL import Image, ImageDraw

from accounts.models import CustomUser
from blog.models import BlogPost, Category, Comment, Tag

DEMO_DOMAIN = "demo.blog"
PASSWORD = "DemoPass123!"

AUTHORS = [
    ("sara", "Sara Khan", "author", "Backend engineer writing about Django and APIs."),
    ("bilal", "Bilal Ahmed", "author", "DevOps and cloud. Ships things on Fridays."),
    ("ayesha", "Ayesha Malik", "author", "Frontend developer who likes clean UIs."),
    ("reader", "Demo Reader", "user", "Reads everything, comments sometimes."),
]

PALETTES = [
    ((37, 99, 235), (124, 58, 237)),
    ((5, 150, 105), (14, 116, 144)),
    ((234, 88, 12), (219, 39, 119)),
    ((15, 23, 42), (51, 65, 85)),
]

POSTS = [
    ("Backend", ["django", "performance"], "sara",
     "Finding and Fixing N+1 Queries in Django",
     "How select_related, prefetch_related and a query-count test keep list pages fast.",
     "A list page that runs one query per row looks fine with ten rows and falls over with a thousand. "
     "This post walks through spotting N+1 queries with the Django debug toolbar, fixing them with "
     "select_related for foreign keys and prefetch_related for many-to-many fields, and locking the fix in "
     "with assertNumQueries so it never comes back."),
    ("Backend", ["django", "celery"], "sara",
     "Background Jobs with Celery and Redis",
     "Sending emails, publishing scheduled posts and building reports without blocking requests.",
     "Anything slower than a few hundred milliseconds belongs outside the request. Celery workers pick up "
     "jobs from Redis, retry failures with a back-off, and Celery Beat runs periodic tasks such as "
     "publishing scheduled posts and clearing old notifications."),
    ("Backend", ["django", "websockets"], "sara",
     "Real-Time Notifications with Django Channels",
     "Pushing likes and comments to the browser the moment they happen.",
     "Django Channels adds WebSockets to Django. Each user joins a personal group, each post has its own "
     "room, and views publish events to the channel layer so every open tab updates instantly."),
    ("Backend", ["drf", "security"], "sara",
     "JWT Authentication for a DRF API",
     "Access and refresh tokens, rotation and blacklisting on logout.",
     "Short-lived access tokens limit the damage of a leak, refresh tokens keep users signed in, and "
     "blacklisting on logout makes sure an old refresh token cannot be reused."),
    ("DevOps", ["docker", "deployment"], "bilal",
     "Dockerizing a Django App with PostgreSQL and Redis",
     "One docker compose up for the web app, workers, database and cache.",
     "A compose file with separate services for Django, Celery worker, Celery Beat, PostgreSQL and Redis "
     "gives every developer the same environment and makes production deploys boring."),
    ("DevOps", ["ci-cd", "testing"], "bilal",
     "CI with GitHub Actions: Tests on Every Push",
     "Run migrations checks and the test suite against a real PostgreSQL service.",
     "A workflow that spins up PostgreSQL as a service, installs dependencies with caching, checks for "
     "missing migrations and runs the whole test suite takes a couple of minutes and catches most "
     "regressions before they reach main."),
    ("Frontend", ["ux", "css"], "ayesha",
     "Designing a Readable Blog Layout",
     "Line length, spacing and contrast choices that make long articles easier to read.",
     "Keep lines between 60 and 80 characters, use generous line height, and give headings enough space. "
     "Small choices like these matter more than any animation."),
    ("Frontend", ["javascript", "ux"], "ayesha",
     "Infinite Scroll Without a Framework",
     "Loading the next page of posts with fetch and a few lines of JavaScript.",
     "When the reader nears the bottom of the page, fetch the next page, parse the returned HTML and "
     "append the new cards. No framework needed, and the server-rendered pages still work without JS."),
    ("Career", ["career"], "bilal",
     "What I Look for in a Junior Developer Portfolio",
     "Live demos, tests and a clear README beat a long list of tutorials.",
     "A project that is deployed, tested and documented tells a reviewer more than ten unfinished ones. "
     "Show the live link, explain the trade-offs, and keep the README short."),
]

COMMENTS = [
    "Really clear explanation, thanks!",
    "This saved me a few hours today.",
    "Would love a follow-up on testing this.",
    "Great examples, bookmarked.",
    "Exactly the problem I had last week.",
]


def cover_image(title, palette):
    width, height = 1200, 630
    start, end = palette
    image = Image.new("RGB", (width, height), start)
    draw = ImageDraw.Draw(image)
    for x in range(width):
        t = x / width
        colour = tuple(int(start[i] + (end[i] - start[i]) * t) for i in range(3))
        draw.line([(x, 0), (x, height)], fill=colour)
    for i in range(6):
        r = 120 + i * 70
        draw.ellipse([width - r, -r // 2, width + r, r * 1.5], outline=(255, 255, 255, 40), width=2)
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return ContentFile(buffer.getvalue(), name=f"{title[:40].lower().replace(' ', '-')}.jpg")


class Command(BaseCommand):
    help = "Create demo authors, posts, comments and likes."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete demo data first.")

    def handle(self, *args, **options):
        if options["reset"]:
            CustomUser.objects.filter(email__endswith=f"@{DEMO_DOMAIN}").delete()

        if CustomUser.objects.filter(email__endswith=f"@{DEMO_DOMAIN}").exists():
            self.stdout.write("Demo data already present. Use --reset to recreate it.")
            return

        random.seed(7)
        users = {}
        for username, full_name, role, bio in AUTHORS:
            first, last = full_name.split(" ", 1)
            user = CustomUser.objects.create_user(
                username=username,
                email=f"{username}@{DEMO_DOMAIN}",
                password=PASSWORD,
                first_name=first,
                last_name=last,
                role=role,
                bio=bio,
                email_verified=True,
            )
            users[username] = user

        categories = {name: Category.objects.get_or_create(name=name)[0]
                      for name in {p[0] for p in POSTS}}
        now = timezone.now()
        posts = []
        for index, (category, tags, author, title, summary, body) in enumerate(POSTS):
            post = BlogPost.objects.create(
                title=title,
                short_description=summary,
                content=body,
                author=users[author],
                category=categories[category],
                status="published",
                publish_at=now - timedelta(days=len(POSTS) - index),
                views=random.randint(40, 600),
                featured_image=cover_image(title, PALETTES[index % len(PALETTES)]),
            )
            post.tags.set([Tag.objects.get_or_create(name=t)[0] for t in tags])
            posts.append(post)

        BlogPost.objects.create(
            title="Draft: Caching Strategies with Redis",
            short_description="Work in progress.",
            content="Notes on per-view caching, low-level cache API and invalidation.",
            author=users["sara"],
            category=categories["Backend"],
            status="draft",
        )
        BlogPost.objects.create(
            title="Scheduled: Zero-Downtime Deploys",
            short_description="Publishes automatically via Celery Beat.",
            content="Health checks, rollbacks and running migrations safely.",
            author=users["bilal"],
            category=categories["DevOps"],
            status="draft",
            publish_at=now + timedelta(days=2),
        )

        everyone = list(users.values())
        for post in posts:
            others = [u for u in everyone if u != post.author]
            for user in random.sample(others, k=random.randint(1, len(others))):
                post.likes.add(user)
            for user in random.sample(others, k=random.randint(0, 2)):
                post.bookmarks.add(user)
            for user in random.sample(others, k=random.randint(1, 2)):
                Comment.objects.create(
                    post=post, author=user, content=random.choice(COMMENTS),
                    rating=random.randint(4, 5),
                )

        BlogPost.objects.filter(pk__in=[p.pk for p in posts[:3]]).update(views=F("views") + 500)
        self.stdout.write(self.style.SUCCESS(
            f"Created {len(users)} users and {len(posts) + 2} posts. "
            f"Log in with sara@{DEMO_DOMAIN} / {PASSWORD}"
        ))
