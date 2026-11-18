"""Class-based views for the calculators.

The forms submit with GET, so every result has a shareable URL and the
browser back button works. A request without any form field shows an empty
form; otherwise the form is bound and validated. Pages always return 200;
validation errors are shown inline.

Subclass :class:`CalculatorView` to add your own calculator, or point
``template_name`` at your own template.
"""

from __future__ import annotations

from typing import Any, Dict, List, Type

from django.http import HttpRequest, HttpResponse
from django.views.generic import TemplateView

from . import conf
from .forms import CalculatorForm, SPLForm, TankRuntimeForm, WireGaugeForm

CALCULATORS: List[Dict[str, str]] = [
    {"url_name": "trainhorn:spl", "title": "Sound level at a distance",
     "summary": "How loud a horn rated at 10 ft is at 100 ft, 1/4 mile or anywhere else."},
    {"url_name": "trainhorn:tank", "title": "Air tank runtime",
     "summary": "Seconds of horn time from your tank, blast count and compressor refill time."},
    {"url_name": "trainhorn:wire", "title": "Wire gauge (AWG)",
     "summary": "Smallest copper wire for a compressor or solenoid run at 12 V or 24 V."},
]


class CalculatorView(TemplateView):
    """Render ``form_class`` bound to the query string and its result."""

    form_class: Type[CalculatorForm] = CalculatorForm
    title: str = ""
    intro: str = ""

    def get_form(self) -> CalculatorForm:
        names = set(self.form_class.base_fields)
        submitted = any(name in self.request.GET for name in names)
        return self.form_class(self.request.GET if submitted else None)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        form = self.get_form()
        is_valid = form.is_bound and form.is_valid()
        context = self.get_context_data(form=form, result=form.result if is_valid else None, **kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.setdefault("title", self.title)
        context.setdefault("intro", self.intro)
        context["decimals"] = conf.get("DECIMALS")
        return context


class IndexView(TemplateView):
    """List the calculators."""

    template_name = "trainhorn/index.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["calculators"] = CALCULATORS
        context["title"] = "Train horn calculators"
        return context


class SPLView(CalculatorView):
    form_class = SPLForm
    template_name = "trainhorn/spl.html"
    title = "Sound level at a distance"
    intro = ("Free-field estimate with the inverse-square law: the level falls about 6 dB "
             "each time the distance doubles.")


class TankRuntimeView(CalculatorView):
    form_class = TankRuntimeForm
    template_name = "trainhorn/tank.html"
    title = "Air tank runtime"
    intro = "Boyle's law estimate of horn time between two gauge pressures, with the compressor off."


class WireGaugeView(CalculatorView):
    form_class = WireGaugeForm
    template_name = "trainhorn/wire.html"
    title = "Wire gauge (AWG)"
    intro = ("Smallest copper gauge whose round-trip voltage drop stays within your budget. "
             "It does not check ampacity; fuse for the wire you choose.")
