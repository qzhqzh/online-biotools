"""Shared exceptions for annotation engines."""

from __future__ import annotations


class AnnotationError(Exception):
    """Base annotation error with HTTP status hint."""

    status_code = 500
    code = "annotation_error"

    def __init__(self, message: str, *, status_code: int | None = None, code: str | None = None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code


class EngineNotReady(AnnotationError):
    status_code = 503
    code = "engine_not_ready"


class EngineFailed(AnnotationError):
    status_code = 502
    code = "engine_failed"


class EngineTimeout(AnnotationError):
    status_code = 504
    code = "engine_timeout"


class UnsupportedAssembly(AnnotationError):
    status_code = 400
    code = "unsupported_assembly"
