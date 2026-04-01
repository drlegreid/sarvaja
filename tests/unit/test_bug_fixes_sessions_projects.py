"""
Unit tests for bug fixes: BUG-UI-SESSIONS-001/002/003 and BUG-API-PROJECTS-001.

Batch 173: Tests verifying fixes for:
- BUG-UI-SESSIONS-001: Total Duration computed from ALL sessions, not current page
- BUG-UI-SESSIONS-002: Session filters use @state.change only (no update_modelValue)
- BUG-UI-SESSIONS-003: source_type derivation in load_sessions_page
- BUG-API-PROJECTS-001: list_projects deduplicates project IDs
"""

from unittest.mock import patch, MagicMock
import pytest

# ── Helpers ───────────────────────────────────────────

_MOD = "agent.governance_ui.controllers.sessions_pagination"


def _mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


def _make_state(**attrs):
    s = MagicMock()
    defaults = {
        "sessions_page": 1,
        "sessions_per_page": 20,
        "sessions_filter_status": None,
        "sessions_filter_agent": None,
        "sessions_view_mode": "table",
        "sessions_pivot_group_by": "agent_id",
    }
    defaults.update(attrs)
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


def _make_ctrl():
    triggers = {}
    changes = {}
    ctrl = MagicMock()

    def trigger_decorator(name):
        def decorator(fn):
            triggers[name] = fn
            return fn
        return decorator

    ctrl.trigger = trigger_decorator
    return ctrl, triggers, changes


def _setup(**state_attrs):
    from agent.governance_ui.controllers.sessions_pagination import (
        register_sessions_pagination,
    )
    state = _make_state(**state_attrs)
    ctrl, triggers, changes = _make_ctrl()
    state.change = lambda name: (lambda fn: changes.update({name: fn}) or fn)
    loader = register_sessions_pagination(state, ctrl, "http://localhost:8082")
    return state, triggers, changes, loader


# ── BUG-UI-SESSIONS-001: Metrics from ALL sessions ───


class TestBugSessionsMetricsAllSessions:
    """BUG-UI-SESSIONS-001: Total Duration must be computed from ALL sessions,
    not just the current page (which may show 0h for test sessions)."""

    @patch(f"{_MOD}.has_plotly", return_value=False)
    @patch(f"{_MOD}.compute_timeline_data", return_value=([], []))
    @patch(f"{_MOD}.compute_session_duration", return_value="<1m")
    @patch(f"{_MOD}.compute_session_metrics")
    @patch(f"{_MOD}.format_timestamps_in_list", side_effect=lambda items, _: items)
    @patch("httpx.Client")
    def test_metrics_computed_from_all_sessions_not_page(
        self, MockClient, mock_fmt, mock_metrics, mock_dur, mock_tl, mock_plotly
    ):
        """The _update_timeline_and_metrics call should fetch limit=200 and
        compute metrics from that full dataset, not from the page items."""
        # Page items (20 test sessions with 0 duration)
        page_items = [
            {"session_id": f"S-{i}", "agent_id": "test-agent",
             "start_time": "2026-02-14T00:00:00", "end_time": "2026-02-14T00:00:01"}
            for i in range(20)
        ]
        # All items (200 sessions with real durations)
        all_items = [
            {"session_id": f"S-{i}", "agent_id": "code-agent",
             "start_time": "2026-01-01T00:00:00", "end_time": "2026-01-02T00:00:00"}
            for i in range(87)
        ]

        mc = MagicMock()
        # First call: paginated page (20 items)
        # Second call: all sessions (limit=200) for timeline+metrics
        mc.get.side_effect = [
            _mock_response(200, {
                "items": page_items,
                "pagination": {"total": 87, "offset": 0, "limit": 20, "has_more": True},
            }),
            _mock_response(200, {"items": all_items}),
        ]
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        # Return different values for page vs all
        call_count = [0]
        def metrics_side_effect(items):
            call_count[0] += 1
            if len(items) == 87:
                return {"duration": "14349h", "avg_tasks": 0.9}
            return {"duration": "0h", "avg_tasks": 0}
        mock_metrics.side_effect = metrics_side_effect

        state, _, _, loader = _setup()
        loader()

        # The LAST metrics call should be from all_items (87 items)
        # which sets the real duration
        assert state.sessions_metrics_duration == "14349h"

    @patch(f"{_MOD}.has_plotly", return_value=False)
    @patch(f"{_MOD}.compute_timeline_data", return_value=([], []))
    @patch(f"{_MOD}.compute_session_duration", return_value="<1m")
    @patch(f"{_MOD}.compute_session_metrics",
           return_value={"duration": "5000h", "avg_tasks": 3})
    @patch(f"{_MOD}.format_timestamps_in_list", side_effect=lambda items, _: items)
    @patch("httpx.Client")
    def test_timeline_call_uses_limit_200(
        self, MockClient, mock_fmt, mock_metrics, mock_dur, mock_tl, mock_plotly
    ):
        """The second API call must use limit=200 to get all sessions."""
        # Clear module-level timeline cache from prior tests
        from agent.governance_ui.controllers.sessions_pagination import _timeline_cache
        _timeline_cache.clear()

        mc = MagicMock()
        mc.get.return_value = _mock_response(200, {"items": []})
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, _, loader = _setup()
        loader()

        # Should have 2 calls: paginated page + all sessions
        assert mc.get.call_count == 2
        second_call = mc.get.call_args_list[1]
        assert second_call[1]["params"]["limit"] == 200


