"""Site URLs: admin, the deployment health check, and the app."""
from django.contrib import admin
from django.urls import include, path

from core.health import healthz


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", healthz, name="healthz"),
    path("", include("core.urls")),
]
