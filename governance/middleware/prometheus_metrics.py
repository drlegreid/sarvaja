"""Prometheus metrics middleware for the Governance API.

Exposes HTTP request metrics via prometheus_client:
  - sarvaja_http_request_duration_seconds: Histogram (method, path, status)
  - sarvaja_http_requests_total: Counter (method, path, status)
  - sarvaja_http_errors_total: Counter (method, path) — status >= 500
  - sarvaja_http_active_requests: Gauge — in-flight requests

The /metrics path is excluded from its own instrumentation to avoid
self-referential noise.

Created: 2026-03-26  EPIC-PERF-TELEM-V1 Phase 9
"""

try:
    from prometheus_client import Counter, Gauge, Histogram
except ImportError as _exc:
    raise ImportError(
        "prometheus_client is required for the metrics middleware. "
        "Install via: pip install prometheus-client"
    ) from _exc
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time

# Paths excluded from metrics recording
EXCLUDED_PATHS = frozenset({"/metrics", "/api/health", "/api/docs", "/openapi.json"})

# ---------------------------------------------------------------------------
# Prometheus instruments (module-level singletons)
# ---------------------------------------------------------------------------

REQUEST_DURATION = Histogram(
    "sarvaja_http_request_duration_seconds",
    "HTTP request duration in seconds",
    labelnames=["method", "path", "status"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

REQUEST_COUNT = Counter(
    "sarvaja_http_requests_total",
    "Total HTTP requests",
    labelnames=["method", "path", "status"],
)

ERROR_COUNT = Counter(
    "sarvaja_http_errors_total",
    "Total HTTP server errors (5xx)",
    labelnames=["method", "path"],
)

ACTIVE_REQUESTS = Gauge(
    "sarvaja_http_active_requests",
    "Number of in-flight HTTP requests",
)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Record Prometheus metrics for every HTTP request."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip excluded paths
        if path in EXCLUDED_PATHS:
            return await call_next(request)

        method = request.method
        ACTIVE_REQUESTS.inc()
        start = time.monotonic()

        try:
            response = await call_next(request)
        except Exception:
            ACTIVE_REQUESTS.dec()
            raise

        duration = time.monotonic() - start
        status = str(response.status_code)
        ACTIVE_REQUESTS.dec()

        REQUEST_DURATION.labels(method=method, path=path, status=status).observe(duration)
        REQUEST_COUNT.labels(method=method, path=path, status=status).inc()

        if response.status_code >= 500:
            ERROR_COUNT.labels(method=method, path=path).inc()

        return response
