"""
Django settings for the wagtail-starling test suite.

Minimal harness: the package tests were never runnable before the captcha
extraction (no DJANGO_SETTINGS_MODULE anywhere). Keep this thin — it exists
so pytest-django can build a schema for the shared modules.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = "starling-tests-secret-key"
DEBUG = True
ALLOWED_HOSTS = ["localhost", "testserver"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "taggit",
    "wagtail",
    "wagtail.admin",
    "wagtail.documents",
    "wagtail.snippets",
    "wagtail.users",
    "wagtail.images",
    "wagtail.embeds",
    "wagtail.search",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.settings",
    "wagtail_starling",
    "wagtail_starling.captcha",
    "django_recaptcha",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "wagtail.contrib.settings.context_processors.settings",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ROOT_URLCONF = "tests.urls"

SITE_ID = 1

USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

STATIC_URL = "static/"
WAGTAILADMIN_BASE_URL = "http://localhost:8000"

# Bot-gate defaults mirror a dev checkout: Cloudflare's documented test
# secrets, so TurnstileField decides dev behavior identically to medan's.
TURNSTILE_SITE_KEY = "1x00000000000000000000AA"
TURNSTILE_SECRET_KEY = "1x0000000000000000000000000000000AA"

# reCAPTCHA well-known test pair, so the recaptcha field types behave like
# the medan PR's dev defaults and system checks stay quiet.
RECAPTCHA_PUBLIC_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
RECAPTCHA_PRIVATE_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
RECAPTCHA_REQUIRED_SCORE = 0.7
SILENCED_SYSTEM_CHECKS = ["django_recaptcha.recaptcha_test_key_error"]