# ── BUG-UI-SESSIONS-002: Filter double-fire prevention ──


class TestBugSessionsFilterDoubleFire:
    """BUG-UI-SESSIONS-002: Filters should only use @state.change handlers,
    NOT update_modelValue triggers (which cause double-fire race conditions)."""

    def test_state_change_handlers_registered(self):
        """@state.change handlers must be registered for both filters."""
        _, _, changes, _ = _setup()
        assert "sessions_filter_status" in changes
        assert "sessions_filter_agent" in changes

    def test_state_change_resets_page_to_1(self):
        """Filter change must reset to page 1."""
        state, _, changes, _ = _setup(sessions_page=3)
        # Simulate a filter change — the handler resets page
        # (will fail to load because httpx not mocked, but page should be set)
        try:
            changes["sessions_filter_status"]("ACTIVE")
        except Exception:
            pass  # httpx error expected — we just check the page reset
        assert state.sessions_page == 1

    def test_no_update_model_value_on_filter_selects(self):
        """VSelects for status/agent filters must NOT have update_modelValue.
        The VBtnToggle for view mode is OK to keep update_modelValue."""
        import inspect
        from agent.governance_ui.views.sessions import list as list_module

        source = inspect.getsource(list_module._build_filters_row)
        # Extract lines around VSelect (not VBtnToggle)
        lines = source.split("\n")
        in_vselect = False
        vselect_model_values = 0
        for line in lines:
            stripped = line.strip()
            if "VSelect(" in stripped or "v3.VSelect(" in stripped:
                in_vselect = True
            if in_vselect and "update_modelValue" in stripped:
                vselect_model_values += 1
            if in_vselect and stripped.startswith(")"):
                in_vselect = False
        # VSelects should have 0 update_modelValue (was 2 before fix)
        assert vselect_model_values == 0, (
            f"Found {vselect_model_values} update_modelValue on VSelects — "
            "should be 0 to prevent double-fire with @state.change"
        )


# ── BUG-UI-SESSIONS-003: source_type derivation ──────


