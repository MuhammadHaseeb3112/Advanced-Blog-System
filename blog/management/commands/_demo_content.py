"""Text used by `seed_demo`. Kept separate so the command stays readable.

Post bodies use the small Markdown subset understood by the `render_content`
template filter: ## and ### headings, - lists, > quotes, ``` code blocks,
`inline code` and **bold**.
"""

# username, full name, role, bio
PEOPLE = [
    ("admin", "Areeba Hassan", "admin", "Runs the publication. Reviews posts and keeps the community friendly."),
    ("sara", "Sara Khan", "author", "Backend engineer. Writes about Django, PostgreSQL and API design."),
    ("bilal", "Bilal Ahmed", "author", "DevOps engineer. Docker, CI/CD and keeping servers boring."),
    ("ayesha", "Ayesha Malik", "author", "Frontend developer who cares about readable, accessible interfaces."),
    ("usman", "Usman Tariq", "author", "Data engineer. Python, SQL and the occasional dashboard."),
    ("reader", "Hamza Raza", "user", "Junior developer reading everything about Django."),
    ("zainab", "Zainab Ali", "user", "CS student, building my first SaaS side project."),
    ("omar", "Omar Farooq", "user", "Full-stack developer at a fintech startup."),
    ("fatima", "Fatima Noor", "user", "QA engineer learning backend development."),
]

