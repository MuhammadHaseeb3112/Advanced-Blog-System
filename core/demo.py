"""Public demo mode (DEMO_MODE=True).

The live demo uses shared demo accounts, so anything that would lock other
visitors out or needs real email is switched off: sign-up, password and
profile changes, password reset and Django's /admin/. Everything else (writing,
editing and deleting posts, likes, comments, live notifications) works, and the
data is reset every night with `manage.py seed_demo --reset`.
"""
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect

DEMO_PASSWORD = "DemoPass123!"
DEMO_ACCOUNTS = [
    {"label": "Author", "email": "sara@demo.blog", "hint": "Write, schedule and manage posts"},
    {"label": "Reader", "email": "reader@demo.blog", "hint": "Like, bookmark and comment"},
    {"label": "Admin", "email": "admin@demo.blog", "hint": "Analytics and moderation (read-only)"},
]
# The shared admin account can open every page but cannot change anything,
# so all visitors see the same clean demo.
READ_ONLY_EMAILS = {"admin@demo.blog"}
ALLOWED_WHILE_READ_ONLY = ("/accounts/logout/", "/accounts/login/")

# Paths that are blocked for every method.
BLOCKED_ALWAYS = ("/admin/",)
# Paths where only reading (GET) is allowed.
READ_ONLY = (
    "/accounts/signup/",
    "/accounts/password-reset/",
    "/accounts/reset/",
    "/accounts/password/",
    "/accounts/email/",
    "/accounts/profile/",
    "/profile/",
    "/api/register/",
    "/api/change-password/",
    "/api/profile/update/",
)


class DemoModeMiddleware:
    message = "This is a public demo: account changes are turned off. Use the demo logins."
    read_only_message = "The demo admin is read-only: browse everything, but changes are not saved."

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.DEMO_MODE:
            return self.get_response(request)
        if self.read_only_write(request) or self.read_only_token(request):
            return self.reject(request, self.read_only_message, back=True)
        if self.blocked(request):
            return self.reject(request, self.message)
        return self.get_response(request)

    @staticmethod
    def read_only_write(request):
        user = getattr(request, "user", None)
        return (
            request.method not in ("GET", "HEAD", "OPTIONS")
            and user is not None
            and user.is_authenticated
            and user.email in READ_ONLY_EMAILS
            and not request.path.startswith(ALLOWED_WHILE_READ_ONLY)
        )

    @staticmethod
    def read_only_token(request):
        """Do not hand out API tokens for the read-only account."""
        if request.method != "POST" or not request.path.startswith("/api/token/"):
            return False
        if request.path.startswith("/api/token/refresh"):
            return False
        body = request.body.decode("utf-8", "ignore").lower()
        return any(email in body for email in READ_ONLY_EMAILS)

    def reject(self, request, text, back=False):
        wants_json = (
            request.path.startswith("/api/")
            or request.headers.get("x-requested-with") == "XMLHttpRequest"
            or "application/json" in request.headers.get("accept", "")
            or request.path.rstrip("/").rsplit("/", 1)[-1] in ("like", "bookmark", "comment")
        )
        if wants_json:
            return JsonResponse({"success": False, "message": text}, status=403)
        messages.info(request, text)
        if back and request.headers.get("referer"):
            return redirect(request.headers["referer"])
        return redirect("login")

    @staticmethod
    def blocked(request):
        path = request.path
        if path.startswith(BLOCKED_ALWAYS):
            return True
        if path.startswith("/accounts/signup/"):
            return True
        return request.method != "GET" and path.startswith(READ_ONLY)


def demo(request):
    """Template context: demo flag and the one-click demo accounts."""
    if not settings.DEMO_MODE:
        return {"demo_mode": False}
    return {
        "demo_mode": True,
        "demo_accounts": DEMO_ACCOUNTS,
        "demo_password": DEMO_PASSWORD,
    }
