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
                "jobs_ui": "/tools/jobs/",
                "engines_ui": "/tools/engines/",
                "gene_knowledge_ui": "/knowledge/genes/",
                "amino_acid_knowledge_ui": "/knowledge/amino-acids/",
            }
        )
    return render(request, "portal/home.html")


def annotate_tool(request):
    return render(request, "portal/annotate.html")


def jobs_page(request):
    return render(request, "portal/jobs.html")


def engines_page(request):
    return render(request, "portal/engines.html")


def docs_page(request):
    return render(request, "portal/docs.html")


def gene_knowledge_page(request):
    return render(request, "portal/gene_knowledge.html")


def amino_acid_knowledge_page(request):
    return render(request, "portal/amino_acid_knowledge.html")
