"""Request ID + structured access logging (no variant payloads)."""

from __future__ import annotations

import logging
import time
import uuid

logger = logging.getLogger("biotools.access")


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.request_id = request_id
        started = time.perf_counter()
        response = self.get_response(request)
        duration_ms = int((time.perf_counter() - started) * 1000)
        response["X-Request-ID"] = request_id

        # Avoid logging bodies / variants
        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%s peer=%s",
            request_id,
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            request.META.get("REMOTE_ADDR", "-"),
        )
        return response
