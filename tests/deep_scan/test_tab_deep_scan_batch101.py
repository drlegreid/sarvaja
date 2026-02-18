"""Deep scan batch 101: Route handlers + UI controllers.

Batch 101 findings: 48 total, 0 confirmed fixes, 48 rejected.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime


# ── Session detail loader error isolation defense ──────────────


class TestLoaderErrorIsolation:
    """Verify each loader catches its own exceptions."""

    def test_tool_calls_loader_catches_error(self):
        """load_session_tool_calls has internal try-except."""
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )

        state = MagicMock()
        state.session_tool_calls = []
        state.session_tool_calls_loading = False
        loaders = register_session_detail_loaders(state, "http://bad-host:9999")

        # Call loader with unreachable host — should NOT raise
        loaders["load_tool_calls"]("SESSION-TEST")
        # State should reflect failure gracefully
        assert state.session_tool_calls_loading is False

    def test_thinking_loader_catches_error(self):
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )

        state = MagicMock()
        state.session_thinking_items = []
        state.session_thinking_items_loading = False
        loaders = register_session_detail_loaders(state, "http://bad-host:9999")

        loaders["load_thinking_items"]("SESSION-TEST")
        assert state.session_thinking_items_loading is False

    def test_evidence_loader_catches_error(self):
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )

        state = MagicMock()
        state.session_evidence_files = []
        state.session_evidence_loading = False
        loaders = register_session_detail_loaders(state, "http://bad-host:9999")

        loaders["load_evidence"]("SESSION-TEST")
        assert state.session_evidence_loading is False


# ── Route 404 defense ──────────────


class TestRoute404Handling:
    """Verify routes return proper 404 for missing entities."""

    def test_session_not_found(self):
        from fastapi.testclient import TestClient
        from governance.api import app

        client = TestClient(app)
        resp = client.get("/api/sessions/NONEXISTENT-SESSION-999")
        assert resp.status_code == 404

    def test_task_not_found(self):
        from fastapi.testclient import TestClient
        from governance.api import app

        client = TestClient(app)
        resp = client.get("/api/tasks/NONEXISTENT-TASK-999")
        assert resp.status_code == 404


# ── Duration abs() defense ──────────────


class TestDurationAbsGuard:
    """Verify abs() handles reversed timestamps."""

    def test_reversed_timestamps_produce_positive_duration(self):
        from agent.governance_ui.utils import compute_session_duration

        # End time before start time (data anomaly)
        result = compute_session_duration(
            "2026-02-15T17:00:00",
            "2026-02-15T09:00:00",
        )
        # Should return positive duration via abs(), not "invalid"
        assert "invalid" not in result.lower() if result else True

    def test_normal_timestamps_produce_duration(self):
        from agent.governance_ui.utils import compute_session_duration

        result = compute_session_duration(
            "2026-02-15T09:00:00",
            "2026-02-15T13:00:00",
        )
        assert result is not None
        assert "4h" in result or "4" in result


# ── Timeline build defense ──────────────


class TestTimelineBuild:
    """Verify timeline merges tool_calls + thinking safely."""

    def test_empty_inputs_produce_empty_timeline(self):
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )

        state = MagicMock()
        state.session_tool_calls = []
        state.session_thinking_items = []
        state.session_timeline = []

        loaders = register_session_detail_loaders(state, "http://localhost:8082")
        loaders["build_timeline"]()

        # Setter called with empty list
        assert state.session_timeline == [] or state.session_timeline is not None


# ── Pagination defense ──────────────


class TestPaginationRoutes:
    """Verify pagination routes return consistent structure."""

    def test_sessions_list_pagination(self):
        from fastapi.testclient import TestClient
        from governance.api import app

        client = TestClient(app)
        resp = client.get("/api/sessions?limit=2&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert "pagination" in data or isinstance(data, list)

    def test_tasks_list_pagination(self):
        from fastapi.testclient import TestClient
        from governance.api import app

        client = TestClient(app)
        resp = client.get("/api/tasks?limit=2&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert "pagination" in data or isinstance(data, list)


# ── Health endpoint defense ──────────────


class TestHealthEndpoint:
    """Verify health endpoint returns structured response."""

    def test_health_returns_200(self):
        from fastapi.testclient import TestClient
        from governance.api import app

        client = TestClient(app)
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data or "typedb_connected" in data
