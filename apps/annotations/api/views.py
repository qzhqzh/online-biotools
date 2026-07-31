from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.annotations.api.auth import APIKeyAuthentication
from apps.annotations.api.permissions import AnnotationRateThrottle, HasAPIKeyOrOpen
from apps.annotations.api.serializers import (
    AnnotationRequestSerializer,
    AnnotationResponseSerializer,
    JobCreateSerializer,
)
from apps.annotations.engines.base import AnnotationError
from apps.annotations.knowledge import store as knowledge_store
from apps.annotations.models import AnnotationJob
from apps.annotations.services import annotate as annotate_service
from apps.annotations.services import jobs as jobs_service


class EnginesView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"engines": annotate_service.list_engines()})


class AnnotationsView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKeyOrOpen]
    throttle_classes = [AnnotationRateThrottle]

    def post(self, request):
        ser = AnnotationRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        try:
            result = annotate_service.annotate(
                variants=data["variants"],
                assembly=data["assembly"],
                engine=data.get("engine", "vep"),
            )
        except AnnotationError as exc:
            return Response(
                {"error": {"code": exc.code, "message": str(exc)}},
                status=exc.status_code,
            )
        out = AnnotationResponseSerializer(result)
        return Response(out.data, status=status.HTTP_200_OK)


class JobsView(APIView):
    """Create / list background annotation jobs."""

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKeyOrOpen]
    throttle_classes = [AnnotationRateThrottle]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", "50"))
        except ValueError:
            limit = 50
        jobs = jobs_service.list_jobs(limit=limit)
        return Response(
            {
                "jobs": [
                    jobs_service.job_to_dict(j, include_result=False) for j in jobs
                ]
            }
        )

    def post(self, request):
        ser = JobCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        max_n = settings.ANNOTATION_MAX_VARIANTS
        if len(data["variants"]) > max_n:
            return Response(
                {
                    "error": {
                        "code": "too_many_variants",
                        "message": f"Too many variants (max {max_n})",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            jobs_service.check_submit_cooldown(request)
        except jobs_service.JobSubmitTooSoon as exc:
            return Response(
                {
                    "error": {
                        "code": "submit_too_soon",
                        "message": str(exc),
                        "retry_after": exc.retry_after,
                    }
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(exc.retry_after)},
            )

        job = jobs_service.create_and_enqueue(
            variants=data["variants"],
            assembly=data["assembly"],
            engines=data["engines"],
        )
        return Response(
            jobs_service.job_to_dict(job, include_result=True),
            status=status.HTTP_202_ACCEPTED,
        )


class JobDetailView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKeyOrOpen]

    def get(self, request, job_id):
        try:
            job = AnnotationJob.objects.get(pk=job_id)
        except (AnnotationJob.DoesNotExist, ValueError):
            return Response(
                {"error": {"code": "not_found", "message": "任务不存在"}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(jobs_service.job_to_dict(job, include_result=True))


class KnowledgeMetaView(APIView):
    """Imported gene / MANE knowledge metadata (public)."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(knowledge_store.get_meta())


class KnowledgeGenesView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        q = request.query_params.get("q", "")
        gene_type = request.query_params.get("type") or None
        try:
            limit = min(max(int(request.query_params.get("limit", "50")), 1), 200)
        except ValueError:
            limit = 50
        try:
            offset = max(int(request.query_params.get("offset", "0")), 0)
        except ValueError:
            offset = 0
        return Response(
            knowledge_store.search_genes(
                q, gene_type=gene_type, limit=limit, offset=offset
            )
        )


class KnowledgeTranscriptsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        q = request.query_params.get("q", "")
        mane_only = request.query_params.get("mane_only", "").lower() in {
            "1",
            "true",
            "yes",
        }
        try:
            limit = min(max(int(request.query_params.get("limit", "50")), 1), 200)
        except ValueError:
            limit = 50
        try:
            offset = max(int(request.query_params.get("offset", "0")), 0)
        except ValueError:
            offset = 0
        return Response(
            knowledge_store.search_transcripts(
                q, mane_only=mane_only, limit=limit, offset=offset
            )
        )


class LegacyAnnotateView(APIView):
    """Deprecated FastAPI-compatible alias; same auth as AnnotationsView."""

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKeyOrOpen]
    throttle_classes = [AnnotationRateThrottle]

    def post(self, request):
        payload = {
            "variants": request.data.get("variants", []),
            "assembly": request.data.get("assembly", "GRCh37"),
            "engine": "vep",
        }
        ser = AnnotationRequestSerializer(data=payload)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        try:
            result = annotate_service.annotate(
                variants=data["variants"],
                assembly=data["assembly"],
                engine="vep",
            )
        except AnnotationError as exc:
            return Response(
                {
                    "success": False,
                    "assembly": data["assembly"],
                    "results": [],
                    "errors": [str(exc)],
                },
                status=exc.status_code,
            )
        return Response(
            {
                "success": True,
                "assembly": result["assembly"],
                "results": result["results"],
                "errors": [],
            }
        )
