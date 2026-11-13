import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default):
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def env_int(name, default):
    return int(os.getenv(name, default))


# ------------------------------------------------------------------ core
DEFAULT_DEV_KEY = "dev-only-insecure-key-change-me"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", DEFAULT_DEV_KEY)
DEBUG = env_bool("DJANGO_DEBUG", True)
if not DEBUG and SECRET_KEY == DEFAULT_DEV_KEY:
    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY in .env when DJANGO_DEBUG is off.")

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "research",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        # the background worker writes while pages are read: wait instead of failing
        "OPTIONS": {"timeout": 30},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "research:home"
LOGOUT_REDIRECT_URL = "login"

# Generated PDF/Word files live here. They are NOT served directly:
# research.views.download checks that the file belongs to the logged-in user.
MEDIA_ROOT = BASE_DIR / "media"

# ------------------------------------------------------------------ research agent
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3:4b")
LLM_API_KEY = os.getenv("LLM_API_KEY", "ollama")

RESEARCH_MAX_STEPS = env_int("RESEARCH_MAX_STEPS", 6)
RESEARCH_MAX_PAGE_CHARS = env_int("RESEARCH_MAX_PAGE_CHARS", 4000)
RESEARCH_WORKERS = env_int("RESEARCH_WORKERS", 1)
RESEARCH_MAX_ACTIVE_PER_USER = env_int("RESEARCH_MAX_ACTIVE_PER_USER", 2)
RESEARCH_MAX_PER_DAY = env_int("RESEARCH_MAX_PER_DAY", 20)
RESEARCH_JOB_TIMEOUT_MINUTES = env_int("RESEARCH_JOB_TIMEOUT_MINUTES", 20)
RESEARCH_ALLOW_SIGNUP = env_bool("RESEARCH_ALLOW_SIGNUP", True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"research": {"handlers": ["console"], "level": "INFO"}},
}
