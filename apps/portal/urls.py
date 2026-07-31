from django.urls import path

from apps.portal import views

urlpatterns = [
    path("", views.home, name="home"),
    path("tools/annotate/", views.annotate_tool, name="annotate-tool"),
    path("tools/engines/", views.engines_page, name="engines-page"),
    path("docs/", views.docs_page, name="docs-page"),
]
