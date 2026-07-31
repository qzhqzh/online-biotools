from django.urls import path

from apps.portal import views

urlpatterns = [
    path("", views.home, name="home"),
    path("tools/annotate/", views.annotate_tool, name="annotate-tool"),
]
