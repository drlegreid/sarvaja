"""
E2E Tests for EPIC-PERF-TELEM-V1 Phase 4: Dashboard Parallel Loading.

Verifies parallel loading performance against live API:
1. Task detail GET + sub-resources completes in <2s
2. Session detail GET + sub-resources completes in <3s
3. Rapid task/session switching doesn't hang
4. All sub-sections populated after detail load

Prerequisites:
- API server running on port 8082
- TypeDB connected with tasks and sessions

Run:
    pytest tests/e2e/test_perf_telem_p4_e2e.py -v

Created: 2026-03-26
"""

import time
from concurrent.futures import ThreadPoolExecutor

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
    resp = httpx.get(f"{API_BASE_URL}/api/tasks", params={"limit": 5}, timeout=10.0)
    if resp.status_code != 200:
        pytest.skip("Cannot list tasks from API")
    data = resp.json()
    tasks = data if isinstance(data, list) else data.get("items", [])
    if not tasks:
        pytest.skip("No tasks in TypeDB to test against")
    return tasks[0].get("task_id") or tasks[0].get("id", "unknown")


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


def _get_multiple_task_ids(count=3) -> list:
    """Get multiple task IDs for rapid-switching test."""
    resp = httpx.get(f"{API_BASE_URL}/api/tasks", params={"limit": count}, timeout=10.0)
    if resp.status_code != 200:
        pytest.skip("Cannot list tasks from API")
    data = resp.json()
    tasks = data if isinstance(data, list) else data.get("items", [])
    if len(tasks) < 2:
        pytest.skip(f"Need at least 2 tasks, got {len(tasks)}")
    return [t.get("task_id") or t.get("id") for t in tasks[:count]]


def _get_multiple_session_ids(count=3) -> list:
    """Get multiple session IDs for rapid-switching test."""
    resp = httpx.get(f"{API_BASE_URL}/api/sessions", params={"limit": count}, timeout=10.0)
    if resp.status_code != 200:
        pytest.skip("Cannot list sessions from API")
    data = resp.json()
    sessions = data if isinstance(data, list) else data.get("items", [])
    if len(sessions) < 2:
        pytest.skip(f"Need at least 2 sessions, got {len(sessions)}")
    return [s.get("session_id") or s.get("id") for s in sessions[:count]]


# ── Feature: Task Detail Parallel Loading ────────────────────────


class TestTaskDetailPerformance:
    """Task detail + all sub-resources must load in <2s parallel."""

    def test_task_detail_under_2_seconds(self):
        """Simulating parallel load of task + 4 sub-resources."""
        task_id = _get_any_task_id()
        endpoints = [
            f"/api/tasks/{task_id}",
            f"/api/tasks/{task_id}/execution",
            f"/api/tasks/{task_id}/evidence/rendered",
            f"/api/tasks/{task_id}/timeline?per_page=50",
            f"/api/tasks/{task_id}/comments",
        ]

        start = time.monotonic()
        results = {}
        # Detail fetch first (synchronous in implementation)
        r = httpx.get(f"{API_BASE_URL}{endpoints[0]}", timeout=10.0)
        results["detail"] = r.status_code

        # 4 sub-resources in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            def _fetch(ep):
                resp = httpx.get(f"{API_BASE_URL}{ep}", timeout=10.0)
                return resp.status_code
            futures = {executor.submit(_fetch, ep): ep for ep in endpoints[1:]}
            for f in futures:
                results[futures[f]] = f.result()

        elapsed = time.monotonic() - start
        assert elapsed < 2.0, f"Task detail took {elapsed:.2f}s (target <2s)"
        # Detail should be 200
        assert results["detail"] == 200

    def test_all_task_sub_sections_populated(self):
        """All 4 sub-resources return data."""
        task_id = _get_any_task_id()
        with httpx.Client(timeout=10.0) as client:
            detail = client.get(f"{API_BASE_URL}/api/tasks/{task_id}")
            assert detail.status_code == 200

            execution = client.get(f"{API_BASE_URL}/api/tasks/{task_id}/execution")
            evidence = client.get(f"{API_BASE_URL}/api/tasks/{task_id}/evidence/rendered")
            timeline = client.get(f"{API_BASE_URL}/api/tasks/{task_id}/timeline",
                                  params={"per_page": 50})
            comments = client.get(f"{API_BASE_URL}/api/tasks/{task_id}/comments")

        # All should return 200 (even if empty lists)
        for name, resp in [("execution", execution), ("evidence", evidence),
                           ("timeline", timeline), ("comments", comments)]:
            assert resp.status_code in (200, 404), f"{name} returned {resp.status_code}"


