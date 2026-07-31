"""Django settings for online-biotools."""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-only-change-me-online-biotools-not-for-production",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.portal",
    "apps.annotations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.annotations.middleware.RequestContextMiddleware",
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
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_THROTTLE_RATES": {
        "annotation": os.environ.get("BIOTOOLS_ANNOTATION_RATE", "30/min"),
    },
}

# Request limits
DATA_UPLOAD_MAX_MEMORY_SIZE = int(
    os.environ.get("DATA_UPLOAD_MAX_MEMORY_SIZE", str(2 * 1024 * 1024))
)
DATA_UPLOAD_MAX_NUMBER_FIELDS = int(os.environ.get("DATA_UPLOAD_MAX_NUMBER_FIELDS", "1000"))

# Auth / ops
# Comma-separated keys. When non-empty (or BIOTOOLS_REQUIRE_API_KEY=1), POST annotate requires X-API-Key.
BIOTOOLS_API_KEYS = os.environ.get("BIOTOOLS_API_KEYS", "")
BIOTOOLS_REQUIRE_API_KEY = os.environ.get("BIOTOOLS_REQUIRE_API_KEY", "0") == "1"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "format": "%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
        },
    },
    "loggers": {
        "biotools.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# --- Annotation engines ---
VEP_BIN = os.environ.get("VEP_BIN", "/opt/vep/src/ensembl-vep/vep")
VEP_CACHE_DIR = os.environ.get("VEP_CACHE_DIR", str(BASE_DIR / "data" / "vep"))
VEP_ASSEMBLY_DEFAULT = os.environ.get("VEP_ASSEMBLY", "GRCh37")
VEP_TIMEOUT_SECONDS = int(os.environ.get("VEP_TIMEOUT_SECONDS", "300"))
VEP_MAX_CONCURRENCY = int(os.environ.get("VEP_MAX_CONCURRENCY", "2"))
ANNOTATION_MAX_VARIANTS = int(os.environ.get("ANNOTATION_MAX_VARIANTS", "200"))

# assembly -> relative cache subdirectory under VEP_CACHE_DIR (manifest-aligned)
VEP_ASSEMBLY_CACHE = {
    "GRCh37": os.environ.get("VEP_CACHE_GRCh37", "homo_sapiens_merged/116_GRCh37"),
    "GRCh38": os.environ.get("VEP_CACHE_GRCh38", "homo_sapiens_merged/116_GRCh38"),
}

# ANNOVAR (local perl or dockerized CLI)
ANNOVAR_MODE = os.environ.get("ANNOVAR_MODE", "auto")  # auto|local|docker
ANNOVAR_DB_DIR = os.environ.get(
    "ANNOVAR_DB_DIR",
    str(BASE_DIR / "data" / "annovar-hg38"),
)
ANNOVAR_TABLE_BIN = os.environ.get(
    "ANNOVAR_TABLE_BIN",
    "/home/TOOLS/tools/annovar/current/bin/table_annovar.pl",
)
ANNOVAR_DOCKER_IMAGE = os.environ.get(
    "ANNOVAR_DOCKER_IMAGE",
    "registry.cn-shanghai.aliyuncs.com/kszy-biosoft/annovar:v20180416_2",
)
ANNOVAR_TIMEOUT_SECONDS = int(os.environ.get("ANNOVAR_TIMEOUT_SECONDS", "300"))
ANNOVAR_MAX_CONCURRENCY = int(os.environ.get("ANNOVAR_MAX_CONCURRENCY", "1"))
ANNOVAR_VERSION_LABEL = os.environ.get("ANNOVAR_VERSION_LABEL", "2018-04-16")
# Gate public/online ANNOVAR usage until license is confirmed by the operator.
ANNOVAR_PUBLIC_ENABLED = os.environ.get("ANNOVAR_PUBLIC_ENABLED", "0") == "1"
