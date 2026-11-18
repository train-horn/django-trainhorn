"""Django forms for the three calculators.

Each form validates its fields, runs the vendored ``trainhorn-calc`` core in
``clean()`` and stores the answer in ``form.result`` (``None`` until the form
is valid). Errors raised by the core (``InputError``) become non-field form
errors, so templates only need ``form.non_field_errors``.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from django import forms
from django.core.exceptions import ValidationError

from . import conf
from .calc import InputError, blast_count, compressor_recovery_seconds, distance_for_spl, free_air_volume_cuft
from .calc import spl_at_distance, suggest_awg, tank_runtime_seconds

UNIT_CHOICES = (("ft", "feet"), ("m", "metres"))


def validate_positive(value: Optional[float]) -> None:
    """Reject zero and negative numbers (Django's ``min_value`` is inclusive)."""
    if value is not None and value <= 0:
        raise ValidationError("Enter a number greater than 0.", code="not_positive")


def _number(label: str, help_text: str = "", required: bool = True, positive: bool = True, **kwargs: Any) -> forms.FloatField:
    validators = [validate_positive] if positive else []
    return forms.FloatField(label=label, help_text=help_text, required=required, validators=validators, **kwargs)


class CalculatorForm(forms.Form):
    """Base class: subclasses implement :meth:`calculate`."""

    result: Optional[Dict[str, Any]] = None

    def _describedby(self, name: str, with_errors: bool) -> str:
        auto_id = self[name].auto_id
        ids = []
        if self.fields[name].help_text:
            ids.append(f"{auto_id}_help")
        if with_errors:
            ids.append(f"{auto_id}_errors")
        return " ".join(ids)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs["inputmode"] = "decimal" if isinstance(field, forms.FloatField) else None
            if field.widget.attrs["inputmode"] is None:
                del field.widget.attrs["inputmode"]
            described = self._describedby(name, with_errors=False)
            if described:
                field.widget.attrs["aria-describedby"] = described

    def full_clean(self) -> None:
        super().full_clean()
        # Link inline errors to their inputs for screen readers.
        for name in self.errors:
            if name in self.fields:
                self.fields[name].widget.attrs["aria-invalid"] = "true"
                self.fields[name].widget.attrs["aria-describedby"] = self._describedby(name, with_errors=True)

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - abstract
        raise NotImplementedError

    def clean(self) -> Dict[str, Any]:
        cleaned = super().clean()
        if self.errors:
            return cleaned
        try:
            self.result = self.calculate(cleaned)
        except InputError as exc:
            self.result = None
            raise ValidationError(str(exc), code="calculation") from exc
        return cleaned


class SPLForm(CalculatorForm):
    """Sound level at a distance from a horn's rated dB (inverse-square law)."""

    source_db = _number(
        "Rated level (dB)", "The horn's rating, e.g. 150 for \"150 dB at 10 ft\".", positive=False,
        min_value=0, max_value=250,
    )
    ref_distance = _number("Rated at distance", "The distance the rating applies to.")
    distance = _number("Listener distance", "Where you want to know the level.")
    unit = forms.ChoiceField(label="Unit", choices=UNIT_CHOICES)
    absorption_db_per_km = _number(
        "Air absorption (dB/km)", "Optional; about 1-2 dB/km for a typical horn chord. Leave empty for none.",
        required=False, positive=False, min_value=0,
    )
    target_db = _number(
        "Target level (dB)", "Optional; also find the distance at which the level drops to this.",
        required=False, positive=False, min_value=0, max_value=250,
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["unit"].initial = conf.get("DEFAULT_UNIT")
        self.fields["ref_distance"].initial = conf.get("DEFAULT_REF_DISTANCE")

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        absorption = data.get("absorption_db_per_km") or 0.0
        level = spl_at_distance(data["source_db"], data["distance"], data["ref_distance"], data["unit"], absorption)
        result: Dict[str, Any] = {"level_db": level, "unit": data["unit"], "target_distance": None}
        if data.get("target_db") is not None:
            result["target_distance"] = distance_for_spl(
                data["source_db"], data["target_db"], data["ref_distance"], data["unit"], absorption
            )
        return result


class TankRuntimeForm(CalculatorForm):
    """Horn time from an air tank (Boyle's law) and optional compressor refill time."""

    tank_gallons = _number("Tank size (US gallons)")
    start_psi = _number("Start pressure (psi gauge)", "Tank pressure when you start, e.g. 150.")
    cutoff_psi = _number(
        "Cut-off pressure (psi gauge)", "Lowest pressure at which the horn still sounds right, e.g. 110.",
        positive=False, min_value=0,
    )
    horn_cfm = _number("Horn air use (CFM)", "Free-air consumption from the horn's spec sheet.")
    blast_seconds = _number("Blast length (s)", "Optional; count how many blasts of this length fit.", required=False)
    compressor_cfm = _number(
        "Compressor output (CFM)", "Optional; free-air delivery near your cut-out pressure, to estimate refill time.",
        required=False,
    )

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        runtime = tank_runtime_seconds(data["tank_gallons"], data["start_psi"], data["cutoff_psi"], data["horn_cfm"])
        result: Dict[str, Any] = {
            "runtime_seconds": runtime,
            "free_air_cuft": free_air_volume_cuft(data["tank_gallons"], data["start_psi"], data["cutoff_psi"]),
            "blasts": None,
            "recovery_seconds": None,
        }
        if data.get("blast_seconds"):
            result["blasts"] = blast_count(runtime, data["blast_seconds"])
        if data.get("compressor_cfm"):
            result["recovery_seconds"] = compressor_recovery_seconds(
                data["tank_gallons"], data["cutoff_psi"], data["start_psi"], data["compressor_cfm"]
            )
        return result


class WireGaugeForm(CalculatorForm):
    """Smallest copper AWG that keeps a 12 V / 24 V run within a voltage-drop budget."""

    amps = _number("Current (A)", "Continuous draw, e.g. a compressor's rated amps.")
    one_way_length = _number("One-way run length", "Distance from the battery or fuse to the load.")
    unit = forms.ChoiceField(label="Unit", choices=UNIT_CHOICES)
    system_voltage = _number("System voltage (V)")
    max_drop_pct = _number("Allowed voltage drop (%)", max_value=50)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["unit"].initial = conf.get("DEFAULT_UNIT")
        self.fields["system_voltage"].initial = conf.get("DEFAULT_SYSTEM_VOLTAGE")
        self.fields["max_drop_pct"].initial = conf.get("DEFAULT_MAX_DROP_PCT")

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        wire = suggest_awg(
            data["amps"], data["one_way_length"], data["system_voltage"], data["max_drop_pct"], data["unit"]
        )
        return {"wire": wire, "awg": wire.awg}
