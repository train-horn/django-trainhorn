"""URL patterns. Include with ``path("calc/", include("trainhorn.urls"))``."""

from django.urls import path

from . import views

app_name = "trainhorn"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("spl/", views.SPLView.as_view(), name="spl"),
    path("tank/", views.TankRuntimeView.as_view(), name="tank"),
    path("wire/", views.WireGaugeView.as_view(), name="wire"),
]
