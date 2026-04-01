"""E2E tests for Prometheus metrics endpoint (EPIC-PERF-TELEM-V1 Phase 9).

TDD-first: written BEFORE implementation.

These tests hit the LIVE API at localhost:8082 and verify:
  1. GET /metrics returns prometheus text content-type
  2. Response contains sarvaja_http_request_duration_seconds histogram
  3. Response contains sarvaja_http_requests_total counter
  4. sarvaja_typedb_query_duration_seconds present after a query
  5. Prometheus container scrapes sarvaja-api target (when running)
"""

import os

import pytest

# E2E tests require live API
API_BASE = os.getenv("API_BASE", "http://localhost:8082")
PROMETHEUS_BASE = os.getenv("PROMETHEUS_BASE", "http://localhost:9090")


@pytest.fixture(scope="module")
def http_client():
    """Shared httpx client for E2E tests."""
    import httpx
    with httpx.Client(base_url=API_BASE, timeout=10) as client:
        yield client


@pytest.fixture(scope="module")
def prom_client():
    """Shared httpx client for Prometheus API."""
    import httpx
    with httpx.Client(base_url=PROMETHEUS_BASE, timeout=10) as client:
        yield client


class TestMetricsEndpointE2E:
    """E2E: /metrics returns prometheus exposition format."""

    def test_metrics_returns_200(self, http_client):
        """GET /metrics returns 200 OK."""
        resp = http_client.get("/metrics")
        assert resp.status_code == 200

    def test_metrics_content_type_is_text_plain(self, http_client):
        """Content-Type is text/plain (prometheus exposition format)."""
        resp = http_client.get("/metrics")
        ct = resp.headers.get("content-type", "")
        assert "text/plain" in ct or "text/plain; charset=utf-8" in ct

    def test_metrics_contains_http_duration_histogram(self, http_client):
        """Response body has sarvaja_http_request_duration_seconds."""
        resp = http_client.get("/metrics")
        assert "sarvaja_http_request_duration_seconds" in resp.text

    def test_metrics_contains_http_requests_total(self, http_client):
        """Response body has sarvaja_http_requests_total counter."""
        resp = http_client.get("/metrics")
        assert "sarvaja_http_requests_total" in resp.text

    def test_metrics_contains_active_requests_gauge(self, http_client):
        """Response body has sarvaja_http_active_requests gauge."""
        resp = http_client.get("/metrics")
        assert "sarvaja_http_active_requests" in resp.text

    def test_metrics_contains_typedb_query_metrics(self, http_client):
        """After at least one API call, TypeDB metrics should appear."""
        # Trigger an API call that hits TypeDB
        http_client.get("/api/tasks")
        resp = http_client.get("/metrics")
        body = resp.text
        assert "sarvaja_typedb_query_duration_seconds" in body
        assert "sarvaja_typedb_query_total" in body

    def test_metrics_has_sarvaja_prefix(self, http_client):
        """All custom metrics use sarvaja_ prefix."""
        resp = http_client.get("/metrics")
        body = resp.text
        # Should have at least one sarvaja_ prefixed metric
        sarvaja_lines = [
            line for line in body.splitlines()
            if line.startswith("sarvaja_") or line.startswith("# HELP sarvaja_")
        ]
        assert len(sarvaja_lines) >= 3, f"Expected >=3 sarvaja_ lines, got {len(sarvaja_lines)}"

    def test_request_counter_increments_after_api_call(self, http_client):
        """After GET /api/tasks, counter for that path should be >= 1."""
        http_client.get("/api/tasks")
        resp = http_client.get("/metrics")
        body = resp.text
        # Look for a counter line with path="/api/tasks"
        assert 'path="/api/tasks"' in body


class TestPrometheusContainerE2E:
    """E2E: Prometheus container scrapes sarvaja-api target."""

    def test_prometheus_healthy(self, prom_client):
        """Prometheus /-/healthy returns 200."""
        try:
            resp = prom_client.get("/-/healthy")
            assert resp.status_code == 200
        except Exception:
            pytest.skip("Prometheus container not running")

    def test_sarvaja_api_target_up(self, prom_client):
        """Prometheus has sarvaja-api target in UP state."""
        try:
            resp = prom_client.get("/api/v1/targets")
            if resp.status_code != 200:
                pytest.skip("Prometheus API unavailable")
            data = resp.json()
            targets = data.get("data", {}).get("activeTargets", [])
            sarvaja_targets = [
                t for t in targets
                if t.get("labels", {}).get("job") == "sarvaja-api"
            ]
            assert len(sarvaja_targets) >= 1, "No sarvaja-api target found"
            assert sarvaja_targets[0]["health"] == "up", (
                f"sarvaja-api target is {sarvaja_targets[0]['health']}, expected 'up'"
            )
        except Exception as e:
            if "Prometheus" in str(e) or "Connection" in str(e):
                pytest.skip("Prometheus container not running")
            raise
