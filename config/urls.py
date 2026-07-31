from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", include("apps.annotations.api.health_urls")),
    path("api/v1/", include("apps.annotations.api.urls")),
    path("", include("apps.portal.urls")),
]
