from django.http import JsonResponse
from django.urls import path

from apps.annotations.services import annotate as annotate_service


def live(_request):
    return JsonResponse({"status": "ok"})


def ready(_request):
    payload = annotate_service.readiness()
    status_code = 200 if payload["ready"] else 503
    return JsonResponse(payload, status=status_code)


urlpatterns = [
    path("live", live, name="health-live"),
    path("ready", ready, name="health-ready"),
]
