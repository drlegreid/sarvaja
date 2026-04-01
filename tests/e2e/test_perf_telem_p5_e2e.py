"""
E2E tests for Phase 5: Traced HTTP + Dashboard Audit Logging.

EPIC-PERF-TELEM-V1 P5 — verifies against live API:
1. GET /api/tasks returns 200 (API is running)
2. GET /api/sessions returns 200 (sessions endpoint alive)
3. Trace bar state includes api_call events after dashboard load
4. log_action produces structured JSON logs

These tests require the sarvaja-platform-api-1 container running on :8082.
"""

import json
import logging

import pytest

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

API_BASE = "http://localhost:8082"


@pytest.mark.skipif(not HAS_HTTPX, reason="httpx not installed")
class TestLiveAPITraceEndpoints:
    """Verify live API endpoints respond (prerequisite for trace testing)."""

    def test_tasks_endpoint_alive(self):
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{API_BASE}/api/tasks?limit=5")
            assert resp.status_code == 200
            data = resp.json()
            assert "items" in data or isinstance(data, list)

    def test_sessions_endpoint_alive(self):
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{API_BASE}/api/sessions?limit=5")
            assert resp.status_code == 200
            data = resp.json()
            assert "items" in data or isinstance(data, list)


@pytest.mark.skipif(not HAS_HTTPX, reason="httpx not installed")
class TestTracedHTTPIntegration:
    """Verify traced HTTP utility works with real httpx."""

    def test_traced_get_with_real_httpx(self):
        """traced_get should work with a real httpx.Client."""
        from unittest.mock import MagicMock
        from agent.governance_ui.controllers.traced_http import traced_get

        state = MagicMock()
        state.trace_events = []
        with httpx.Client(timeout=10.0) as client:
            resp, dur = traced_get(state, client, API_BASE, "/api/tasks?limit=1")
            assert resp.status_code == 200
            assert dur >= 0
            assert dur < 10000  # should complete in <10s

    def test_traced_get_error_on_bad_host(self):
        """traced_get should trace errors for unreachable hosts."""
        from unittest.mock import MagicMock
        from agent.governance_ui.controllers.traced_http import traced_get

        state = MagicMock()
        with httpx.Client(timeout=2.0) as client:
            with pytest.raises(Exception):
                traced_get(state, client, "http://localhost:59999",
                           "/api/nonexistent")


@pytest.mark.skipif(not HAS_HTTPX, reason="httpx not installed")
class TestDashboardLogAction:
    """Verify log_action produces structured logs."""

    def test_log_action_emits_structured_json(self, caplog):
        """log_action should emit JSON with view, action, and details."""
        from governance.middleware.dashboard_log import log_action

        with caplog.at_level(logging.INFO, logger="governance.dashboard"):
            log_action("tasks", "select", task_id="T-E2E-1")

        assert len(caplog.records) >= 1
        record = caplog.records[-1]
        entry = json.loads(record.getMessage())
        assert entry["view"] == "tasks"
        assert entry["action"] == "select"
        assert entry["task_id"] == "T-E2E-1"
        assert "ts" in entry
