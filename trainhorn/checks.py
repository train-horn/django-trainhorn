"""System checks for the ``TRAINHORN`` setting (run by ``manage.py check``).

IDs:

* ``trainhorn.E001`` ``TRAINHORN`` is not a dict.
* ``trainhorn.E002`` ``DEFAULT_UNIT`` is not ``"ft"`` or ``"m"``.
* ``trainhorn.E003`` a numeric setting is not a positive number.
* ``trainhorn.E004`` ``DEFAULT_MAX_DROP_PCT`` is above 50.
* ``trainhorn.E005`` ``DECIMALS`` is not an integer from 0 to 6.
* ``trainhorn.W001`` unknown key (probably a typo).
"""

from __future__ import annotations

import math
from typing import Any, List, Optional, Sequence

from django.apps import AppConfig
from django.core.checks import Error, Tags, Warning, register

from . import conf

_POSITIVE_NUMBERS = ("DEFAULT_REF_DISTANCE", "DEFAULT_SYSTEM_VOLTAGE", "DEFAULT_MAX_DROP_PCT")


def _is_positive_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value) and value > 0


@register(Tags.compatibility)
def check_settings(app_configs: Optional[Sequence[AppConfig]] = None, **kwargs: Any) -> List[Any]:
    """Validate the ``TRAINHORN`` settings dict."""
    raw = conf.user_settings()
    if not isinstance(raw, dict):
        return [
            Error(
                "TRAINHORN must be a dict.",
                hint="Use for example TRAINHORN = {'DEFAULT_UNIT': 'ft'} or remove the setting.",
                id="trainhorn.E001",
            )
        ]

    messages: List[Any] = []
    for key in sorted(set(raw) - set(conf.DEFAULTS)):
        messages.append(
            Warning(
                f"Unknown TRAINHORN key {key!r}.",
                hint="Valid keys: " + ", ".join(sorted(conf.DEFAULTS)) + ".",
                id="trainhorn.W001",
            )
        )

    unit = conf.get("DEFAULT_UNIT")
    if unit not in ("ft", "m"):
        messages.append(
            Error(f"TRAINHORN['DEFAULT_UNIT'] must be 'ft' or 'm', got {unit!r}.", id="trainhorn.E002")
        )

    for key in _POSITIVE_NUMBERS:
        value = conf.get(key)
        if not _is_positive_number(value):
            messages.append(
                Error(f"TRAINHORN[{key!r}] must be a positive number, got {value!r}.", id="trainhorn.E003")
            )

    drop = conf.get("DEFAULT_MAX_DROP_PCT")
    if _is_positive_number(drop) and drop > 50:
        messages.append(
            Error(f"TRAINHORN['DEFAULT_MAX_DROP_PCT'] must be 50 or less, got {drop!r}.", id="trainhorn.E004")
        )

    decimals = conf.get("DECIMALS")
    if isinstance(decimals, bool) or not isinstance(decimals, int) or not 0 <= decimals <= 6:
        messages.append(
            Error(f"TRAINHORN['DECIMALS'] must be an integer from 0 to 6, got {decimals!r}.", id="trainhorn.E005")
        )
    return messages
