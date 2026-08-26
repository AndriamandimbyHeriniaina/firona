"""Root URL configuration for the Firona HTTP API."""

from django.contrib import admin
from django.urls import include, path

from config.health import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/v1/", include("apps.catalog.urls")),
    path("api/v1/", include("apps.trends.urls")),
]
