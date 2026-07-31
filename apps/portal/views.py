from django.shortcuts import render
from django.http import JsonResponse


def home(request):
    """Placeholder portal; React+shadcn UI arrives in a later phase."""
    if "application/json" in request.headers.get("Accept", ""):
        return JsonResponse(
            {
                "service": "online-biotools",
                "docs": "/api/v1/engines/",
                "annotate_ui": "/tools/annotate/",
            }
        )
    return render(request, "portal/home.html")


def annotate_tool(request):
    return render(request, "portal/annotate.html")