class TestBugSessionsSourceType:
    """BUG-UI-SESSIONS-003: source_type must be derived for every session
    based on session_id patterns and cc_session_uuid field."""

    @patch(f"{_MOD}.has_plotly", return_value=False)
    @patch(f"{_MOD}.compute_timeline_data", return_value=([], []))
    @patch(f"{_MOD}.compute_session_duration", return_value="<1m")
    @patch(f"{_MOD}.compute_session_metrics",
           return_value={"duration": "0h", "avg_tasks": 0})
    @patch(f"{_MOD}.format_timestamps_in_list", side_effect=lambda items, _: items)
    @patch("httpx.Client")
    def test_source_type_cc_from_uuid(
        self, MockClient, mock_fmt, mock_metrics, mock_dur, mock_tl, mock_plotly
    ):
        """Sessions with cc_session_uuid should get source_type='CC'."""
        items = [{"session_id": "SESSION-2026-02-14-ABC123",
                  "cc_session_uuid": "uuid-123", "agent_id": "a1",
                  "start_time": "", "end_time": ""}]
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, {"items": items})
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, _, loader = _setup()
        loader()
        assert items[0]["source_type"] == "CC"

    @patch(f"{_MOD}.has_plotly", return_value=False)
    @patch(f"{_MOD}.compute_timeline_data", return_value=([], []))
    @patch(f"{_MOD}.compute_session_duration", return_value="<1m")
    @patch(f"{_MOD}.compute_session_metrics",
           return_value={"duration": "0h", "avg_tasks": 0})
    @patch(f"{_MOD}.format_timestamps_in_list", side_effect=lambda items, _: items)
    @patch("httpx.Client")
    def test_source_type_cc_from_id_pattern(
        self, MockClient, mock_fmt, mock_metrics, mock_dur, mock_tl, mock_plotly
    ):
        """Sessions with -CC- in ID should get source_type='CC'."""
        items = [{"session_id": "SESSION-2026-02-14-CC-IMPORT",
                  "agent_id": "a1", "start_time": "", "end_time": ""}]
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, {"items": items})
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, _, loader = _setup()
        loader()
        assert items[0]["source_type"] == "CC"

    @patch(f"{_MOD}.has_plotly", return_value=False)
    @patch(f"{_MOD}.compute_timeline_data", return_value=([], []))
    @patch(f"{_MOD}.compute_session_duration", return_value="<1m")
    @patch(f"{_MOD}.compute_session_metrics",
           return_value={"duration": "0h", "avg_tasks": 0})
    @patch(f"{_MOD}.format_timestamps_in_list", side_effect=lambda items, _: items)
    @patch("httpx.Client")
    def test_source_type_chat(
        self, MockClient, mock_fmt, mock_metrics, mock_dur, mock_tl, mock_plotly
    ):
        """Sessions with -CHAT- in ID should get source_type='Chat'."""
        items = [{"session_id": "SESSION-2026-02-14-CHAT-TEST",
                  "agent_id": "a1", "start_time": "", "end_time": ""}]
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, {"items": items})
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, _, loader = _setup()
        loader()
        assert items[0]["source_type"] == "Chat"

    @patch(f"{_MOD}.has_plotly", return_value=False)
    @patch(f"{_MOD}.compute_timeline_data", return_value=([], []))
    @patch(f"{_MOD}.compute_session_duration", return_value="<1m")
    @patch(f"{_MOD}.compute_session_metrics",
           return_value={"duration": "0h", "avg_tasks": 0})
    @patch(f"{_MOD}.format_timestamps_in_list", side_effect=lambda items, _: items)
    @patch("httpx.Client")
    def test_source_type_mcp_auto(
        self, MockClient, mock_fmt, mock_metrics, mock_dur, mock_tl, mock_plotly
    ):
        """Sessions with -MCP-AUTO- in ID should get source_type='Chat'."""
        items = [{"session_id": "SESSION-2026-02-14-MCP-AUTO-ABC",
                  "agent_id": "a1", "start_time": "", "end_time": ""}]
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, {"items": items})
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, _, loader = _setup()
        loader()
        assert items[0]["source_type"] == "Chat"

    @patch(f"{_MOD}.has_plotly", return_value=False)
    @patch(f"{_MOD}.compute_timeline_data", return_value=([], []))
    @patch(f"{_MOD}.compute_session_duration", return_value="<1m")
    @patch(f"{_MOD}.compute_session_metrics",
           return_value={"duration": "0h", "avg_tasks": 0})
    @patch(f"{_MOD}.format_timestamps_in_list", side_effect=lambda items, _: items)
    @patch("httpx.Client")
    def test_source_type_api_default(
        self, MockClient, mock_fmt, mock_metrics, mock_dur, mock_tl, mock_plotly
    ):
        """Sessions without CC or Chat patterns should get source_type='API'."""
        items = [{"session_id": "SESSION-2026-02-14-ABC123",
                  "agent_id": "a1", "start_time": "", "end_time": ""}]
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, {"items": items})
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, _, loader = _setup()
        loader()
        assert items[0]["source_type"] == "API"

    @patch(f"{_MOD}.has_plotly", return_value=False)
    @patch(f"{_MOD}.compute_timeline_data", return_value=([], []))
    @patch(f"{_MOD}.compute_session_duration", return_value="<1m")
    @patch(f"{_MOD}.compute_session_metrics",
           return_value={"duration": "0h", "avg_tasks": 0})
    @patch(f"{_MOD}.format_timestamps_in_list", side_effect=lambda items, _: items)
    @patch("httpx.Client")
    def test_preserves_existing_source_type(
        self, MockClient, mock_fmt, mock_metrics, mock_dur, mock_tl, mock_plotly
    ):
        """Sessions that already have source_type should not be overwritten."""
        items = [{"session_id": "SESSION-2026-02-14-CHAT-TEST",
                  "source_type": "Custom", "agent_id": "a1",
                  "start_time": "", "end_time": ""}]
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, {"items": items})
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, _, loader = _setup()
        loader()
        assert items[0]["source_type"] == "Custom"


# ── BUG-API-PROJECTS-001: Deduplicate project IDs ────


