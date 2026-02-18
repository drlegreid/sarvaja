"""Structured access logging middleware for the Governance API.

Logs every HTTP request/response as a single JSON line:
  {"ts": "...", "method": "GET", "path": "/api/sessions", "status": 200, "ms": 12, "bytes": 1423}

Opt-in debug mode (LOG_LEVEL=DEBUG) adds query params and request body size.

Created: 2026-02-11
"""
import json
import logging
import os
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("governance.access")

# Paths we skip to avoid log noise
_SKIP_PATHS = frozenset({"/api/health", "/api/docs", "/api/redoc", "/openapi.json"})

# Debug mode logs query params and request size
_DEBUG = os.getenv("LOG_LEVEL", "").upper() == "DEBUG"


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Structured JSON access log for every API request."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip noisy health/docs endpoints
        if path in _SKIP_PATHS:
            return await call_next(request)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 1)

        # Content-Length may not always be set (streaming responses)
        resp_bytes = response.headers.get("content-length", "-")

        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "method": request.method,
            "path": path,
            "status": response.status_code,
            "ms": duration_ms,
            "bytes": resp_bytes,
        }

        if _DEBUG:
            qs = str(request.url.query) if request.url.query else None
            if qs:
                entry["query"] = qs
            cl = request.headers.get("content-length")
            if cl:
                entry["req_bytes"] = cl

        # Use INFO for success, WARNING for 4xx/5xx
        line = json.dumps(entry, separators=(",", ":"))
        if response.status_code >= 500:
            logger.warning(line)
        elif response.status_code >= 400:
            # BUG-225-MW-001: 4xx should be WARNING (auth failures, bad requests)
            logger.warning(line)
        else:
            logger.info(line)

        return response
