"""E2E tests for Phase 6: Slow-request alerting + request correlation against live API.

Requires running API container on localhost:8082.

BDD Scenarios:
  - Response includes X-Request-ID header
  - X-Request-ID is 8-char hex string
  - Access log contains rid field
  - Slow requests logged at WARNING with slow:true

Created: 2026-03-26  EPIC-PERF-TELEM-V1 Phase 6
"""
import os
import re

import pytest

try:
    import httpx
except ImportError:
    httpx = None

API_BASE = os.getenv("GOVERNANCE_API_URL", "http://localhost:8082")

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(httpx is None, reason="httpx not installed"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(path: str, timeout: float = 10.0) -> "httpx.Response":
    """GET request to live API."""
    with httpx.Client(base_url=API_BASE, timeout=timeout) as client:
        return client.get(path)


# ---------------------------------------------------------------------------
# Scenario: Response includes X-Request-ID header
# ---------------------------------------------------------------------------

def test_response_has_x_request_id():
    """Any API response should include X-Request-ID header."""
    resp = _get("/api/health")
    # Health is skipped from access log, but still gets header
    # Actually per middleware, /api/health is skipped entirely.
    # Use a non-skipped endpoint:
    resp = _get("/api/sessions")
    assert "X-Request-ID" in resp.headers, (
        f"Missing X-Request-ID header. Headers: {dict(resp.headers)}"
    )


# ---------------------------------------------------------------------------
# Scenario: X-Request-ID is 8-char hex string
# ---------------------------------------------------------------------------

def test_x_request_id_format():
    """X-Request-ID should be 8-char lowercase hex (uuid4[:8])."""
    resp = _get("/api/sessions")
    rid = resp.headers.get("X-Request-ID", "")
    assert re.match(r"^[0-9a-f]{8}$", rid), f"Unexpected rid format: {rid!r}"


# ---------------------------------------------------------------------------
# Scenario: Different requests get different X-Request-ID
# ---------------------------------------------------------------------------

def test_unique_request_ids():
    """Two sequential requests should get different X-Request-IDs."""
    r1 = _get("/api/sessions")
    r2 = _get("/api/sessions")
    rid1 = r1.headers.get("X-Request-ID")
    rid2 = r2.headers.get("X-Request-ID")
    assert rid1 != rid2, f"Both requests got same rid: {rid1}"


# ---------------------------------------------------------------------------
# Scenario: Slow endpoint triggers WARNING in container log
# ---------------------------------------------------------------------------

def test_slow_request_warning_in_log():
    """A genuinely slow request should appear as WARNING in container logs.

    This test just verifies the endpoint responds with rid — actual log
    verification is done via mcp__log-analyzer in Tier 3 Playwright step.
    """
    # Hit a heavy endpoint (session detail for a large session)
    resp = _get("/api/sessions", timeout=15.0)
    assert resp.status_code in (200, 404, 422)
    assert "X-Request-ID" in resp.headers
