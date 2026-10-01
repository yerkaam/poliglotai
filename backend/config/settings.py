"""PoliglotAi — Django settings. All secrets and environment-specific values come from env vars."""

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).lower() in {"1", "true", "yes", "on"}


# Safe by default: debug mode must be switched on explicitly (DJANGO_DEBUG=1 for local development),
# and without debug the app refuses to start on the public development key.
DEBUG = env_bool("DJANGO_DEBUG", False)
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("Set DJANGO_SECRET_KEY (or DJANGO_DEBUG=1 for local development).")
    SECRET_KEY = "dev-insecure-key-change-me-in-production-0123456789"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
CSRF_TRUSTED_ORIGINS = [
    o for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:4200").split(",") if o
]
# Render publishes the service's public hostname; trust it automatically.
RENDER_HOST = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
if RENDER_HOST:
    ALLOWED_HOSTS.append(RENDER_HOST)
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_HOST}")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "users",
    "vocabulary",
    "srs",
    "trainer",
    "chat",
    "progress",
    "classroom",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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
    "default": dj_database_url.parse(os.environ["DATABASE_URL"], conn_max_age=60)
    if os.environ.get("DATABASE_URL")
    else {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "poliglot"),
        "USER": os.environ.get("POSTGRES_USER", "poliglot"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "poliglot"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "users.validators.HasDigitValidator"},
]

# Reset links live 1 hour (AUTH-10). Tokens are single-use because they hash the password.
PASSWORD_RESET_TIMEOUT = 60 * 60

LANGUAGE_CODE = "kk"
TIME_ZONE = os.environ.get("TIME_ZONE", "Asia/Almaty")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["users.authentication.CookieJWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["users.permissions.IsVerified"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "reset_email": "1/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "UPDATE_LAST_LOGIN": True,
}

AUTH_COOKIE_SECURE = env_bool("AUTH_COOKIE_SECURE", not DEBUG)
AUTH_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = AUTH_COOKIE_SECURE
SESSION_COOKIE_SECURE = AUTH_COOKIE_SECURE
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Email confirmation with a 6-digit code after registration.
REQUIRE_EMAIL_VERIFICATION = env_bool("REQUIRE_EMAIL_VERIFICATION", True)
EMAIL_CODE_TTL_MINUTES = 10
EMAIL_CODE_MAX_ATTEMPTS = 5
# Fixed code for local end-to-end tests; ignored unless DEBUG is on.
EMAIL_CODE_OVERRIDE = os.environ.get("EMAIL_CODE_OVERRIDE", "") if DEBUG else ""

# Login brute-force protection (AUTH-09).
LOGIN_MAX_FAILURES = 5
LOGIN_MAX_FAILURES_PER_IP = 30
# How many of our own proxies add an X-Forwarded-For entry (Render: 1). 0 trusts only REMOTE_ADDR.
TRUSTED_PROXY_COUNT = int(os.environ.get("TRUSTED_PROXY_COUNT", "0"))
LOGIN_LOCKOUT_SECONDS = 15 * 60

# Login lockout and chat limits need a cache shared by all gunicorn workers:
# Redis when available, otherwise a database table (run `createcachetable`).
if os.environ.get("REDIS_URL"):
    _cache = {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": os.environ["REDIS_URL"]}
elif DEBUG:
    _cache = {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
else:
    _cache = {"BACKEND": "django.core.cache.backends.db.DatabaseCache", "LOCATION": "cache_table"}
CACHES = {"default": _cache}

# Single-image deploy: Django also serves the built Angular app from this folder.
SPA_DIR = os.environ.get("SPA_DIR", "")
if SPA_DIR:
    WHITENOISE_ROOT = SPA_DIR
# The web app manifest needs its own type, or browsers may not offer to install the app.
WHITENOISE_MIMETYPES = {".webmanifest": "application/manifest+json"}

EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "PoliglotAi <no-reply@poliglot.ai>")
# Links in emails (password reset, reminders). On Render the service's own address unless set explicitly.
FRONTEND_URL = os.environ.get("FRONTEND_URL") or (f"https://{RENDER_HOST}" if RENDER_HOST else "http://localhost:4200")

# AI chat. The key never leaves the server. Without a key the chat uses an offline tutor stub.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CHAT_MODEL = os.environ.get("CHAT_MODEL", "claude-opus-5")
CHAT_EFFORT = os.environ.get("CHAT_EFFORT", "low")
CHAT_DAILY_LIMIT = int(os.environ.get("CHAT_DAILY_LIMIT", "30"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
