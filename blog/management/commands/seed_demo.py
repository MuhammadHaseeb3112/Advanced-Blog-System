"""Fill the database with demo users, posts, comments and likes.

    python manage.py seed_demo           # add demo data if it is missing
    python manage.py seed_demo --reset   # wipe demo data and create it again

Cover illustrations are drawn with Pillow, so no external files are needed.
"""
import random
from datetime import timedelta
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFilter

from accounts.models import CustomUser
from blog.models import BlogPost, Category, Comment, Tag

from ._demo_content import COMMENTS, DRAFTS, PEOPLE, POSTS

DEMO_DOMAIN = "demo.blog"
PASSWORD = "DemoPass123!"

WIDTH, HEIGHT = 1200, 630
PALETTES = {
    "Backend": [((49, 46, 129), (124, 58, 237)), ((30, 64, 175), (79, 70, 229))],
    "DevOps": [((6, 78, 59), (14, 116, 144)), ((15, 23, 42), (3, 105, 161))],
    "Frontend": [((190, 24, 93), (234, 88, 12)), ((157, 23, 77), (124, 58, 237))],
    "Data": [((12, 74, 110), (6, 182, 212)), ((30, 27, 75), (2, 132, 199))],
    "Career": [((120, 53, 15), (217, 119, 6)), ((67, 56, 202), (219, 39, 119))],
}
WHITE = (255, 255, 255)


def _background(palette, seed):
    start, end = palette
    base = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(base)
    for y in range(HEIGHT):
        for x in range(0, WIDTH, 4):
            t = (x / WIDTH) * 0.7 + (y / HEIGHT) * 0.3
            colour = tuple(int(start[i] + (end[i] - start[i]) * t) for i in range(3))
            draw.line([(x, y), (x + 3, y)], fill=colour)
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    rnd = random.Random(seed)
    for _ in range(4):
        r = rnd.randint(120, 260)
        cx, cy = rnd.randint(0, WIDTH), rnd.randint(0, HEIGHT)
        gdraw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 38))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    base = Image.alpha_composite(base.convert("RGBA"), glow)
    # subtle dot grid
    dots = ImageDraw.Draw(base)
    for x in range(40, WIDTH, 40):
        for y in range(40, HEIGHT, 40):
            dots.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(255, 255, 255, 40))
    return base


def _panel(draw, box, radius=26):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle([x0 + 10, y0 + 16, x1 + 10, y1 + 16], radius, fill=(0, 0, 0, 55))
    draw.rounded_rectangle(box, radius, fill=(255, 255, 255, 235))


def _code_window(draw, rnd):
    box = (300, 120, 900, 520)
    _panel(draw, box)
    draw.rounded_rectangle([300, 120, 900, 175], 26, fill=(30, 27, 75, 255))
    draw.rectangle([300, 150, 900, 175], fill=(30, 27, 75, 255))
    for i, c in enumerate([(248, 113, 113), (251, 191, 36), (52, 211, 153)]):
        draw.ellipse([326 + i * 26, 139, 342 + i * 26, 155], fill=c)
    colours = [(99, 102, 241), (236, 72, 153), (16, 185, 129), (245, 158, 11), (148, 163, 184)]
    y = 205
    indent = 0
    while y < 490:
        indent = max(0, min(3, indent + rnd.choice([-1, 0, 0, 1])))
        x = 340 + indent * 34
        for _ in range(rnd.randint(1, 3)):
            w = rnd.randint(40, 150)
            if x + w > 860:
                break
            draw.rounded_rectangle([x, y, x + w, y + 14], 7, fill=colours[rnd.randrange(len(colours))] + (255,))
            x += w + 14
        y += 30


def _servers(draw, rnd):
    for i in range(3):
        top = 150 + i * 120
        _panel(draw, (330, top, 870, top + 95), 20)
        for j in range(3):
            draw.ellipse([360 + j * 28, top + 38, 376 + j * 28, top + 54],
                         fill=[(52, 211, 153), (52, 211, 153), (251, 191, 36)][(i + j) % 3] + (255,))
        for k in range(rnd.randint(4, 6)):
            x = 480 + k * 62
            draw.rounded_rectangle([x, top + 28, x + 48, top + 66], 8, fill=(14, 116, 144, 200))


def _browser(draw, rnd):
    _panel(draw, (260, 110, 940, 530))
    draw.rounded_rectangle([290, 135, 910, 165], 15, fill=(226, 232, 240, 255))
    draw.rounded_rectangle([290, 190, 910, 300], 16, fill=(236, 72, 153, 210))
    draw.rounded_rectangle([320, 222, 620, 242], 10, fill=WHITE + (255,))
    draw.rounded_rectangle([320, 256, 520, 270], 7, fill=(255, 255, 255, 180))
    for i in range(3):
        x = 290 + i * 212
        draw.rounded_rectangle([x, 320, x + 196, 500], 16, fill=(241, 245, 249, 255))
        draw.rounded_rectangle([x + 16, 336, x + 180, 410], 10, fill=(251, 146, 60, 200))
        draw.rounded_rectangle([x + 16, 426, x + 160, 440], 7, fill=(100, 116, 139, 255))
        draw.rounded_rectangle([x + 16, 452, x + 120, 464], 6, fill=(203, 213, 225, 255))


