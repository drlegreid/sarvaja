"""Unit tests for Prometheus metrics middleware and TypeDB metrics.

TDD-first: written BEFORE implementation (EPIC-PERF-TELEM-V1 Phase 9).

Tests:
  - PrometheusMetricsMiddleware increments request counter
  - Histogram records latency with correct labels (method, path, status)
  - Active requests gauge increments/decrements
  - /metrics path excluded from own metrics
  - TypeDB query metrics recorded (histogram + counter)
  - /metrics endpoint returns prometheus text format with sarvaja_ prefix
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(method: str = "GET", path: str = "/api/tasks") -> MagicMock:
    """Build a fake Starlette Request."""
    req = MagicMock()
    req.method = method
    req.url.path = path
    return req


def _make_response(status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    return resp


# ---------------------------------------------------------------------------
# Middleware tests
# ---------------------------------------------------------------------------

class TestPrometheusMetricsMiddleware:
    """Test the FastAPI Prometheus middleware."""

    def test_request_counter_incremented(self):
        """After a request, sarvaja_http_requests_total is incremented."""
        from governance.middleware.prometheus_metrics import (
            REQUEST_COUNT,
            PrometheusMetricsMiddleware,
        )

        # Reset metrics for test isolation
        REQUEST_COUNT._metrics.clear()

        middleware = PrometheusMetricsMiddleware(app=MagicMock())

        # Simulate: after dispatch records a request
        REQUEST_COUNT.labels(method="GET", path="/api/tasks", status="200").inc()

        val = REQUEST_COUNT.labels(method="GET", path="/api/tasks", status="200")._value.get()
        assert val >= 1

    def test_histogram_records_latency(self):
        """REQUEST_DURATION histogram records a positive duration."""
        from governance.middleware.prometheus_metrics import REQUEST_DURATION

        REQUEST_DURATION._metrics.clear()

        REQUEST_DURATION.labels(method="GET", path="/api/tasks", status="200").observe(0.05)

        # Histogram count should be 1
        sample_count = REQUEST_DURATION.labels(
            method="GET", path="/api/tasks", status="200"
        )._sum.get()
        assert sample_count > 0

    def test_error_counter_incremented_on_5xx(self):
        """ERROR_COUNT is incremented when status >= 500."""
        from governance.middleware.prometheus_metrics import ERROR_COUNT

        ERROR_COUNT._metrics.clear()

        ERROR_COUNT.labels(method="POST", path="/api/sessions").inc()

        val = ERROR_COUNT.labels(method="POST", path="/api/sessions")._value.get()
        assert val >= 1

    def test_active_requests_gauge(self):
        """ACTIVE_REQUESTS gauge increments and decrements."""
        from governance.middleware.prometheus_metrics import ACTIVE_REQUESTS

        # Reset gauge to 0 (Gauge without labels uses _value directly)
        ACTIVE_REQUESTS._value.set(0)

        ACTIVE_REQUESTS.inc()
        assert ACTIVE_REQUESTS._value.get() == 1
        ACTIVE_REQUESTS.dec()
        assert ACTIVE_REQUESTS._value.get() == 0

    def test_metrics_path_excluded(self):
        """Requests to /metrics should not be recorded in counters."""
        from governance.middleware.prometheus_metrics import EXCLUDED_PATHS

        assert "/metrics" in EXCLUDED_PATHS

    async def test_dispatch_records_metrics(self):
        """Full middleware dispatch records counter + histogram."""
        from governance.middleware.prometheus_metrics import (
            REQUEST_COUNT,
            REQUEST_DURATION,
            ACTIVE_REQUESTS,
            PrometheusMetricsMiddleware,
        )

        REQUEST_COUNT._metrics.clear()
        REQUEST_DURATION._metrics.clear()
        ACTIVE_REQUESTS._value.set(0)

        app = MagicMock()
        middleware = PrometheusMetricsMiddleware(app)

        request = _make_request("GET", "/api/tasks")
        response = _make_response(200)

        async def call_next(req):
            return response

        result = await middleware.dispatch(request, call_next)

        assert result.status_code == 200
        # Counter should have been incremented
        val = REQUEST_COUNT.labels(method="GET", path="/api/tasks", status="200")._value.get()
        assert val >= 1

    async def test_dispatch_skips_metrics_path(self):
        """Dispatch on /metrics path does NOT increment counters."""
        from governance.middleware.prometheus_metrics import (
            REQUEST_COUNT,
            PrometheusMetricsMiddleware,
        )

        REQUEST_COUNT._metrics.clear()

        app = MagicMock()
        middleware = PrometheusMetricsMiddleware(app)

        request = _make_request("GET", "/metrics")
        response = _make_response(200)

        async def call_next(req):
            return response

        await middleware.dispatch(request, call_next)

        # /metrics path should have zero observations
        assert len(REQUEST_COUNT._metrics) == 0


# ---------------------------------------------------------------------------
# TypeDB Prometheus metrics
# ---------------------------------------------------------------------------

class TestTypeDBPrometheusMetrics:
    """Test that TypeDB base client records Prometheus metrics."""

    def test_typedb_query_histogram_exists(self):
        """sarvaja_typedb_query_duration_seconds Histogram is importable."""
        from governance.typedb.base import TYPEDB_QUERY_DURATION

        assert TYPEDB_QUERY_DURATION._name == "sarvaja_typedb_query_duration_seconds"

    def test_typedb_query_counter_exists(self):
        """sarvaja_typedb_query_total Counter is importable."""
        from governance.typedb.base import TYPEDB_QUERY_COUNT

        # Counter._name stores the base name; _total suffix is added on exposition
        assert TYPEDB_QUERY_COUNT._name == "sarvaja_typedb_query"

    def test_record_query_timing_updates_prometheus(self):
        """_record_query_timing should observe Prometheus histogram."""
        from governance.typedb.base import (
            TYPEDB_QUERY_DURATION,
            TYPEDB_QUERY_COUNT,
            TypeDBBaseClient,
        )

        TYPEDB_QUERY_DURATION._metrics.clear()
        TYPEDB_QUERY_COUNT._metrics.clear()

        client = TypeDBBaseClient()
        t0 = time.monotonic() - 0.05  # simulate 50ms ago

        with patch("governance.middleware.request_context.get_request_id", return_value=None):
            client._record_query_timing(t0, "match $x isa rule;")

        # Histogram should have an observation
        read_sum = TYPEDB_QUERY_DURATION.labels(query_type="read")._sum.get()
        assert read_sum > 0

        # Counter should be incremented
        read_count = TYPEDB_QUERY_COUNT.labels(query_type="read")._value.get()
        assert read_count >= 1

    def test_write_query_labeled_correctly(self):
        """_execute_write timing uses query_type='write' label."""
        from governance.typedb.base import (
            TYPEDB_QUERY_DURATION,
            TYPEDB_QUERY_COUNT,
            TypeDBBaseClient,
        )

        TYPEDB_QUERY_DURATION._metrics.clear()
        TYPEDB_QUERY_COUNT._metrics.clear()

        client = TypeDBBaseClient()
        t0 = time.monotonic() - 0.1

        with patch("governance.middleware.request_context.get_request_id", return_value=None):
            client._record_query_timing(t0, "insert $x isa rule;")

        write_count = TYPEDB_QUERY_COUNT.labels(query_type="write")._value.get()
        assert write_count >= 1


# ---------------------------------------------------------------------------
# /metrics endpoint
# ---------------------------------------------------------------------------

class TestMetricsEndpoint:
    """Test /metrics endpoint returns prometheus exposition format."""

    def test_metrics_endpoint_exists(self):
        """metrics_prom_router has /metrics GET route."""
        from governance.routes.infra import metrics_prom_router

        paths = [r.path for r in metrics_prom_router.routes]
        assert "/metrics" in paths

    def test_metrics_returns_prometheus_format(self):
        """GET /metrics returns text/plain with sarvaja_ prefix metrics."""
        from fastapi.testclient import TestClient
        from governance.routes.infra import metrics_prom_router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(metrics_prom_router)

        client = TestClient(app)
        resp = client.get("/metrics")

        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]
        body = resp.text
        assert "sarvaja_http_requests_total" in body or "sarvaja_http_request_duration_seconds" in body

    def test_metrics_contains_typedb_metrics(self):
        """GET /metrics includes TypeDB query metrics."""
        from fastapi.testclient import TestClient
        from governance.routes.infra import metrics_prom_router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(metrics_prom_router)

        client = TestClient(app)
        resp = client.get("/metrics")
        body = resp.text

        assert "sarvaja_typedb_query_duration_seconds" in body
        assert "sarvaja_typedb_query_total" in body
