"""Tests for Fix A: Tests auto-load on dashboard init.

Validates that _load_tests() is called during load_initial_data() and
populates state.tests_recent_runs + state.tests_cvp_status.
"""
from unittest.mock import MagicMock, patch
import pytest


def _make_mock_client(test_runs=None, cvp_status=None):
    """Build a mock httpx client with test and CVP responses."""
    def mock_get(url, **kwargs):
        resp = MagicMock()
        if "/api/tests/results" in url:
            resp.status_code = 200
            resp.json.return_value = {"runs": test_runs or []}
        elif "/api/tests/cvp/status" in url:
            resp.status_code = 200
            resp.json.return_value = cvp_status or {"pipeline_health": "unknown"}
        elif "/api/rules" in url:
            resp.status_code = 200
            resp.json.return_value = {"items": []}
        elif "/api/decisions" in url:
            resp.status_code = 200
            resp.json.return_value = {"items": []}
        elif "/api/sessions" in url:
            resp.status_code = 200
            resp.json.return_value = {"items": [], "pagination": {}}
        elif "/api/agents" in url:
            resp.status_code = 200
            resp.json.return_value = {"items": []}
        elif "/api/tasks" in url:
            resp.status_code = 200
            resp.json.return_value = {"items": [], "pagination": {}}
        elif "/api/projects" in url:
            resp.status_code = 200
            resp.json.return_value = {"items": []}
        else:
            resp.status_code = 404
        return resp

    client = MagicMock()
    client.get = mock_get
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)
    return client


def test_load_tests_populates_recent_runs():
    """_load_tests sets state.tests_recent_runs from API response."""
    from agent.governance_ui.dashboard_data_loader import _load_tests

    state = MagicMock()
    runs = [{"run_id": "RUN-001", "status": "completed", "passed": 10}]
    client = _make_mock_client(test_runs=runs)

    _load_tests(state, client, "http://localhost:8082")

    assert state.tests_recent_runs == runs


def test_load_tests_populates_cvp_status():
    """_load_tests sets state.tests_cvp_status from CVP endpoint."""
    from agent.governance_ui.dashboard_data_loader import _load_tests

    state = MagicMock()
    cvp = {"pipeline_health": "healthy", "total_cvp_runs": 5}
    client = _make_mock_client(cvp_status=cvp)

    _load_tests(state, client, "http://localhost:8082")

    assert state.tests_cvp_status == cvp


def test_load_tests_handles_api_failure():
    """_load_tests gracefully handles API errors."""
    from agent.governance_ui.dashboard_data_loader import _load_tests

    state = MagicMock()
    client = MagicMock()
    client.get.side_effect = Exception("Connection refused")

    _load_tests(state, client, "http://localhost:8082")

    assert state.tests_recent_runs == []


def test_load_initial_data_calls_load_tests():
    """load_initial_data calls _load_tests during startup."""
    from agent.governance_ui.dashboard_data_loader import load_initial_data

    state = MagicMock()
    runs = [{"run_id": "RUN-002"}]
    client = _make_mock_client(test_runs=runs)

    with patch("httpx.Client") as mock_httpx_cls:
        mock_httpx_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_httpx_cls.return_value.__exit__ = MagicMock(return_value=False)
        load_initial_data(
            state, "http://localhost:8082",
            get_rules=lambda: [], get_decisions=lambda: [],
            get_sessions=lambda limit=100: [], get_tasks=lambda: [],
        )

    assert state.tests_recent_runs == runs


def test_initial_state_has_cvp_status():
    """State initialization includes tests_cvp_status field."""
    from agent.governance_ui.state.initial import get_initial_state
    init = get_initial_state()
    assert "tests_cvp_status" in init
    assert init["tests_cvp_status"] is None
