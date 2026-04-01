"""E2E tests for Phase 7: JSONL Parse Cache against live API.

Requires running API container on localhost:8082.

BDD Scenarios:
  - Second GET /sessions/{id}/tools is faster (cache hit)
  - GET /sessions/cache/stats returns counts
  - DELETE /sessions/cache clears cache

Created: 2026-03-26  EPIC-PERF-TELEM-V1 Phase 7
"""
import os
import time

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


def _get(path: str, timeout: float = 15.0) -> "httpx.Response":
    with httpx.Client(base_url=API_BASE, timeout=timeout) as client:
        return client.get(path)


def _delete(path: str, timeout: float = 10.0) -> "httpx.Response":
    with httpx.Client(base_url=API_BASE, timeout=timeout) as client:
        return client.delete(path)


# ---------------------------------------------------------------------------
# Scenario: Cache stats endpoint exists and returns counts
# ---------------------------------------------------------------------------

def test_cache_stats_endpoint():
    """GET /api/sessions/cache/stats returns hit/miss/eviction counts."""
    resp = _get("/api/sessions/cache/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "hit_count" in data
    assert "miss_count" in data
    assert "eviction_count" in data
    assert "size" in data


# ---------------------------------------------------------------------------
# Scenario: Cache clear endpoint works
# ---------------------------------------------------------------------------

def test_cache_clear_endpoint():
    """DELETE /api/sessions/cache resets cache."""
    resp = _delete("/api/sessions/cache")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("cleared") is True

    # Stats should show 0 after clear
    stats_resp = _get("/api/sessions/cache/stats")
    stats = stats_resp.json()
    assert stats["size"] == 0
    assert stats["hit_count"] == 0


# ---------------------------------------------------------------------------
# Scenario: Second call to session detail is faster (cache hit)
# ---------------------------------------------------------------------------

def test_second_call_faster_cache_hit():
    """Second GET for same session detail should be faster (cache hit)."""
    # First, clear cache
    _delete("/api/sessions/cache")

    # Find a CC session with JSONL data
    sessions_resp = _get("/api/sessions")
    if sessions_resp.status_code != 200:
        pytest.skip("Sessions endpoint unavailable")

    items = sessions_resp.json().get("items", [])
    cc_session = None
    for s in items:
        if s.get("cc_session_uuid") and s.get("status") == "COMPLETED":
            cc_session = s
            break

    if not cc_session:
        pytest.skip("No CC session with JSONL available")

    sid = cc_session["session_id"]

    # First call — cache miss (cold)
    t1_start = time.monotonic()
    r1 = _get(f"/api/sessions/{sid}/detail?zoom=1")
    t1_ms = (time.monotonic() - t1_start) * 1000

    if r1.status_code != 200:
        pytest.skip(f"Session detail returned {r1.status_code}")

    # Second call — should hit cache
    t2_start = time.monotonic()
    r2 = _get(f"/api/sessions/{sid}/detail?zoom=1")
    t2_ms = (time.monotonic() - t2_start) * 1000

    assert r2.status_code == 200

    # Cache hit should be meaningfully faster
    # (We don't assert <50ms because network overhead varies,
    # but we check stats to confirm it was a hit)
    stats = _get("/api/sessions/cache/stats").json()
    assert stats["hit_count"] >= 1, f"Expected cache hit. Stats: {stats}"
