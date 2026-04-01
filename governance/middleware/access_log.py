"""Structured access logging middleware for the Governance API.

Logs every HTTP request/response as a single JSON line:
  {"ts": "...", "method": "GET", "path": "/api/sessions", "status": 200, "ms": 12, "rid": "a1b2c3d4", "bytes": 1423}

Features (EPIC-PERF-TELEM-V1 Phase 6):
  - X-Request-ID (uuid4[:8]) for correlating dashboard cascades
  - Slow-request WARNING when ms > SLOW_REQUEST_MS (env, default 1000)
  - "slow":true flag in log entry when threshold exceeded
  - Opt-in debug mode (LOG_LEVEL=DEBUG) adds query params and request body size

Created: 2026-02-11
Updated: 2026-03-26 (Phase 6: slow alerting + request correlation)
"""
import json
import logging
import os
import time
import uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from governance.middleware.request_context import set_request_id

logger = logging.getLogger("governance.access")

# --- File handler for Promtail ingestion (Phase 10) ---
_LOG_DIR = Path(os.getenv("ACCESS_LOG_DIR", "logs"))
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_ACCESS_LOG_PATH = _LOG_DIR / "access.jsonl"

_file_handler = RotatingFileHandler(
    _ACCESS_LOG_PATH,
    maxBytes=50 * 1024 * 1024,  # 50 MB
    backupCount=5,
    encoding="utf-8",
)
_file_handler.setLevel(logging.DEBUG)
# Raw JSON lines — no formatter prefix needed
_file_handler.setFormatter(logging.Formatter("%(message)s"))

_file_logger = logging.getLogger("governance.access.file")
_file_logger.setLevel(logging.DEBUG)
_file_logger.addHandler(_file_handler)
_file_logger.propagate = False  # Don't duplicate to console

# Paths we skip to avoid log noise
_SKIP_PATHS = frozenset({"/api/health", "/api/docs", "/api/redoc", "/openapi.json", "/metrics"})

# Debug mode logs query params and request size
_DEBUG = os.getenv("LOG_LEVEL", "").upper() == "DEBUG"

# Slow-request threshold in milliseconds (env-configurable)
SLOW_REQUEST_MS = int(os.getenv("SLOW_REQUEST_MS", "1000"))


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Structured JSON access log for every API request."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip noisy health/docs endpoints
        if path in _SKIP_PATHS:
            return await call_next(request)

        # Generate request correlation ID
        rid = uuid.uuid4().hex[:8]
        set_request_id(rid)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 1)

        # Add X-Request-ID to response headers for client correlation
        response.headers["X-Request-ID"] = rid

        # Content-Length may not always be set (streaming responses)
        resp_bytes = response.headers.get("content-length", "-")

        is_slow = duration_ms > SLOW_REQUEST_MS

        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "method": request.method,
            "path": path,
            "status": response.status_code,
            "ms": duration_ms,
            "rid": rid,
            "bytes": resp_bytes,
        }

        if is_slow:
            entry["slow"] = True

        if _DEBUG:
            qs = str(request.url.query) if request.url.query else None
            if qs:
                entry["query"] = qs
            cl = request.headers.get("content-length")
            if cl:
                entry["req_bytes"] = cl

        # Slow requests always WARNING (regardless of status code)
        line = json.dumps(entry, separators=(",", ":"))
        if is_slow or response.status_code >= 400:
            logger.warning(line)
        else:
            logger.info(line)

        # Write to file for Promtail ingestion (Phase 10)
        _file_logger.info(line)

        # Clear thread-local after request completes
        set_request_id(None)

        return response
