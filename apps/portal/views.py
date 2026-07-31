from django.shortcuts import render
from django.http import JsonResponse


def home(request):
    """Portal home; JSON clients get service metadata."""
    if "application/json" in request.headers.get("Accept", ""):
        return JsonResponse(
            {
                "service": "online-biotools",
                "docs": "/docs/",
                "annotate_ui": "/tools/annotate/",
                "engines_ui": "/tools/engines/",
            }
        )
    return render(request, "portal/home.html")


def annotate_tool(request):
    bootstrap = {
        "apiBase": "/api/v1",
        "csrfCookie": "csrftoken",
    }
    return render(request, "portal/annotate.html", {"bootstrap": bootstrap})


def engines_page(request):
    return render(request, "portal/engines.html")


def docs_page(request):
    return render(request, "portal/docs.html")
