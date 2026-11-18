"""URLconf used by the tests: mounts the app the way the README shows."""

from django.urls import include, path

urlpatterns = [path("calc/", include("trainhorn.urls"))]
