"""Django settings loaded from environment variables (see docker-compose)."""

import sys
from datetime import timedelta
from pathlib import Path

import environ
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Trust the nginx gateway (TLS will set X-Forwarded-Proto=https in production).
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost",
        "http://127.0.0.1",
    ],
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "apps.catalog",
    "apps.sources",
    "apps.trends",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # ETag + 304 on the radar JSON: phones on metered data skip unchanged payloads.
    "django.middleware.http.ConditionalGetMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="firona"),
        "USER": env("POSTGRES_USER", default="firona"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="firona"),
        "HOST": env("POSTGRES_HOST", default="db"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr"
TIME_ZONE = "Indian/Antananarivo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Same-origin through nginx in Docker; keep CORS for local `npm run dev`.
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
)

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}

REDIS_URL = env("REDIS_URL", default="redis://redis:6379/0")
TESTING = "test" in sys.argv[1:2]

# Cache: collect lock, hourly request budgets, worker heartbeat.
# Redis DB 1 so it never mixes with the Celery broker (DB 0).
CACHES = {
    "default": (
        {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
        if TESTING
        else {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": env("REDIS_CACHE_URL", default="redis://redis:6379/1"),
            "KEY_PREFIX": "firona",
            "TIMEOUT": 300,
        }
    )
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TIMEZONE = TIME_ZONE
CELERY_RESULT_EXPIRES = 24 * 3600
# A task is acknowledged only once done: a killed worker hands it back to the queue.
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BEAT_SCHEDULE = {
    "collect-legal-sources": {
        "task": "apps.trends.tasks.collect_legal_sources",
        "schedule": timedelta(hours=6),
        # If the worker was down, drop the stale run instead of piling them up.
        "options": {"expires": 3 * 3600},
    },
    "worker-heartbeat": {
        "task": "apps.trends.tasks.heartbeat",
        "schedule": timedelta(minutes=5),
        "options": {"expires": 240},
    },
    "prune-collection-runs": {
        "task": "apps.trends.tasks.prune_collection_runs",
        "schedule": crontab(hour=3, minute=30),
        "options": {"expires": 6 * 3600},
    },
}

# v3 collectors (empty token = skip Ads Library HTTP, mark_error).
META_ADS_ACCESS_TOKEN = env("META_ADS_ACCESS_TOKEN", default="")
META_GRAPH_API_VERSION = env("META_GRAPH_API_VERSION", default="v21.0")

# v4 robustness (see docs/workers.md).
COLLECT_HTTP_TIMEOUT = env.int("COLLECT_HTTP_TIMEOUT", default=20)
COLLECT_HTTP_ATTEMPTS = env.int("COLLECT_HTTP_ATTEMPTS", default=3)
COLLECT_RETRY_BASE_S = env.float("COLLECT_RETRY_BASE_S", default=1.0)
COLLECT_RETRY_CAP_S = env.float("COLLECT_RETRY_CAP_S", default=20.0)
COLLECT_BUDGET_PER_HOUR = {
    "meta_ads": env.int("COLLECT_BUDGET_META_ADS", default=150),
    "google_trends": env.int("COLLECT_BUDGET_GOOGLE_TRENDS", default=20),
    "default": 60,
}
COLLECT_SOFT_TIME_LIMIT = env.int("COLLECT_SOFT_TIME_LIMIT", default=900)
COLLECT_RUN_RETENTION_DAYS = env.int("COLLECT_RUN_RETENTION_DAYS", default=90)
# /api/v1/status/ thresholds.
STATUS_STALE_HOURS = env.int("STATUS_STALE_HOURS", default=13)
STATUS_HEARTBEAT_MAX_AGE_S = env.int("STATUS_HEARTBEAT_MAX_AGE_S", default=900)
STATUS_QUEUE_WARN = env.int("STATUS_QUEUE_WARN", default=50)

LOG_LEVEL = env("LOG_LEVEL", default="INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "filters": {
        # Last line of defence: no token / bearer / secret reaches stdout.
        "redact": {"()": "apps.sources.redact.RedactingFilter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "plain",
            "filters": ["redact"],
        },
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        # httpx logs full request URLs at INFO, query-string tokens included.
        "httpx": {"level": "WARNING"},
        "httpcore": {"level": "WARNING"},
        "django.db.backends": {"level": "WARNING"},
    },
}