def _chart(draw, rnd):
    _panel(draw, (290, 120, 910, 520))
    values = [rnd.randint(60, 260) for _ in range(8)]
    for i, v in enumerate(values):
        x = 340 + i * 68
        draw.rounded_rectangle([x, 480 - v, x + 42, 480], 10, fill=(6, 182, 212, 220))
    points = [(361 + i * 68, 470 - v - 30) for i, v in enumerate(values)]
    draw.line(points, fill=(124, 58, 237, 255), width=6, joint="curve")
    for x, y in points:
        draw.ellipse([x - 8, y - 8, x + 8, y + 8], fill=(124, 58, 237, 255), outline=WHITE, width=3)


def _profile(draw, rnd):
    _panel(draw, (360, 110, 840, 530))
    draw.ellipse([540, 150, 660, 270], fill=(217, 119, 6, 255))
    draw.ellipse([575, 175, 625, 225], fill=WHITE + (255,))
    draw.pieslice([555, 220, 645, 300], 180, 360, fill=WHITE + (255,))
    draw.rounded_rectangle([470, 295, 730, 315], 10, fill=(30, 41, 59, 255))
    draw.rounded_rectangle([510, 330, 690, 344], 7, fill=(148, 163, 184, 255))
    for i, c in enumerate([(16, 185, 129), (99, 102, 241), (236, 72, 153)]):
        y = 375 + i * 44
        draw.ellipse([420, y, 444, y + 24], fill=c + (255,))
        draw.rounded_rectangle([460, y + 5, 460 + rnd.randint(180, 300), y + 19], 7, fill=(203, 213, 225, 255))


MOTIFS = {"Backend": _code_window, "DevOps": _servers, "Frontend": _browser,
          "Data": _chart, "Career": _profile}


def cover_image(title, category, index):
    rnd = random.Random(title)
    palettes = PALETTES.get(category, PALETTES["Backend"])
    image = _background(palettes[index % len(palettes)], title)
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    MOTIFS.get(category, _code_window)(ImageDraw.Draw(layer), rnd)
    image = Image.alpha_composite(image, layer).convert("RGB")
    buffer = BytesIO()
    # 960px wide is plenty for cards and the post header, and keeps files small
    image = image.resize((960, 504), Image.LANCZOS)
    image.save(buffer, format="JPEG", quality=80, optimize=True, progressive=True)
    return ContentFile(buffer.getvalue(), name=f"{slugify(title)[:50]}.jpg")


class Command(BaseCommand):
    help = "Create demo users, posts, comments and likes."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete demo data first.")

    def handle(self, *args, **options):
        if options["reset"]:
            CustomUser.objects.filter(email__endswith=f"@{DEMO_DOMAIN}").delete()

        if CustomUser.objects.filter(email__endswith=f"@{DEMO_DOMAIN}").exists():
            self.stdout.write("Demo data already present. Use --reset to recreate it.")
            return

        rnd = random.Random(7)
        now = timezone.now()
        users = {}
        for username, full_name, role, bio in PEOPLE:
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
                is_staff=role == "admin",
                is_superuser=role == "admin",
            )
            users[username] = user

        names = {p[0] for p in POSTS} | {d[0] for d in DRAFTS}
        categories = {name: Category.objects.get_or_create(name=name)[0] for name in names}

        posts = []
        for index, (category, tags, author, title, summary, body, days_ago) in enumerate(POSTS):
            post = BlogPost.objects.create(
                title=title,
                short_description=summary,
                content=body,
                author=users[author],
                category=categories[category],
                status="published",
                publish_at=now - timedelta(days=days_ago, hours=rnd.randint(0, 10)),
                views=rnd.randint(180, 1400) + days_ago * 25,
                featured_image=cover_image(title, category, index),
            )
            post.tags.set([Tag.objects.get_or_create(name=t)[0] for t in tags])
            posts.append(post)

        for category, author, title, summary, body, publish_in in DRAFTS:
            BlogPost.objects.create(
                title=title,
                short_description=summary,
                content=body,
                author=users[author],
                category=categories[category],
                status="draft",
                publish_at=now + timedelta(days=publish_in) if publish_in else None,
                featured_image=cover_image(title, category, 1),
            )

        everyone = [u for u in users.values() if u.username != "admin"]
        comment_pool = COMMENTS[:]
        rnd.shuffle(comment_pool)
        for i, post in enumerate(posts):
            others = [u for u in everyone if u != post.author]
            for user in rnd.sample(others, k=rnd.randint(3, len(others))):
                post.likes.add(user)
            for user in rnd.sample(others, k=rnd.randint(1, 3)):
                post.bookmarks.add(user)
            for j, user in enumerate(rnd.sample(others, k=rnd.randint(1, 3))):
                comment = Comment.objects.create(
                    post=post, author=user,
                    content=comment_pool[(i * 3 + j) % len(comment_pool)],
                    rating=rnd.choice([4, 5, 5]),
                )
                # spread comments over the days after publishing
                published = post.publish_at or now
                created = min(now, published + timedelta(hours=rnd.randint(2, 72)))
                Comment.objects.filter(pk=comment.pk).update(created_at=created)

        self._refresh_cached_stats()
        self.stdout.write(self.style.SUCCESS(
            f"Created {len(users)} users and {len(posts) + len(DRAFTS)} posts. "
            f"Log in with sara@{DEMO_DOMAIN} / {PASSWORD}"
        ))

    def _refresh_cached_stats(self):
        """Fill the trending and analytics caches so the demo never shows empty charts."""
        from blog.tasks import calculate_dashboard_analytics, calculate_trending_posts

        for task in (calculate_trending_posts, calculate_dashboard_analytics):
            try:
                task()
            except Exception as exc:  # cache down: the hourly task will fill it later
                self.stdout.write(f"Skipped {task.__name__}: {exc}")
