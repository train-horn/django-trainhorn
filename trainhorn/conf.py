"""App settings, read from the optional ``TRAINHORN`` dict in Django settings.

Example::

    TRAINHORN = {
        "DEFAULT_UNIT": "m",
        "DEFAULT_REF_DISTANCE": 1,
        "DEFAULT_SYSTEM_VOLTAGE": 24,
        "DEFAULT_MAX_DROP_PCT": 3,
        "DECIMALS": 1,
    }

Every key is optional. Values are read on each call, so ``override_settings``
works in tests.
"""

from __future__ import annotations

from typing import Any, Dict

from django.conf import settings

DEFAULTS: Dict[str, Any] = {
    # Unit for distances and wire runs: "ft" or "m".
    "DEFAULT_UNIT": "ft",
    # Distance at which a horn's rated dB applies (in DEFAULT_UNIT).
    "DEFAULT_REF_DISTANCE": 10,
    # Nominal vehicle system voltage for the wire gauge calculator.
    "DEFAULT_SYSTEM_VOLTAGE": 12,
    # Allowed voltage drop in percent for the wire gauge calculator.
    "DEFAULT_MAX_DROP_PCT": 3,
    # Decimal places used by template filters and result pages.
    "DECIMALS": 1,
}


def user_settings() -> Dict[str, Any]:
    """Return the raw ``TRAINHORN`` setting (an empty dict when unset)."""
    value = getattr(settings, "TRAINHORN", None)
    return {} if value is None else value


def get(name: str) -> Any:
    """Return setting ``name``, falling back to :data:`DEFAULTS`."""
    if name not in DEFAULTS:
        raise KeyError(f"unknown django-trainhorn setting {name!r}")
    raw = user_settings()
    if isinstance(raw, dict) and name in raw:
        return raw[name]
    return DEFAULTS[name]
