from pathlib import Path
import environ
import os
from datetime import timedelta


# =========================
# BASE DIRECTORY
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =========================
# ENVIRONMENT VARIABLES
# =========================

env = environ.Env()

environ.Env.read_env(
    os.path.join(BASE_DIR, '.env')
)


# =========================
# SECURITY
# =========================

SECRET_KEY = env('SECRET_KEY')

# DEBUG = env.bool('DEBUG')

# ALLOWED_HOSTS = [
#     '127.0.0.1',
#     'localhost',
# ]

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost",
]


SESSION_ENGINE = "django.contrib.sessions.backends.db"


SESSION_COOKIE_AGE = 1209600
SESSION_EXPIRE_AT_BROWSER_CLOSE = False


# =========================
# APPLICATIONS
# =========================

INSTALLED_APPS = [


    'daphne',

    # Django Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Third Party Apps

    "allauth",
    "allauth.account",
    "allauth.socialaccount",

    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.github",
    

    "dj_rest_auth",

    # Channels
    'channels',

    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',

    # Local Apps
    'accounts',
    'api',
    'django_filters',
    'blog.apps.BlogConfig',
    'django_celery_beat',

    'corsheaders',

    'drf_yasg',
    'drf_spectacular',

]


SITE_ID = 1



# =========================
# AUTHENTICATION BACKENDS
# =========================

AUTHENTICATION_BACKENDS = [

    'django.contrib.auth.backends.ModelBackend',

    'allauth.account.auth_backends.AuthenticationBackend',
]

REST_AUTH = {
    "TOKEN_MODEL": None,
    "USE_JWT": True,
}


# =========================
# MIDDLEWARE
# =========================

MIDDLEWARE = [

    'django.middleware.security.SecurityMiddleware',

    'whitenoise.middleware.WhiteNoiseMiddleware',

    'corsheaders.middleware.CorsMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'allauth.account.middleware.AccountMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.demo.DemoModeMiddleware',
    
    
]


# =========================
# URLS & WSGI
# =========================

ROOT_URLCONF = 'core.urls'

WSGI_APPLICATION = 'core.wsgi.application'

ASGI_APPLICATION = 'core.asgi.application'

# =========================
# TEMPLATES
# =========================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [BASE_DIR / 'templates'],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [

                'django.template.context_processors.debug',

                'django.template.context_processors.request',

                'django.contrib.auth.context_processors.auth',

                'django.contrib.messages.context_processors.messages',

                'blog.context_processors.unread_notifications',
                'core.demo.demo',
            ],
        },
    },
]


# =========================
# DATABASE
# =========================


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': os.getenv('POSTGRES_PORT'),

        'CONN_MAX_AGE': 60,
    }
}

# =========================
# PASSWORD VALIDATION
# =========================

AUTH_PASSWORD_VALIDATORS = [

    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },

    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },

    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },

    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# =========================
# INTERNATIONALIZATION
# =========================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Karachi'

USE_TZ = True

USE_I18N = True




# =========================
# CUSTOM USER MODEL
# =========================

AUTH_USER_MODEL = 'accounts.CustomUser'


# =========================
# STATIC & MEDIA FILES
# =========================

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'


STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

STATICFILES_STORAGE = (
    'whitenoise.storage.CompressedManifestStaticFilesStorage'
)


MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'


# =========================
# LOGIN SETTINGS
# =========================

LOGIN_URL = 'login'

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'


# =========================
# DEFAULT PRIMARY KEY
# =========================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



ACCOUNT_LOGIN_METHODS = {"email"}

# =========================
# DJANGO ALLAUTH
# =========================

ACCOUNT_SIGNUP_FIELDS = [

    'email*',

    'username*',

    'password1*',

    'password2*',

]

ACCOUNT_EMAIL_VERIFICATION = 'mandatory'

LOGGING = {

    'version': 1,

    'disable_existing_loggers': False,

    'handlers': {

        'console': {
            'class': 'logging.StreamHandler',
        },

    },

    'root': {

        'handlers': ['console'],

        'level': 'INFO',

    },

}


SITE_URL = "http://localhost"



# =========================
# EMAIL CONFIGURATION
# =========================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = env('EMAIL_HOST', default='localhost')

EMAIL_PORT = env.int('EMAIL_PORT', default=25)

EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='noreply@example.com')

EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# =========================================
# DJANGO REST FRAMEWORK
# =========================================

