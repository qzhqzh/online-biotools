from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.annotations.api.auth import APIKeyAuthentication
from apps.annotations.api.permissions import AnnotationRateThrottle, HasAPIKeyOrOpen
from apps.annotations.api.serializers import (
    AnnotationRequestSerializer,
    AnnotationResponseSerializer,
)
from apps.annotations.engines.base import AnnotationError
from apps.annotations.services import annotate as annotate_service


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
