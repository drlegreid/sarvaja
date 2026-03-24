"""
P12 Integration Tests: Session Navigation Fix.

Per BUG-012: Verifies the full session navigation pipeline against live TypeDB.
Tests cover:
  - MCP-created sessions accessible via REST API
  - Session chip click → API load → navigation state
  - Back button → restore source task
  - FEAT-008 route hash integration
"""
import pytest
import httpx

API_BASE = "http://localhost:8082"
_cleanup_sessions = []
_cleanup_tasks = []


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up test sessions and tasks after each test."""
    yield
    for sid in _cleanup_sessions:
        try:
            httpx.delete(f"{API_BASE}/api/sessions/{sid}", timeout=5.0)
        except Exception:
            pass
    _cleanup_sessions.clear()
    for tid in _cleanup_tasks:
        try:
            httpx.delete(f"{API_BASE}/api/tasks/{tid}", timeout=5.0)
        except Exception:
            pass
    _cleanup_tasks.clear()


def _create_session(session_id: str, description: str = "test") -> dict:
    """Create a session via REST API."""
    resp = httpx.post(
        f"{API_BASE}/api/sessions",
        json={"session_id": session_id, "description": description},
        timeout=10.0,
    )
    assert resp.status_code == 201, f"Create session failed: {resp.text}"
    _cleanup_sessions.append(session_id)
    return resp.json()


def _create_task(task_id: str, session_id: str = None) -> dict:
    """Create a task via REST API, optionally linked to session."""
    payload = {
        "task_id": task_id,
        "description": f"Test task {task_id}",
        "status": "OPEN",
        "phase": "P12",
    }
    resp = httpx.post(f"{API_BASE}/api/tasks", json=payload, timeout=10.0)
    assert resp.status_code == 201, f"Create task failed: {resp.text}"
    _cleanup_tasks.append(task_id)
    if session_id:
        httpx.post(
            f"{API_BASE}/api/tasks/{task_id}/sessions/{session_id}",
            timeout=10.0,
        )
    return resp.json()


class TestSessionGetReturnsCorrectStatus:
    """BUG-013: GET session should return 404 (not 500) for missing sessions."""

    @pytest.mark.integration
    def test_missing_session_returns_404(self):
        resp = httpx.get(
            f"{API_BASE}/api/sessions/SESSION-NONEXISTENT-XYZ",
            timeout=10.0,
        )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    @pytest.mark.integration
    def test_existing_session_returns_200(self):
        sid = "SESSION-2026-03-23-P12-INT-GET-OK"
        _create_session(sid, "GET test")
        resp = httpx.get(f"{API_BASE}/api/sessions/{sid}", timeout=10.0)
        assert resp.status_code == 200
        assert resp.json()["session_id"] == sid


class TestSessionNavPipeline:
    """BUG-012: Full pipeline test — session chip → API load → nav state."""

    @pytest.mark.integration
    def test_session_accessible_after_rest_create(self):
        """Session created via REST API must be GET-able."""
        sid = "SESSION-2026-03-23-P12-INT-PIPELINE"
        _create_session(sid, "Pipeline test")
        resp = httpx.get(f"{API_BASE}/api/sessions/{sid}", timeout=10.0)
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == sid
        assert data["status"] == "ACTIVE"

    @pytest.mark.integration
    def test_task_session_link_visible_on_task_get(self):
        """Task linked to session shows session_id in linked_sessions."""
        sid = "SESSION-2026-03-23-P12-INT-LINK-VIS"
        tid = "P12-INT-LINK-VIS-001"
        _create_session(sid)
        _create_task(tid, session_id=sid)

        resp = httpx.get(f"{API_BASE}/api/tasks/{tid}", timeout=10.0)
        assert resp.status_code == 200
        task = resp.json()
        linked = task.get("linked_sessions", [])
        assert sid in linked, f"Session {sid} not in linked_sessions: {linked}"


class TestCrossNavGuardIntegration:
    """BUG-012: Cross-nav guard with routing integration."""

    @pytest.mark.integration
    def test_navigation_helpers_load_session_from_api(self):
        """_load_session_from_api returns dict for existing session."""
        from agent.governance_ui.controllers.tasks_navigation import (
            _load_session_from_api,
        )
        sid = "SESSION-2026-03-23-P12-INT-HELPER"
        _create_session(sid, "Helper test")

        result = _load_session_from_api(API_BASE, sid)
        assert result is not None
        assert result["session_id"] == sid

    @pytest.mark.integration
    def test_navigation_helpers_return_none_for_missing(self):
        """_load_session_from_api returns None for missing session."""
        from agent.governance_ui.controllers.tasks_navigation import (
            _load_session_from_api,
        )
        result = _load_session_from_api(API_BASE, "SESSION-DOESNT-EXIST")
        assert result is None

    @pytest.mark.integration
    def test_navigate_to_session_with_real_api(self):
        """Full navigate_to_session trigger against live API."""
        from unittest.mock import MagicMock

        from agent.governance_ui.controllers.tasks_navigation import (
            register_tasks_navigation,
        )

        sid = "SESSION-2026-03-23-P12-INT-NAV-FULL"
        _create_session(sid, "Full nav test")

        # Setup mock state + ctrl
        ctrl = MagicMock()
        state = MagicMock()
        state.sessions = []  # Empty cache — forces API load
        triggers = {}

        def trigger_decorator(name):
            def wrapper(fn):
                triggers[name] = fn
                return fn
            return wrapper

        ctrl.trigger = MagicMock(side_effect=trigger_decorator)
        register_tasks_navigation(state, ctrl, API_BASE)

        # Navigate to session
        triggers["navigate_to_session"](
            sid, source_view="tasks", source_id="T-1", source_label="Back to T-1"
        )

        # Verify navigation state
        assert state.active_view == "sessions"
        assert state.show_session_detail is True
        assert state.selected_session["session_id"] == sid
        assert state.nav_source_view == "tasks"
        assert state.nav_source_id == "T-1"
        assert state.cross_nav_in_progress is True


class TestRoutingWithNavigation:
    """FEAT-008: Route hash correctly reflects cross-nav state."""

    @pytest.mark.integration
    def test_route_hash_after_session_nav(self):
        """After navigate_to_session, state_to_hash produces session detail URL."""
        from unittest.mock import MagicMock
        from agent.governance_ui.routing.sync import RouteSyncBridge

        sid = "SESSION-2026-03-23-P12-INT-ROUTE"
        _create_session(sid)

        bridge = RouteSyncBridge()
        state = MagicMock()
        state.active_view = "sessions"
        state.show_session_detail = True
        state.selected_session = {"session_id": sid}
        state.current_project_id = "WS-9147535A"

        url_hash = bridge.state_to_hash(state)
        assert f"/sessions/{sid}" in url_hash
