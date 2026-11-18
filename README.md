# django-trainhorn

Reusable Django app with three train horn calculators, built on the tested
[trainhorn-calc](https://github.com/train-horn/trainhorn-calc) 1.0.0 core:

- **Sound level at a distance**: SPL from a rated level with the inverse-square law
  (150 dB at 10 ft is about 130 dB at 100 ft), optional air absorption, and the
  distance at which the level falls to a target.
- **Air tank runtime**: seconds of horn time between two gauge pressures (Boyle's law),
  blast count and compressor refill time.
- **Wire gauge**: smallest copper AWG that keeps a 12 V / 24 V run within a voltage-drop budget.

You get template filters, Django forms with validation, class-based views with URL
patterns, overridable accessible templates and a system check for the settings.
The only dependency is Django (4.2+); the core is vendored in `trainhorn/calc/`.

Documentation: https://docs.page/train-horn/django-trainhorn

> Results are engineering estimates from simple physical models, not measurements
> and not legal advice about horn use.

## Install

```bash
pip install "git+https://github.com/train-horn/django-trainhorn.git@v1.0.0"
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "trainhorn",
]

# urls.py
from django.urls import include, path

urlpatterns = [
    # ...
    path("calc/", include("trainhorn.urls")),
]
```

This adds `/calc/` (index), `/calc/spl/`, `/calc/tank/` and `/calc/wire/`
(URL names `trainhorn:index`, `trainhorn:spl`, `trainhorn:tank`, `trainhorn:wire`).
Forms submit with GET, so every result has a shareable URL.

## Template filters

```django
{% load trainhorn %}
{{ 150|spl_at_distance:"10,100" }}      {# 130.0  dB at 100 ft for a horn rated 150 dB at 10 ft #}
{{ 150|spl_at_distance:"1,30,m" }}      {# rated at 1 m, listener at 30 m #}
{{ 150|distance_for_spl:"10,90" }}      {# 10000.0  ft until the level falls to 90 dB #}
{{ 5|tank_runtime:"150,110,10" }}       {# 10.9  s: 5 gal tank, 150 -> 110 psi, 10 CFM horn #}
{{ 30|awg:"10" }}                       {# 6  AWG for 30 A, 10 ft one way, 12 V, 3 % #}
{{ 30|awg:"10,24,3,ft" }}               {# same at 24 V #}
{{ 30|voltage_drop:"10,8" }}            {# volts lost over 10 ft of 8 AWG #}

{% trainhorn_wire 30 10 as wire %}
{{ wire.awg }} AWG, {{ wire.voltage_drop_pct|floatformat:2 }} % drop
```

Filters never raise: invalid input renders as an empty string.

## Forms

```python
from trainhorn.forms import SPLForm, TankRuntimeForm, WireGaugeForm

form = TankRuntimeForm({"tank_gallons": 5, "start_psi": 150, "cutoff_psi": 110, "horn_cfm": 10})
form.is_valid()             # True
form.result["runtime_seconds"]   # 10.91566866267465
```

Field errors (empty, not a number, zero or negative) appear on the field; errors
from the physics (for example a cut-off pressure above the start pressure) appear
in `form.non_field_errors()`.

## Templates

All pages extend `trainhorn/base.html`. Override it in your project
(`templates/trainhorn/base.html`) to use your site layout; keep a `content` block.
The calculator pages are `trainhorn/spl.html`, `trainhorn/tank.html`,
`trainhorn/wire.html` and share `trainhorn/_form.html`, which renders labels,
help text, `aria-describedby`, `aria-invalid` and a `role="alert"` error summary.

## Settings

All optional:

```python
TRAINHORN = {
    "DEFAULT_UNIT": "ft",          # "ft" or "m"
    "DEFAULT_REF_DISTANCE": 10,    # distance the rated dB applies to
    "DEFAULT_SYSTEM_VOLTAGE": 12,
    "DEFAULT_MAX_DROP_PCT": 3,
    "DECIMALS": 1,                 # rounding in filters and result pages
}
```

`manage.py check` validates them (`trainhorn.E001`-`E005`, `trainhorn.W001` for unknown keys).

## Tests

```bash
python -m venv .venv && .venv/bin/pip install django
.venv/bin/python runtests.py
```

53 tests with Django's test runner cover the filters, the forms (valid and invalid),
the views (200, inline errors, results), the system check and parity with the
trainhorn-calc reference vectors.

## Related

Browser versions of these calculators are on
[train-horn.com](https://train-horn.com/tools/), an independent reference on train horns.

## License

MIT. See [LICENSE](LICENSE).
