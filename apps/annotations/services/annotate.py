"""Annotation orchestration."""

from __future__ import annotations

from typing import Any

from django.conf import settings

from apps.annotations.engines import annovar as annovar_engine
from apps.annotations.engines import vep as vep_engine
from apps.annotations.engines.base import AnnotationError


def list_engines() -> list[dict[str, Any]]:
    return [vep_engine.engine_info(), annovar_engine.engine_info()]


def _run_one(engine: str, variants: list[str], assembly: str) -> list[dict[str, Any]]:
    if engine == "vep":
        return [r.as_dict() for r in vep_engine.run_vep(variants, assembly)]
    if engine == "annovar":
        return [r.as_dict() for r in annovar_engine.run_annovar(variants, assembly)]
    raise AnnotationError(
        f"Unknown engine: {engine}",
        status_code=400,
        code="unknown_engine",
    )


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
    if engine == "both":
        results: list[dict[str, Any]] = []
        results.extend(_run_one("vep", variants, assembly))
        results.extend(_run_one("annovar", variants, assembly))
        return {
            "assembly": assembly,
            "engine": "both",
            "results": results,
        }

    if engine not in ("vep", "annovar"):
        raise AnnotationError(
            f"Unknown engine: {engine}",
            status_code=400,
            code="unknown_engine",
        )

    return {
        "assembly": assembly,
        "engine": engine,
        "results": _run_one(engine, variants, assembly),
    }


def readiness() -> dict[str, Any]:
    engines = list_engines()
    return {
        "ready": any(e.get("ready") for e in engines),
        "engines": engines,
    }