REST_FRAMEWORK = {

    # =====================================
    # AUTHENTICATION
    # =====================================

    'DEFAULT_AUTHENTICATION_CLASSES': [

        'rest_framework_simplejwt.authentication.JWTAuthentication',

    ],

    # =====================================
    # PERMISSIONS
    # =====================================

    'DEFAULT_PERMISSION_CLASSES': [

        'rest_framework.permissions.IsAuthenticatedOrReadOnly',

    ],

    # =====================================
    # FILTERING
    # =====================================

    'DEFAULT_FILTER_BACKENDS': [

        'django_filters.rest_framework.DjangoFilterBackend',

        'rest_framework.filters.SearchFilter',

        'rest_framework.filters.OrderingFilter',

    ],

    # =====================================
    # PAGINATION
    # =====================================

    'DEFAULT_PAGINATION_CLASS':

        'api.pagination.custom_pagination.CustomPagination',

    'PAGE_SIZE': 10,



    'DEFAULT_SCHEMA_CLASS': (
        'drf_spectacular.openapi.AutoSchema'
    ),
    

    # =====================================
    # THROTTLING
    # =====================================

    'DEFAULT_THROTTLE_CLASSES': [

        'rest_framework.throttling.UserRateThrottle',

        'rest_framework.throttling.AnonRateThrottle',

    ],

    'DEFAULT_THROTTLE_RATES': {

        'user': '1000/day',

        'anon': '100/day',

    },

}


# =========================
# SIMPLE JWT SETTINGS
# =========================

SIMPLE_JWT = {

    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),

    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),

    'ROTATE_REFRESH_TOKENS': True,

    'BLACKLIST_AFTER_ROTATION': True,

    'UPDATE_LAST_LOGIN': True,
}

# =====================================
# REDIS CACHE
# =====================================

# Public demo mode (core/demo.py) and serving uploaded files from Django
# (for a single-server deploy without a separate media server).
DEMO_MODE = os.getenv('DEMO_MODE', 'False').lower() == 'true'
SERVE_MEDIA = os.getenv('SERVE_MEDIA', 'False').lower() == 'true'

# Redis host: "redis" inside Docker Compose, overridable for local runs and CI
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')

CACHES = {

    "default": {

        "BACKEND": "django_redis.cache.RedisCache",

        "LOCATION": f"redis://{REDIS_HOST}:6379/1",

        "OPTIONS": {
            "CLIENT_CLASS":
            "django_redis.client.DefaultClient",
        },

        "TIMEOUT": 300,

    }

}


# =====================================
# CELERY CONFIGURATION
# =====================================

CELERY_BROKER_URL = f'redis://{REDIS_HOST}:6379/0'

CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:6379/0'

CELERY_ACCEPT_CONTENT = [
    'json'
]

CELERY_TASK_SERIALIZER = 'json'

CELERY_RESULT_SERIALIZER = 'json'

CELERY_TIMEZONE = 'Asia/Karachi'

CELERY_ENABLE_UTC = False

# =====================================
# CELERY BEAT SCHEDULER
# =====================================

# Periodic jobs. The database scheduler loads these on start and they can be
# edited later in the Django admin (Periodic tasks).
CELERY_BEAT_SCHEDULE = {
    'publish-scheduled-posts': {
        'task': 'blog.tasks.publish_scheduled_posts',
        'schedule': 60.0,
    },
    'calculate-trending-posts': {
        'task': 'blog.tasks.calculate_trending_posts',
        'schedule': 30 * 60.0,
    },
    'calculate-dashboard-analytics': {
        'task': 'blog.tasks.calculate_dashboard_analytics',
        'schedule': 60 * 60.0,
    },
    'delete-old-notifications': {
        'task': 'blog.tasks.delete_old_notifications',
        'schedule': 24 * 60 * 60.0,
    },
    'weekly-recommendations': {
        'task': 'blog.tasks.send_weekly_blog_recommendations',
        'schedule': 7 * 24 * 60 * 60.0,
    },
}

CELERY_BEAT_SCHEDULER = (
    'django_celery_beat.schedulers:DatabaseScheduler'
)


# =====================================
# CHANNELS
# =====================================
CHANNEL_LAYERS = {

    'default': {

        'BACKEND': 'channels_redis.core.RedisChannelLayer',

        'CONFIG': {

            'hosts': [(REDIS_HOST, 6379)],

            "capacity": 1500,

            "expiry": 10,

        },

    },

}


SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'






SPECTACULAR_SETTINGS = {

    'TITLE': 'Advanced Blog System API',

    'DESCRIPTION': (
        'Professional Django REST API '
        'for Blogging Platform'
    ),

    'VERSION': '1.0.0',

    'SERVE_INCLUDE_SCHEMA': False,

}