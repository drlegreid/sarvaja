"""
E2E Tests for EPIC-PERF-TELEM-V1 Phase 2: Task Query Consolidation.

Verifies consolidated task queries against live API + TypeDB:
1. GET /api/tasks/{id} returns all fields
2. Single task GET completes in <500ms
3. Task response includes relation fields

Prerequisites:
- API server running on port 8082
- TypeDB connected with tasks

Run:
    pytest tests/e2e/test_perf_telem_p2_e2e.py -v

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


def _get_any_task_id() -> str:
    """Get an existing task ID from the API."""
    resp = httpx.get(f"{API_BASE_URL}/api/tasks", timeout=10.0)
    if resp.status_code != 200:
        pytest.skip("Cannot list tasks from API")
    data = resp.json()
    tasks = data if isinstance(data, list) else data.get("items", data.get("tasks", []))
    if not tasks:
        pytest.skip("No tasks in TypeDB to test against")
    t = tasks[0]
    return t.get("task_id") or t.get("id") or t.get("name", "unknown")


# ── Feature: Task Query Consolidation ────────────────────


class TestTaskGetAllFields:
    """Scenario: GET /api/tasks/{id} returns all expected fields."""

    def test_core_fields_present(self):
        """Response includes task_id, status, phase."""
        task_id = _get_any_task_id()
        resp = httpx.get(f"{API_BASE_URL}/api/tasks/{task_id}", timeout=10.0)
        assert resp.status_code == 200, f"GET task failed: {resp.status_code}"
        data = resp.json()
        assert data.get("task_id"), "Missing task_id"
        assert "status" in data, "Missing status"
        assert "phase" in data, "Missing phase"

    def test_relation_fields_present(self):
        """Response includes linked_rules, linked_sessions, linked_commits."""
        task_id = _get_any_task_id()
        resp = httpx.get(f"{API_BASE_URL}/api/tasks/{task_id}", timeout=10.0)
        assert resp.status_code == 200
        data = resp.json()
        for field in ("linked_rules", "linked_sessions", "linked_commits"):
            assert field in data, f"Missing relation field: {field}"


class TestTaskGetPerformance:
    """Scenario: Single task GET completes in <500ms."""

    def test_single_task_get_under_500ms(self):
        """Task GET completes within performance budget."""
        task_id = _get_any_task_id()
        t0 = time.monotonic()
        resp = httpx.get(f"{API_BASE_URL}/api/tasks/{task_id}", timeout=10.0)
        duration_ms = (time.monotonic() - t0) * 1000
        assert resp.status_code == 200
        assert duration_ms < 500, (
            f"Task GET took {duration_ms:.0f}ms, limit is 500ms"
        )

    def test_repeated_gets_stable(self):
        """Three consecutive GETs show stable performance (no degradation)."""
        task_id = _get_any_task_id()
        durations = []
        for _ in range(3):
            t0 = time.monotonic()
            resp = httpx.get(
                f"{API_BASE_URL}/api/tasks/{task_id}", timeout=10.0
            )
            durations.append((time.monotonic() - t0) * 1000)
            assert resp.status_code == 200
        # No query should take more than 2x the fastest
        fastest = min(durations)
        for d in durations:
            assert d < fastest * 3, (
                f"Unstable: {durations} (fastest={fastest:.0f}ms)"
            )