# category, tags, author, title, summary, body, days ago
POSTS = [
    ("Backend", ["django", "performance", "postgresql"], "sara",
     "Finding and Fixing N+1 Queries in Django",
     "A list page that runs one query per row is fine with ten rows and painful with a thousand. "
     "Here is how I find those queries and make sure they never come back.",
     """Last month our post list page took almost two seconds to load. The template looked innocent, the view was four lines long, and yet the debug toolbar showed **214 SQL queries** for a single request. Classic N+1.

## What an N+1 query looks like

The view fetched the posts in one query. Then, for every post, the template touched `post.author.username` and `post.tags.all`, and each of those triggered its own query.

```python
posts = BlogPost.objects.filter(status="published")
# template: {{ post.author.username }} and {% for tag in post.tags.all %}
```

One query for the list, plus one per author, plus one per tag set. With 100 posts that is 201 queries.

## The fix: select_related and prefetch_related

- `select_related` follows foreign keys with a SQL JOIN, so the author arrives in the same query.
- `prefetch_related` runs one extra query for many-to-many fields and joins the results in Python.

```python
posts = (
    BlogPost.objects.filter(status="published")
    .select_related("author", "category")
    .prefetch_related("tags")
)
```

That brought the page down to **3 queries** and about 90 ms.

## Lock it in with a test

Performance fixes quietly regress when someone adds a new field to the template. A query-count test catches that in CI:

```python
def test_post_list_query_count(self):
    make_posts(30)
    with self.assertNumQueries(4):
        self.client.get(reverse("blog_list"))
```

> If the number of queries grows with the number of rows, you have an N+1 problem, no matter how fast it feels locally.

I now put the optimised queryset on a custom manager (`BlogPost.objects.optimized()`) so every view gets it for free.""",
     41),

    ("Backend", ["django", "celery", "redis"], "sara",
     "Background Jobs with Celery and Redis: A Practical Setup",
     "Emails, scheduled publishing and nightly reports should never block a request. "
     "This is the Celery setup I use in production, including retries and periodic tasks.",
     """Anything that takes longer than a few hundred milliseconds does not belong inside the request. Sending a welcome email, resizing an image or recalculating trending posts can all happen in the background.

## The moving parts

- **Redis** is the broker: Django puts a message on a queue.
- **Celery worker** picks the message up and runs the task.
- **Celery Beat** is a scheduler that enqueues periodic tasks.

## A task that retries properly

Network calls fail. Instead of losing the email, let Celery retry with a back-off:

```python
@shared_task(bind=True, autoretry_for=(SMTPException,),
             retry_backoff=True, max_retries=5)
def send_welcome_email(self, user_id):
    user = CustomUser.objects.get(pk=user_id)
    send_mail("Welcome!", render_body(user), None, [user.email])
```

## Periodic tasks with Beat

This blog uses Beat for four jobs: publishing scheduled posts every minute, recalculating trending posts every 30 minutes, refreshing dashboard analytics every hour and cleaning old notifications once a day.

```python
CELERY_BEAT_SCHEDULE = {
    "publish-scheduled-posts": {
        "task": "blog.tasks.publish_scheduled_posts",
        "schedule": 60,
    },
}
```

## Testing without a broker

In tests I set `CELERY_TASK_ALWAYS_EAGER = True`, so `.delay()` runs the task immediately and I can assert on the result without Redis running.

> Keep tasks small and idempotent. If a task runs twice, nothing bad should happen.""",
     34),

    ("Backend", ["django", "websockets", "channels"], "sara",
     "Real-Time Notifications with Django Channels",
     "How likes and comments on this blog reach your browser the instant they happen, "
     "using Channels, Redis groups and a few lines of JavaScript.",
     """Polling every five seconds works, but it wastes requests and still feels slow. WebSockets let the server push an event the moment something happens.

## Groups are the key idea

Every logged-in user joins a personal group like `user_42`. Every open post page joins `post_17`. When someone likes post 17, the view sends one message to that group and every connected browser receives it.

```python
async def connect(self):
    self.group = f"post_{self.scope['url_route']['kwargs']['post_id']}"
    await self.channel_layer.group_add(self.group, self.channel_name)
    await self.accept()
```

## Sending from a normal Django view

Views are synchronous, so use `async_to_sync`:

```python
async_to_sync(channel_layer.group_send)(
    f"post_{post.id}",
    {"type": "like.update", "likes": post.likes.count()},
)
```

## Things that bit me

- Daphne (or Uvicorn) must serve the app, not plain `runserver` in production.
- The channel layer must be Redis in production; the in-memory layer only works in one process.
- Behind a reverse proxy, forward the `Upgrade` and `Connection` headers.

> Try it: open this post in two tabs, like it in one, and watch the counter change in the other.""",
     27),

    ("Backend", ["drf", "security", "jwt"], "sara",
     "JWT Authentication for a DRF API, Done Right",
     "Short-lived access tokens, refresh token rotation and blacklisting on logout, "
     "with the settings and tests I actually use.",
     """JWTs are easy to add and easy to get wrong. Here is the setup behind this blog's API.

## Two tokens, two lifetimes

- **Access token**: 15 minutes. Sent with every request.
- **Refresh token**: 7 days. Only used to get a new access token.

If an access token leaks, it is useless within minutes.

## Rotation and blacklisting

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}
```

With rotation, every refresh returns a new refresh token and blacklists the old one. On logout the client sends its refresh token and the API blacklists it, so it cannot be reused.

## Document it

`drf-spectacular` generates an OpenAPI schema and a Swagger UI at `/api/docs/`. Recruiters and frontend developers both appreciate being able to click through an API.

> Never put tokens in localStorage if you can avoid it. An httpOnly cookie is harder to steal.""",
     19),

    ("DevOps", ["docker", "deployment", "postgresql"], "bilal",
     "Dockerizing Django with PostgreSQL, Redis and Celery",
     "One docker compose up for the web app, worker, scheduler, database and cache, "
     "and the small details that make the same images work in production.",
     """Five services, one command. This is the compose setup that runs this blog in production.

## The services

- `web`: Daphne serving Django (HTTP and WebSockets)
- `celery`: the background worker
- `beat`: the scheduler
- `db`: PostgreSQL 16
- `redis`: broker, cache and channel layer

All three Python services use the **same image**, only the command changes.

## A small, safe Dockerfile

```dockerfile
FROM python:3.13-slim
RUN useradd --create-home appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
USER appuser
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "core.asgi:application"]
```

## Migrations on start, but only once

An entrypoint script runs `migrate` and `collectstatic` only when `RUN_MIGRATIONS=1`, which is set on the web service alone. Workers never race each other on migrations.

## Health checks

```yaml
db:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U $POSTGRES_USER"]
```

With `depends_on: condition: service_healthy`, Django never starts before PostgreSQL is ready.""",
     23),

    ("DevOps", ["ci-cd", "github-actions", "testing"], "bilal",
     "CI/CD with GitHub Actions: Test, Build, Deploy",
     "Every push runs the test suite against a real PostgreSQL. Every merge to main "
     "deploys automatically, with a health check and automatic rollback.",
     """A pipeline does not need to be complicated to be useful. Mine has two workflows.

## 1. CI on every push

```yaml
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_PASSWORD: postgres
steps:
  - run: python manage.py makemigrations --check
  - run: python manage.py test
```

`makemigrations --check` fails the build if someone changed a model and forgot the migration. That alone has saved me twice.

## 2. Deploy on main

The deploy job connects to the server over SSH and runs a script that:

- pulls the latest code
- builds the new image
- restarts the services
- calls the health check URL
- **rolls back** to the previous image if the check fails

```bash
if ! curl -fsS "$HEALTH_URL" > /dev/null; then
  docker tag blog:previous blog:latest
  docker compose up -d
  exit 1
fi
```

> Secrets live in GitHub Actions secrets, never in the repository. The server keeps its own `.env` file.""",
     12),

    ("DevOps", ["linux", "caddy", "https"], "bilal",
     "Free HTTPS for Side Projects with Caddy",
     "Caddy gets and renews Let's Encrypt certificates on its own. "
     "One small config file serves four projects from a single server.",
     """I used to spend an evening on Nginx and Certbot for every new project. With Caddy, HTTPS is a single line.

## The whole config

```text
blog.example.com {
    encode gzip
    reverse_proxy blog-web:8000
}
```

Caddy sees the domain, requests a certificate from Let's Encrypt, renews it before it expires and redirects HTTP to HTTPS.

## Several projects, one server

Each project runs in its own compose stack, but they all join a shared Docker network called `edge`. Caddy sits on that network and routes by domain name:

- `blog.example.com` to `blog-web:8000`
- `shop.example.com` to `shop-web:8000`
- `chat.example.com` to `chat-web:8000`

Prefix service names per project so two stacks never fight over the name `web`.

## WebSockets just work

Caddy forwards `Upgrade` headers by default, so Django Channels needs no extra config.""",
     8),

    ("Frontend", ["ux", "css", "typography"], "ayesha",
     "Designing a Blog Layout People Actually Finish Reading",
     "Line length, spacing, contrast and a few quiet animations. "
     "Small typographic choices matter more than any hero image.",
     """Most readers leave an article because it is tiring to read, not because it is boring. These are the rules I follow.

## Line length

Keep body text between **60 and 80 characters** per line. On wide screens, cap the content width instead of letting text stretch edge to edge.

```css
.article { max-width: 72ch; margin: 0 auto; }
```

## Spacing and rhythm

- Body line height around 1.7 to 1.8
- More space above a heading than below it, so it belongs to the text that follows
- Paragraph spacing roughly equal to the line height

## Contrast

Pure black on pure white is harsh. A very dark slate like `#0f172a` on white is easier on the eyes and still passes WCAG AA comfortably.

## Motion, gently

A card that lifts a few pixels on hover or fades in while scrolling makes a page feel alive. Anything longer than about 400 ms starts to feel slow.

```css
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
```

> Respect `prefers-reduced-motion`. Some readers get motion sick.""",
     30),

    ("Frontend", ["javascript", "ux", "performance"], "ayesha",
     "Infinite Scroll Without a Framework",
     "Load the next page of posts with IntersectionObserver and fetch. "
     "Server-rendered pages keep working without JavaScript.",
     """You do not need React to load more posts as the reader scrolls. Thirty lines of plain JavaScript are enough.

## The idea

Put an empty sentinel element after the list. When it scrolls into view, fetch the next page, take the cards out of the returned HTML and append them.

```javascript
const observer = new IntersectionObserver(async ([entry]) => {
  if (!entry.isIntersecting || !nextUrl) return;
  const html = await (await fetch(nextUrl)).text();
  const doc = new DOMParser().parseFromString(html, "text/html");
  list.append(...doc.querySelectorAll(".post-card"));
  nextUrl = doc.querySelector("[data-next]")?.dataset.next;
});
observer.observe(sentinel);
```

## Why server-rendered HTML

- The normal paginated page still works with JavaScript disabled
- Search engines see real links
- No duplicate templates for JSON and HTML

## Do not forget

- Show a small loading indicator
- Stop observing when there is no next page
- Update the URL with `history.replaceState` so refresh keeps the position""",
     16),

    ("Data", ["python", "sql", "analytics"], "usman",
     "Building an Analytics Dashboard Without Slowing Down Your App",
     "Counting likes, views and comments on every page load gets expensive. "
     "Precompute the numbers in Celery and serve them from Redis instead.",
     """The admin dashboard on this blog shows total users, posts, views, likes and the top categories. Calculating that on every request would mean several heavy aggregate queries each time someone opens the page.

## Precompute, then cache

A Celery Beat task runs every hour, calculates everything once and stores the result in Redis:

```python
@shared_task
def calculate_dashboard_analytics():
    data = {
        "total_posts": BlogPost.objects.count(),
        "total_views": BlogPost.objects.aggregate(v=Sum("views"))["v"] or 0,
        "top_categories": list(
            Category.objects.annotate(n=Count("posts")).values("name", "n")[:5]
        ),
    }
    cache.set("dashboard_analytics", data, timeout=None)
```

The view then does a single `cache.get`.

## A fallback for the first request

Right after a deploy the cache is empty. The view checks for that and runs the calculation once, so the very first visitor never sees an empty chart.

## Charts

`Chart.js` takes the numbers straight from the template context. A doughnut chart for categories and a bar chart for engagement cover most needs.

> Ask what decision a chart helps someone make. If there is no answer, it probably does not belong on the dashboard.""",
     5),

    ("Data", ["postgresql", "search"], "usman",
     "Full-Text Search in PostgreSQL from Django",
     "Before reaching for Elasticsearch, try SearchVector and SearchRank. "
     "For a blog with thousands of posts they are more than enough.",
     """Searching posts with `icontains` works until you have a few thousand rows and want results ranked by relevance.

## SearchVector and SearchRank

```python
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

vector = SearchVector("title", weight="A") + SearchVector("content", weight="B")
query = SearchQuery(term)
results = (
    BlogPost.objects.annotate(rank=SearchRank(vector, query))
    .filter(rank__gte=0.1)
    .order_by("-rank")
)
```

Titles get weight **A**, so a match in the title ranks above a match buried in the body.

## Make it fast

- Store the vector in a `SearchVectorField`
- Add a `GinIndex` on that field
- Update it with a database trigger or in `save()`

## When to move on

If you need typo tolerance, synonyms across languages or faceted search over millions of documents, that is when a dedicated search engine earns its operational cost.""",
     2),

    ("Career", ["career", "portfolio"], "bilal",
     "What I Look for in a Junior Developer Portfolio",
     "After reviewing dozens of applications: a live demo, tests and a clear README "
     "beat a long list of tutorial projects every time.",
     """I review a lot of junior applications. The ones that get an interview usually have the same three things.

## 1. Something I can click

A live link removes all doubt. If the project needs a login, give me a demo account or a one-click demo button. Most reviewers will not clone and run your repo.

## 2. Evidence it works

- A test suite, even a small one
- A CI badge that is green
- A short note on what you would improve next

## 3. A README written for a busy person

- One sentence on what it is
- A screenshot or GIF
- The stack
- How to run it locally in three commands

> Three finished, deployed projects tell me more than ten half-finished ones.

## What matters less than you think

Fancy animations, a huge number of technologies and a perfect commit history. Show that you can finish something and explain your trade-offs.""",
     1),
]

DRAFTS = [
    ("Backend", "sara", "Caching Strategies with Redis",
     "Per-view caching, the low-level cache API and invalidation.",
     "Notes in progress: per-view caching, template fragment caching and cache invalidation on save.",
     None),
    ("DevOps", "bilal", "Zero-Downtime Deploys with Docker Compose",
     "Health checks, rolling restarts and safe migrations.",
     "Scheduled post: publishes automatically through Celery Beat.",
     2),
]

COMMENTS = [
    "This is exactly the problem I had in production last week. The query-count test is a great idea.",
    "Clear and to the point. Bookmarked for the next time I set this up.",
    "Would love a follow-up post on how you test this part.",
    "I tried this on my side project and it just worked. Thanks for writing it up!",
    "Great explanation. The code examples make it really easy to follow.",
    "We use almost the same setup at work. One thing I would add is monitoring.",
    "Finally an article that explains the why and not just the how.",
    "Shared this with my team. Short, practical and no fluff.",
    "Do you have a sample repository for this?",
    "The section about common mistakes saved me a lot of debugging time.",
    "Nice write-up. How does this behave with a lot more traffic?",
    "Simple and well structured. More posts like this please!",
]
