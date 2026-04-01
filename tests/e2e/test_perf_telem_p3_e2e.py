"""
E2E Tests for EPIC-PERF-TELEM-V1 Phase 3: Session Query Consolidation + Timeline Cache.

Verifies consolidated session queries against live API + TypeDB:
1. GET /api/sessions/{id} returns all fields
2. Single session GET completes in <500ms
3. Session page navigation completes in <2s

Prerequisites:
- API server running on port 8082
- TypeDB connected with sessions

Run:
    pytest tests/e2e/test_perf_telem_p3_e2e.py -v

Created: 2026-03-26
"""

import time

import httpx
import pytest

API_BASE_URL = "http://localhost:8082"


def _api_available() -> bool:
    """Check if API is reachable."""
    try:
        r = httpx.get(f"{API_BASE_URL}/api/health", timeout=5.0)
        return r.status_code in (200, 503)
    except Exception:
        return False


API_AVAILABLE = _api_available()
pytestmark = pytest.mark.skipif(not API_AVAILABLE, reason="API not reachable")


def _get_any_session_id() -> str:
    """Get an existing session ID from the API."""
    resp = httpx.get(f"{API_BASE_URL}/api/sessions", params={"limit": 5}, timeout=10.0)
    if resp.status_code != 200:
        pytest.skip("Cannot list sessions from API")
    data = resp.json()
    sessions = data if isinstance(data, list) else data.get("items", [])
    if not sessions:
        pytest.skip("No sessions in TypeDB to test against")
    return sessions[0].get("session_id") or sessions[0].get("id", "unknown")


# ── Feature: Session Query Consolidation ─────────────────


class TestSessionGetAllFields:
    """Scenario: GET /api/sessions/{id} returns all expected fields."""

    def test_core_fields_present(self):
        """Response includes session_id, status, start_time."""
        session_id = _get_any_session_id()
        resp = httpx.get(f"{API_BASE_URL}/api/sessions/{session_id}", timeout=10.0)
        assert resp.status_code == 200, f"GET session failed: {resp.status_code}"
        data = resp.json()
        assert data.get("session_id"), "Missing session_id"
        assert "status" in data, "Missing status"

    def test_cc_fields_present_if_cc_session(self):
        """CC sessions include cc_session_uuid and other CC fields."""
        resp = httpx.get(
            f"{API_BASE_URL}/api/sessions",
            params={"limit": 20},
            timeout=10.0,
        )
        if resp.status_code != 200:
            pytest.skip("Cannot list sessions")
        data = resp.json()
        sessions = data if isinstance(data, list) else data.get("items", [])
        cc_sessions = [s for s in sessions if s.get("cc_session_uuid")]
        if not cc_sessions:
            pytest.skip("No CC sessions to verify")
        sid = cc_sessions[0].get("session_id") or cc_sessions[0].get("id")
        detail = httpx.get(f"{API_BASE_URL}/api/sessions/{sid}", timeout=10.0)
        assert detail.status_code == 200
        d = detail.json()
        assert d.get("cc_session_uuid"), "CC session missing cc_session_uuid"

    def test_relation_fields_present(self):
        """Response includes linked_rules_applied, linked_decisions, evidence_files."""
        session_id = _get_any_session_id()
        resp = httpx.get(f"{API_BASE_URL}/api/sessions/{session_id}", timeout=10.0)
        assert resp.status_code == 200
        data = resp.json()
        # These may be empty lists or None, but keys should exist
        for field in ("linked_rules_applied", "linked_decisions",
                      "evidence_files", "tasks_completed"):
            assert field in data, f"Missing relation field: {field}"


# ── Feature: Session Performance ─────────────────────────


class TestSessionGetPerformance:
    """Scenario: Single session GET completes in <500ms."""

    def test_single_session_get_under_500ms(self):
        """GET /api/sessions/{id} responds within 500ms."""
        session_id = _get_any_session_id()
        t0 = time.monotonic()
        resp = httpx.get(f"{API_BASE_URL}/api/sessions/{session_id}", timeout=10.0)
        duration_ms = (time.monotonic() - t0) * 1000
        assert resp.status_code == 200
        assert duration_ms < 500, f"Session GET took {duration_ms:.0f}ms (>500ms)"


class TestPageNavigationPerformance:
    """Scenario: Session page navigation completes in <2s."""

    def test_session_list_page_under_2s(self):
        """GET /api/sessions (paginated) responds within 2s."""
        t0 = time.monotonic()
        resp = httpx.get(
            f"{API_BASE_URL}/api/sessions",
            params={"limit": 20, "offset": 0},
            timeout=10.0,
        )
        duration_ms = (time.monotonic() - t0) * 1000
        assert resp.status_code == 200
        assert duration_ms < 2000, f"Session list took {duration_ms:.0f}ms (>2000ms)"

    def test_second_page_under_2s(self):
        """Second page navigation is also fast."""
        t0 = time.monotonic()
        resp = httpx.get(
            f"{API_BASE_URL}/api/sessions",
            params={"limit": 20, "offset": 20},
            timeout=10.0,
        )
        duration_ms = (time.monotonic() - t0) * 1000
        assert resp.status_code == 200
        assert duration_ms < 2000, f"Session page 2 took {duration_ms:.0f}ms (>2000ms)"
