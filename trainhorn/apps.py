"""Django app configuration for django-trainhorn."""

from __future__ import annotations

from django.apps import AppConfig


class TrainhornConfig(AppConfig):
    """App config; registers the settings system check on startup."""

    name = "trainhorn"
    label = "trainhorn"
    verbose_name = "Train horn calculators"
    default_auto_field = "django.db.models.AutoField"

    def ready(self) -> None:
        from . import checks  # noqa: F401  (registers the checks)
