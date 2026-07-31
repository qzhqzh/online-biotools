from django.urls import path

from apps.portal import views

urlpatterns = [
    path("", views.home, name="home"),
    path("tools/annotate/", views.annotate_tool, name="annotate-tool"),
    path("tools/jobs/", views.jobs_page, name="jobs-page"),
    path("tools/engines/", views.engines_page, name="engines-page"),
    path("docs/", views.docs_page, name="docs-page"),
    path("knowledge/genes/", views.gene_knowledge_page, name="gene-knowledge"),
    path(
        "knowledge/amino-acids/",
        views.amino_acid_knowledge_page,
        name="amino-acid-knowledge",
    ),
]
