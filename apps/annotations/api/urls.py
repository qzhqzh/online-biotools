from django.urls import path

from apps.annotations.api.views import AnnotationsView, EnginesView, LegacyAnnotateView

urlpatterns = [
    path("engines/", EnginesView.as_view(), name="engines"),
    path("annotations/", AnnotationsView.as_view(), name="annotations"),
    # Temporary FastAPI compatibility
    path("legacy/annotate", LegacyAnnotateView.as_view(), name="legacy-annotate"),
]
