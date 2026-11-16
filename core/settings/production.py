"""Production settings, configured from environment variables.

Runs behind a reverse proxy (Caddy) that terminates HTTPS and forwards
X-Forwarded-Proto, so Django does not redirect to HTTPS itself.
"""
import os

from .base import *  # noqa: F401,F403


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


DEBUG = False

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

# HTTPS is handled by the proxy in front of the app.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = env_bool("SECURE_COOKIES", True)
CSRF_COOKIE_SECURE = env_bool("SECURE_COOKIES", True)
SECURE_HSTS_SECONDS = 31536000
SECURE_REFERRER_POLICY = "same-origin"

SITE_URL = f"https://{ALLOWED_HOSTS[0]}" if ALLOWED_HOSTS else SITE_URL  # noqa: F405

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Public demo: shared demo accounts, no outgoing email (see core/demo.py).
if DEMO_MODE:  # noqa: F405
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# HTTPS redirects and HSTS are set by the proxy for this one host only.
SILENCED_SYSTEM_CHECKS = ["security.W005", "security.W008", "security.W021"]
