from .base import *
import os

DEBUG = False

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "*"
).split(",")

SECURE_SSL_REDIRECT = True

SESSION_COOKIE_SECURE = True

CSRF_COOKIE_SECURE = True

# =====================================
# CSRF TRUSTED ORIGINS
# =====================================

CSRF_TRUSTED_ORIGINS = []

render_url = os.getenv(
    "RENDER_EXTERNAL_URL"
)

if render_url:

    if not render_url.startswith(
        "http"
    ):
        render_url = (
            f"https://{render_url}"
        )

    CSRF_TRUSTED_ORIGINS.append(
        render_url
    )

# =====================================
# SECURITY HEADERS
# =====================================

SECURE_HSTS_SECONDS = 31536000

SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SECURE_HSTS_PRELOAD = True