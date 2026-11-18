"""Template filters and tags: ``{% load trainhorn %}``.

Filters take the main quantity as the value and the rest as a comma-separated
argument string. Numbers are rounded to ``TRAINHORN["DECIMALS"]`` (default 1).
Like Django's own filters they never raise: invalid input renders as an empty
string, so a bad value cannot break a page.

==========================  =================================================
``{{ 150|spl_at_distance:"100" }}``            dB at 100 (default unit, rated at DEFAULT_REF_DISTANCE)
``{{ 150|spl_at_distance:"10,100" }}``         dB at 100 for a rating at 10 -> 130.0
``{{ 150|spl_at_distance:"1,30,m" }}``         rating at 1 m, listener at 30 m
``{{ 150|distance_for_spl:"10,90" }}``         distance where the level falls to 90 dB
``{{ 5|tank_runtime:"150,110,10" }}``          seconds: 5 gal, 150 -> 110 psi, 10 CFM horn -> 10.9
``{{ 30|awg:"10" }}``                          smallest AWG for 30 A over 10 (one way) -> "6"
``{{ 30|awg:"10,24,3,ft" }}``                  same at 24 V, 3 % drop, feet
``{{ 30|voltage_drop:"10,8" }}``               volts lost for 30 A over 10 ft of 8 AWG
==========================  =================================================

Tag::

    {% trainhorn_wire 30 10 system_voltage=12 max_drop_pct=3 as wire %}
    {{ wire.awg }} AWG, {{ wire.voltage_drop_pct|floatformat:2 }} % drop
"""

from __future__ import annotations

from typing import Any, List, Optional, Union

from django import template

from .. import conf
from ..calc import InputError, WireSuggestion
from ..calc import distance_for_spl as _distance_for_spl
from ..calc import spl_at_distance as _spl_at_distance
from ..calc import suggest_awg as _suggest_awg
from ..calc import tank_runtime_seconds as _tank_runtime_seconds
from ..calc import voltage_drop as _voltage_drop

register = template.Library()

Result = Union[float, str]


def _args(arg: Any) -> List[str]:
    if arg is None:
        return []
    return [part.strip() for part in str(arg).split(",") if part.strip()]


def _round(value: float) -> float:
    return round(value, int(conf.get("DECIMALS")))


def _ref_quantity_unit(parts: List[str]) -> "tuple[Any, Any, str]":
    """Parse ``"x"``, ``"ref,x"`` or ``"ref,x,unit"``."""
    if len(parts) == 1:
        return conf.get("DEFAULT_REF_DISTANCE"), parts[0], conf.get("DEFAULT_UNIT")
    if len(parts) == 2:
        return parts[0], parts[1], conf.get("DEFAULT_UNIT")
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    raise InputError("expected 1 to 3 comma-separated values")


@register.filter
def spl_at_distance(source_db: Any, arg: Any) -> Result:
    """Level in dB at a distance: ``{{ 150|spl_at_distance:"10,100" }}`` -> 130.0."""
    try:
        ref, distance, unit = _ref_quantity_unit(_args(arg))
        return _round(_spl_at_distance(source_db, distance, ref, unit))
    except (InputError, TypeError, ValueError):
        return ""


@register.filter
def distance_for_spl(source_db: Any, arg: Any) -> Result:
    """Distance at which the level falls to a target: ``{{ 150|distance_for_spl:"10,130" }}`` -> 100.0."""
    try:
        ref, target, unit = _ref_quantity_unit(_args(arg))
        return _round(_distance_for_spl(source_db, target, ref, unit))
    except (InputError, TypeError, ValueError, OverflowError):
        return ""


@register.filter
def tank_runtime(tank_gallons: Any, arg: Any) -> Result:
    """Horn seconds from a tank: ``{{ 5|tank_runtime:"150,110,10" }}`` (start psi, cut-off psi, horn CFM)."""
    try:
        parts = _args(arg)
        if len(parts) != 3:
            raise InputError("expected start_psi,cutoff_psi,horn_cfm")
        return _round(_tank_runtime_seconds(tank_gallons, parts[0], parts[1], parts[2]))
    except (InputError, TypeError, ValueError):
        return ""


def _wire(amps: Any, parts: List[str]) -> WireSuggestion:
    if not 1 <= len(parts) <= 4:
        raise InputError("expected length[,system_voltage[,max_drop_pct[,unit]]]")
    length = parts[0]
    voltage = parts[1] if len(parts) > 1 else conf.get("DEFAULT_SYSTEM_VOLTAGE")
    drop = parts[2] if len(parts) > 2 else conf.get("DEFAULT_MAX_DROP_PCT")
    unit = parts[3] if len(parts) > 3 else conf.get("DEFAULT_UNIT")
    return _suggest_awg(amps, length, voltage, drop, unit)


@register.filter
def awg(amps: Any, arg: Any) -> str:
    """Smallest copper AWG: ``{{ 30|awg:"10" }}`` -> "6" (length[,volts[,max %[,unit]]])."""
    try:
        return _wire(amps, _args(arg)).awg
    except (InputError, TypeError, ValueError):
        return ""


@register.filter
def voltage_drop(amps: Any, arg: Any) -> Result:
    """Volts lost in a run: ``{{ 30|voltage_drop:"10,8" }}`` (length,awg[,unit])."""
    try:
        parts = _args(arg)
        if len(parts) not in (2, 3):
            raise InputError("expected length,awg[,unit]")
        unit = parts[2] if len(parts) == 3 else conf.get("DEFAULT_UNIT")
        return round(_voltage_drop(amps, parts[0], parts[1], unit), 3)
    except (InputError, TypeError, ValueError):
        return ""


@register.simple_tag
def trainhorn_wire(
    amps: Any,
    one_way_length: Any,
    system_voltage: Optional[Any] = None,
    max_drop_pct: Optional[Any] = None,
    unit: Optional[str] = None,
) -> Optional[WireSuggestion]:
    """Full wire suggestion for use with ``as``; ``None`` on invalid input."""
    try:
        return _suggest_awg(
            amps,
            one_way_length,
            conf.get("DEFAULT_SYSTEM_VOLTAGE") if system_voltage is None else system_voltage,
            conf.get("DEFAULT_MAX_DROP_PCT") if max_drop_pct is None else max_drop_pct,
            conf.get("DEFAULT_UNIT") if unit is None else unit,
        )
    except (InputError, TypeError, ValueError):
        return None
