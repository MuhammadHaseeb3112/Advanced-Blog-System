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
]

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

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEMO_MODE and self.blocked(request):
            if request.path.startswith("/api/"):
                return JsonResponse({"success": False, "message": self.message}, status=403)
            messages.info(request, self.message)
            return redirect("login")
        return self.get_response(request)

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