class TestBugProjectsDedup:
    """BUG-API-PROJECTS-001: list_projects must deduplicate project IDs
    when TypeDB returns multiple entities with the same project-id."""

    def test_list_projects_deduplicates_ids(self):
        """3 identical project-id rows should yield 1 unique project."""
        from governance.typedb.queries.projects.crud import ProjectCRUDOperations

        crud = ProjectCRUDOperations.__new__(ProjectCRUDOperations)
        # Mock the _execute_query to return 3 identical IDs
        crud._execute_query = MagicMock(return_value=[
            {"id": "PROJ-A"},
            {"id": "PROJ-A"},
            {"id": "PROJ-A"},
        ])
        # Mock get_project to return a project dict
        crud.get_project = MagicMock(return_value={
            "project_id": "PROJ-A", "name": "Project A",
            "path": "/tmp", "plan_count": 0, "session_count": 5,
        })

        result = crud.list_projects()

        assert len(result) == 1
        assert result[0]["project_id"] == "PROJ-A"
        # get_project should be called only once (deduplicated)
        crud.get_project.assert_called_once_with("PROJ-A")

    def test_list_projects_multiple_unique_ids(self):
        """Multiple unique project IDs should all be returned."""
        from governance.typedb.queries.projects.crud import ProjectCRUDOperations

        crud = ProjectCRUDOperations.__new__(ProjectCRUDOperations)
        crud._execute_query = MagicMock(return_value=[
            {"id": "PROJ-A"},
            {"id": "PROJ-B"},
            {"id": "PROJ-A"},  # duplicate
            {"id": "PROJ-C"},
            {"id": "PROJ-B"},  # duplicate
        ])
        crud.get_project = MagicMock(side_effect=lambda pid: {
            "project_id": pid, "name": f"Project {pid[-1]}",
        })

        result = crud.list_projects()

        assert len(result) == 3
        ids = [p["project_id"] for p in result]
        assert sorted(ids) == ["PROJ-A", "PROJ-B", "PROJ-C"]

    def test_list_projects_respects_pagination(self):
        """Pagination should work on deduplicated IDs."""
        from governance.typedb.queries.projects.crud import ProjectCRUDOperations

        crud = ProjectCRUDOperations.__new__(ProjectCRUDOperations)
        crud._execute_query = MagicMock(return_value=[
            {"id": "PROJ-A"}, {"id": "PROJ-A"},
            {"id": "PROJ-B"}, {"id": "PROJ-B"},
            {"id": "PROJ-C"}, {"id": "PROJ-C"},
        ])
        crud.get_project = MagicMock(side_effect=lambda pid: {
            "project_id": pid, "name": f"Project {pid[-1]}",
        })

        # offset=1, limit=1 should return only PROJ-B (sorted: A, B, C)
        result = crud.list_projects(offset=1, limit=1)

        assert len(result) == 1
        assert result[0]["project_id"] == "PROJ-B"

    def test_list_projects_empty_results(self):
        """Empty results should return empty list."""
        from governance.typedb.queries.projects.crud import ProjectCRUDOperations

        crud = ProjectCRUDOperations.__new__(ProjectCRUDOperations)
        crud._execute_query = MagicMock(return_value=[])

        result = crud.list_projects()
        assert result == []

    def test_list_projects_exception_returns_empty(self):
        """Query exceptions should return empty list."""
        from governance.typedb.queries.projects.crud import ProjectCRUDOperations

        crud = ProjectCRUDOperations.__new__(ProjectCRUDOperations)
        crud._execute_query = MagicMock(side_effect=Exception("db error"))

        result = crud.list_projects()
        assert result == []


# ── Source type in refresh controllers ────────────────


class TestRefreshSourceType:
    """Verify source_type derivation in data_loaders_refresh.py."""

    @patch("agent.governance_ui.controllers.data_loaders_refresh.compute_timeline_data",
           return_value=([], []))
    @patch("agent.governance_ui.controllers.data_loaders_refresh.compute_session_duration",
           return_value="<1m")
    @patch("agent.governance_ui.controllers.data_loaders_refresh.compute_session_metrics",
           return_value={"duration": "0h", "avg_tasks": 0})
    @patch("agent.governance_ui.controllers.data_loaders_refresh.format_timestamps_in_list",
           side_effect=lambda items, _: items)
    @patch("agent.governance_ui.controllers.data_loaders_refresh.add_error_trace")
    @patch("httpx.Client")
    def test_load_sessions_list_adds_source_type(
        self, MockClient, mock_err_trace, mock_fmt,
        mock_metrics, mock_dur, mock_tl
    ):
        """load_sessions_list should derive source_type for each item."""
        items = [
            {"session_id": "SESSION-2026-02-14-CHAT-X", "start_time": "", "end_time": ""},
            {"session_id": "SESSION-2026-02-14-ABCD", "start_time": "", "end_time": ""},
        ]
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, {"items": items})
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state = MagicMock()
        state.sessions = []
        ctrl = MagicMock()
        triggers = {}
        ctrl.trigger = lambda name: (lambda fn: triggers.update({name: fn}) or fn)

        from agent.governance_ui.controllers.data_loaders_refresh import (
            register_refresh_controllers,
        )
        result = register_refresh_controllers(state, ctrl, "http://localhost:8082", {})
        result["load_sessions_list"]()

        assert items[0]["source_type"] == "Chat"
        assert items[1]["source_type"] == "API"
