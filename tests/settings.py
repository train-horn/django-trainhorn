"""Minimal settings for running the django-trainhorn test-suite."""

SECRET_KEY = "django-trainhorn-tests-only"
DEBUG = False
ALLOWED_HOSTS = ["testserver"]
INSTALLED_APPS = ["trainhorn"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
ROOT_URLCONF = "tests.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {"string_if_invalid": "INVALID"},
    }
]
USE_TZ = True
