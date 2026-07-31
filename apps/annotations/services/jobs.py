"""Background annotation jobs."""

from __future__ import annotations

import logging
import threading
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.db import close_old_connections
from django.utils import timezone

from apps.annotations.engines.base import AnnotationError
from apps.annotations.models import AnnotationJob
from apps.annotations.services import annotate as annotate_service

logger = logging.getLogger("biotools.jobs")

_SUBMIT_CACHE_PREFIX = "annotate_job_submit:"


class JobSubmitTooSoon(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"请等待 {retry_after} 秒后再提交新任务")


def submit_cooldown_seconds() -> int:
    return int(getattr(settings, "BIOTOOLS_JOB_COOLDOWN_SECONDS", 10))


def _client_ident(request) -> str:
    if getattr(request, "auth", None):
        return f"key:{str(request.auth)[:24]}"
    # Prefer X-Forwarded-For first hop when behind proxy
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"
    return f"ip:{request.META.get('REMOTE_ADDR', 'unknown')}"


def check_submit_cooldown(request) -> None:
    seconds = submit_cooldown_seconds()
    if seconds <= 0:
        return
    key = _SUBMIT_CACHE_PREFIX + _client_ident(request)
    if cache.get(key):
        ttl = cache.ttl(key) if hasattr(cache, "ttl") else None
        retry = int(ttl) if ttl and ttl > 0 else seconds
        raise JobSubmitTooSoon(retry)
    cache.set(key, 1, timeout=seconds)


def create_and_enqueue(
    *,
    variants: list[str],
    assembly: str,
    engines: list[str],
) -> AnnotationJob:
    job = AnnotationJob.objects.create(
        status=AnnotationJob.Status.QUEUED,
        assembly=assembly,
        engines=engines,
        variants=variants,
        variant_count=len(variants),
    )
    thread = threading.Thread(
        target=_run_job_safe,
        args=(str(job.id),),
        name=f"annotate-job-{job.id}",
        daemon=True,
    )
    thread.start()
    return job


def _run_job_safe(job_id: str) -> None:
    close_old_connections()
    try:
        _run_job(job_id)
    except Exception:
        logger.exception("job runner crashed job_id=%s", job_id)
        try:
            AnnotationJob.objects.filter(pk=job_id).update(
                status=AnnotationJob.Status.FAILED,
                error="内部任务执行异常",
                finished_at=timezone.now(),
            )
        except Exception:
            logger.exception("failed to mark job failed job_id=%s", job_id)
    finally:
        close_old_connections()


def _run_job(job_id: str) -> None:
    try:
        job = AnnotationJob.objects.get(pk=job_id)
    except AnnotationJob.DoesNotExist:
        return

    job.status = AnnotationJob.Status.RUNNING
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at"])

    runs: list[dict[str, Any]] = []
    fatal: str | None = None

    for engine in job.engines:
        try:
            payload = annotate_service.annotate(
                variants=list(job.variants),
                assembly=job.assembly,
                engine=engine,
            )
            runs.append(
                {
                    "engine": engine,
                    "status": "ok",
                    "results": payload.get("results", []),
                }
            )
        except AnnotationError as exc:
            runs.append(
                {
                    "engine": engine,
                    "status": "error",
                    "error": str(exc),
                    "results": [],
                }
            )
        except Exception as exc:
            logger.exception("engine failed job_id=%s engine=%s", job_id, engine)
            runs.append(
                {
                    "engine": engine,
                    "status": "error",
                    "error": str(exc)[:500],
                    "results": [],
                }
            )

    ok_count = sum(1 for r in runs if r.get("status") == "ok")
    if ok_count == 0:
        job.status = AnnotationJob.Status.FAILED
        fatal = "；".join(
            f"{r.get('engine')}: {r.get('error')}" for r in runs if r.get("error")
        ) or "全部引擎失败"
        job.error = fatal[:2000]
        job.result = {"assembly": job.assembly, "runs": runs}
    else:
        job.status = AnnotationJob.Status.SUCCEEDED
        job.error = ""
        job.result = {"assembly": job.assembly, "runs": runs}

    job.finished_at = timezone.now()
    job.save(update_fields=["status", "error", "result", "finished_at"])


def job_to_dict(job: AnnotationJob, *, include_result: bool = True) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": str(job.id),
        "status": job.status,
        "assembly": job.assembly,
        "engines": job.engines,
        "variant_count": job.variant_count,
        "variants": job.variants if include_result else None,
        "error": job.error or None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }
    if include_result:
        data["result"] = job.result
    else:
        data["result"] = None
        # Compact preview for list views
        data["variants_preview"] = (job.variants or [])[:3]
    return data


def list_jobs(*, limit: int = 50) -> list[AnnotationJob]:
    limit = max(1, min(limit, 200))
    return list(AnnotationJob.objects.all()[:limit])
