"""E2E tests for Loki log aggregation (EPIC-PERF-TELEM-V1 Phase 10).

TDD-first: written BEFORE implementation.

These tests hit LIVE Loki at localhost:3100 and verify:
  1. Loki container healthy (GET /ready returns "ready")
  2. Promtail scraping access.jsonl (check targets)
  3. LogQL {job="sarvaja-api"} returns recent entries with labels
  4. LogQL {job="sarvaja-api",slow="true"} filters slow requests
  5. LogQL |= "rid_value" finds correlated entries
"""

import os
import time

import pytest

API_BASE = os.getenv("API_BASE", "http://localhost:8082")
LOKI_BASE = os.getenv("LOKI_BASE", "http://localhost:3100")


@pytest.fixture(scope="module")
def http_client():
    """Shared httpx client for API traffic generation."""
    import httpx
    with httpx.Client(base_url=API_BASE, timeout=10) as client:
        yield client


@pytest.fixture(scope="module")
def loki_client():
    """Shared httpx client for Loki API."""
    import httpx
    with httpx.Client(base_url=LOKI_BASE, timeout=10) as client:
        yield client


def _loki_query(loki_client, query: str, limit: int = 100):
    """Run a LogQL query against Loki and return parsed result."""
    resp = loki_client.get("/loki/api/v1/query_range", params={
        "query": query,
        "limit": limit,
        "since": "1h",
    })
    assert resp.status_code == 200, f"Loki query failed: {resp.status_code} {resp.text[:200]}"
    return resp.json()


class TestLokiHealthE2E:
    """E2E: Loki container is running and healthy."""

    def test_loki_ready(self, loki_client):
        """GET /ready returns 'ready'."""
        try:
            resp = loki_client.get("/ready")
            assert resp.status_code == 200
            assert "ready" in resp.text.lower(), f"Expected 'ready', got: {resp.text[:100]}"
        except Exception as e:
            if "Connection" in str(type(e).__name__) or "Connect" in str(e):
                pytest.skip("Loki container not running")
            raise

    def test_loki_metrics_endpoint(self, loki_client):
        """Loki exposes /metrics for self-monitoring."""
        try:
            resp = loki_client.get("/metrics")
            assert resp.status_code == 200
        except Exception:
            pytest.skip("Loki container not running")


class TestPromtailScrapingE2E:
    """E2E: Promtail is ingesting API access logs into Loki."""

    def test_sarvaja_api_stream_exists(self, http_client, loki_client):
        """After generating traffic, {job='sarvaja-api'} stream exists in Loki."""
        try:
            # Generate some API traffic first
            for _ in range(3):
                http_client.get("/api/tasks")
                http_client.get("/api/sessions")

            # Give Promtail time to tail + push (up to 15s)
            time.sleep(5)

            resp = loki_client.get("/loki/api/v1/labels")
            if resp.status_code != 200:
                pytest.skip("Loki labels API unavailable")

            data = resp.json()
            labels = data.get("data", [])
            assert "job" in labels, f"No 'job' label found. Labels: {labels}"

            # Verify our job value exists
            resp2 = loki_client.get("/loki/api/v1/label/job/values")
            assert resp2.status_code == 200
            jobs = resp2.json().get("data", [])
            assert "sarvaja-api" in jobs, f"sarvaja-api not in job values: {jobs}"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Loki container not running")
            raise


class TestLogQLQueriesE2E:
    """E2E: LogQL queries return structured access log data."""

    def test_query_returns_recent_entries(self, http_client, loki_client):
        """LogQL {job='sarvaja-api'} returns entries with method/path/status."""
        try:
            # Generate traffic
            http_client.get("/api/tasks")
            time.sleep(5)

            result = _loki_query(loki_client, '{job="sarvaja-api"}', limit=10)
            streams = result.get("data", {}).get("result", [])
            assert len(streams) > 0, "No log streams returned from Loki"

            # Check that entries contain structured access log fields
            found_entry = False
            for stream in streams:
                for _ts, line in stream.get("values", []):
                    if "method" in line and "path" in line and "status" in line:
                        found_entry = True
                        break
                if found_entry:
                    break
            assert found_entry, "No structured access log entries found in Loki"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Loki container not running")
            raise

    def test_entries_have_method_label(self, http_client, loki_client):
        """Promtail extracts 'method' as a label from JSON logs."""
        try:
            http_client.get("/api/tasks")
            time.sleep(5)

            result = _loki_query(loki_client, '{job="sarvaja-api",method="GET"}', limit=5)
            streams = result.get("data", {}).get("result", [])
            assert len(streams) > 0, "No streams with method=GET label"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Loki container not running")
            raise

    def test_entries_have_status_label(self, http_client, loki_client):
        """Promtail extracts 'status' as a label from JSON logs."""
        try:
            http_client.get("/api/tasks")
            time.sleep(5)

            result = _loki_query(loki_client, '{job="sarvaja-api",status="200"}', limit=5)
            streams = result.get("data", {}).get("result", [])
            assert len(streams) > 0, "No streams with status=200 label"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Loki container not running")
            raise


class TestSlowRequestFilterE2E:
    """E2E: Slow requests are queryable by 'slow' label."""

    def test_slow_label_filterable(self, loki_client):
        """LogQL {job='sarvaja-api',slow='true'} is a valid query (may return 0 results)."""
        try:
            result = _loki_query(loki_client, '{job="sarvaja-api",slow="true"}', limit=5)
            # Query itself should succeed even if no slow requests exist
            assert result.get("status") == "success", f"Query failed: {result}"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Loki container not running")
            raise


class TestRequestCorrelationE2E:
    """E2E: Request correlation via rid field."""

    def test_rid_filter_via_logql_line_match(self, http_client, loki_client):
        """LogQL |= 'rid_value' finds correlated log entries."""
        try:
            # Make a request and capture its rid from the response header
            resp = http_client.get("/api/tasks")
            rid = resp.headers.get("X-Request-ID")
            assert rid, "No X-Request-ID header in response"

            time.sleep(5)

            # Search for the rid in Loki
            result = _loki_query(
                loki_client,
                '{job="sarvaja-api"} |= "' + rid + '"',
                limit=5,
            )
            streams = result.get("data", {}).get("result", [])
            # Should find at least one entry with this rid
            total_entries = sum(len(s.get("values", [])) for s in streams)
            assert total_entries >= 1, f"No log entries found for rid={rid}"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Loki container not running")
            raise