class TestTaskRapidSwitching:
    """Rapid task switching must not hang."""

    def test_rapid_3_task_switch_no_hang(self):
        """Click 3 tasks in rapid succession — all complete within 6s total."""
        task_ids = _get_multiple_task_ids(3)
        start = time.monotonic()

        for tid in task_ids:
            # Fire all 5 requests per task (parallel sub-loaders)
            with ThreadPoolExecutor(max_workers=4) as executor:
                endpoints = [
                    f"/api/tasks/{tid}",
                    f"/api/tasks/{tid}/execution",
                    f"/api/tasks/{tid}/evidence/rendered",
                    f"/api/tasks/{tid}/timeline?per_page=50",
                    f"/api/tasks/{tid}/comments",
                ]
                futures = [executor.submit(
                    httpx.get, f"{API_BASE_URL}{ep}", timeout=10.0
                ) for ep in endpoints]
                for f in futures:
                    f.result()

        elapsed = time.monotonic() - start
        assert elapsed < 6.0, f"3 rapid switches took {elapsed:.2f}s (target <6s)"


# ── Feature: Session Detail Parallel Loading ─────────────────────


class TestSessionDetailPerformance:
    """Session detail + 7 sub-resources must load in <3s parallel."""

    def test_session_detail_under_3_seconds(self):
        """Simulating parallel load of session + 7 sub-resources."""
        session_id = _get_any_session_id()
        endpoints = [
            f"/api/sessions/{session_id}/evidence",
            f"/api/sessions/{session_id}/tasks",
            f"/api/sessions/{session_id}/tools?per_page=100",
            f"/api/sessions/{session_id}/thoughts?per_page=100",
            f"/api/sessions/{session_id}/evidence/rendered",
            f"/api/sessions/{session_id}/transcript?page=1&per_page=50",
            f"/api/sessions/{session_id}/validate",
        ]

        start = time.monotonic()
        # Detail fetch first (synchronous)
        r = httpx.get(f"{API_BASE_URL}/api/sessions/{session_id}", timeout=10.0)
        assert r.status_code == 200

        # 7 sub-resources in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            def _fetch(ep):
                resp = httpx.get(f"{API_BASE_URL}{ep}", timeout=10.0)
                return resp.status_code
            futures = {executor.submit(_fetch, ep): ep for ep in endpoints}
            results = {}
            for f in futures:
                results[futures[f]] = f.result()

        elapsed = time.monotonic() - start
        assert elapsed < 3.0, f"Session detail took {elapsed:.2f}s (target <3s)"

    def test_all_session_sub_sections_respond(self):
        """All 7 sub-resource endpoints return 200 or 404."""
        session_id = _get_any_session_id()
        endpoints = {
            "evidence": f"/api/sessions/{session_id}/evidence",
            "tasks": f"/api/sessions/{session_id}/tasks",
            "tools": f"/api/sessions/{session_id}/tools",
            "thoughts": f"/api/sessions/{session_id}/thoughts",
            "evidence_rendered": f"/api/sessions/{session_id}/evidence/rendered",
            "transcript": f"/api/sessions/{session_id}/transcript",
            "validate": f"/api/sessions/{session_id}/validate",
        }
        with httpx.Client(timeout=10.0) as client:
            for name, ep in endpoints.items():
                resp = client.get(f"{API_BASE_URL}{ep}")
                assert resp.status_code in (200, 404), (
                    f"{name} returned {resp.status_code}"
                )


class TestSessionRapidSwitching:
    """Rapid session switching must not hang."""

    def test_rapid_3_session_switch_no_hang(self):
        """Click 3 sessions rapidly — all complete within 9s."""
        session_ids = _get_multiple_session_ids(3)
        start = time.monotonic()

        for sid in session_ids:
            with ThreadPoolExecutor(max_workers=4) as executor:
                endpoints = [
                    f"/api/sessions/{sid}",
                    f"/api/sessions/{sid}/evidence",
                    f"/api/sessions/{sid}/tasks",
                    f"/api/sessions/{sid}/tools?per_page=100",
                    f"/api/sessions/{sid}/thoughts?per_page=100",
                    f"/api/sessions/{sid}/evidence/rendered",
                    f"/api/sessions/{sid}/transcript?page=1&per_page=50",
                    f"/api/sessions/{sid}/validate",
                ]
                futures = [executor.submit(
                    httpx.get, f"{API_BASE_URL}{ep}", timeout=10.0
                ) for ep in endpoints]
                for f in futures:
                    f.result()

        elapsed = time.monotonic() - start
        assert elapsed < 9.0, f"3 rapid session switches took {elapsed:.2f}s (target <9s)"
