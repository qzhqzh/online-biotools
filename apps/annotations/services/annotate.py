"""Annotation orchestration."""

from __future__ import annotations

from typing import Any

from django.conf import settings

from apps.annotations.engines import vep as vep_engine
from apps.annotations.engines.base import AnnotationError


def list_engines() -> list[dict[str, Any]]:
    return [vep_engine.engine_info()]


def annotate(
    *,
    variants: list[str],
    assembly: str,
    engine: str = "vep",
) -> dict[str, Any]:
    if not variants:
        raise AnnotationError("No variants provided", status_code=400, code="empty_input")

    max_n = settings.ANNOTATION_MAX_VARIANTS
    if len(variants) > max_n:
        raise AnnotationError(
            f"Too many variants (max {max_n})",
            status_code=400,
            code="too_many_variants",
        )

    engine = (engine or "vep").lower()
    if engine in ("annovar", "both"):
        raise AnnotationError(
            "ANNOVAR engine is not available yet",
            status_code=501,
            code="engine_not_implemented",
        )
    if engine != "vep":
        raise AnnotationError(
            f"Unknown engine: {engine}",
            status_code=400,
            code="unknown_engine",
        )

    results = vep_engine.run_vep(variants, assembly)
    return {
        "assembly": assembly,
        "engine": "vep",
        "results": [r.as_dict() for r in results],
    }


def readiness() -> dict[str, Any]:
    engines = list_engines()
    return {
        "ready": any(e.get("ready") for e in engines),
        "engines": engines,
    }
