"""Vendored copy of the trainhorn-calc 1.0.0 core (MIT).

Upstream: https://github.com/train-horn/trainhorn-calc

The modules here are byte-for-byte copies of ``trainhorn_calc`` 1.0.0
(``_validate``, ``acoustics``, ``airsystem``, ``electrical``) so that
django-trainhorn needs nothing but Django. The test-suite checks this copy
against the upstream reference vectors.
"""

from __future__ import annotations

from ._validate import InputError
from .acoustics import combine_levels, db_doubling_loss, distance_for_spl, distance_ratio_loss, spl_at_distance
from .airsystem import blast_count, compressor_recovery_seconds, free_air_volume_cuft, tank_runtime_seconds
from .electrical import AWG_SIZES, WireSuggestion, awg_resistance_ohm_per_1000ft, suggest_awg, voltage_drop

CORE_VERSION = "1.0.0"

__all__ = [
    "CORE_VERSION",
    "InputError",
    "spl_at_distance",
    "distance_for_spl",
    "distance_ratio_loss",
    "db_doubling_loss",
    "combine_levels",
    "free_air_volume_cuft",
    "tank_runtime_seconds",
    "blast_count",
    "compressor_recovery_seconds",
    "AWG_SIZES",
    "awg_resistance_ohm_per_1000ft",
    "voltage_drop",
    "suggest_awg",
    "WireSuggestion",
]
