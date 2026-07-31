"""API Key authentication for write endpoints."""

from __future__ import annotations

from django.conf import settings
from rest_framework import authentication, exceptions


def configured_api_keys() -> set[str]:
    raw = getattr(settings, "BIOTOOLS_API_KEYS", "") or ""
    return {k.strip() for k in raw.split(",") if k.strip()}


def api_key_required() -> bool:
    """Require API key when keys are configured, or when explicitly forced."""
    if getattr(settings, "BIOTOOLS_REQUIRE_API_KEY", False):
        return True
    return bool(configured_api_keys())


class APIKeyAuthentication(authentication.BaseAuthentication):
    """Authenticate via X-API-Key or Authorization: Bearer <key>."""

    def authenticate(self, request):
        keys = configured_api_keys()
        if not api_key_required():
            return None

        if not keys:
            raise exceptions.AuthenticationFailed(
                "API key required but BIOTOOLS_API_KEYS is empty"
            )

        provided = request.headers.get("X-API-Key") or ""
        if not provided:
            auth = request.headers.get("Authorization", "")
            if auth.lower().startswith("bearer "):
                provided = auth[7:].strip()

        if not provided or provided not in keys:
            raise exceptions.AuthenticationFailed("Invalid or missing API key")

        return (None, provided)
