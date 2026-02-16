"""Tests for UI tab deep scan fixes (2026-02-15 cycle).

Bug fixes across Audit, Monitor, Projects, and Tests tabs:
- BUG-AUDIT-URL-001: Audit loader used os.getenv instead of api_base_url
- BUG-AUDIT-NAV-001: navigate_to_entity for sessions didn't load detail data
- BUG-MONITOR-STATE-001: Missing monitor_headers and monitor_event_type_filter
- BUG-PROJECT-BACK-001: Back button didn't clear project_sessions
- BUG-PROJECT-TRACE-001: Missing API trace for sessions endpoint
- BUG-TESTS-POLL-001: Polling timeout mismatch (60s vs 300s runner timeout)
- BUG-TESTS-ROBOT-001: Robot summary missing error trace
"""

from unittest.mock import patch, MagicMock, PropertyMock
import pytest


# ---- Audit Tab Tests ----

class TestAuditLoaderUrl:
    """BUG-AUDIT-URL-001: Audit loader should use api_base_url parameter."""

    def test_load_audit_trail_uses_api_base_url(self):
        """Audit loader must use api_base_url param, not os.getenv."""
        import inspect
        from agent.governance_ui.controllers.audit_loaders import (
            register_audit_loader_controllers,
        )
        source = inspect.getsource(register_audit_loader_controllers)
        # Should NOT reference os.getenv for the API URL
        assert "os.getenv" not in source, (
            "audit_loaders still uses os.getenv — should use api_base_url"
        )

    def test_load_audit_trail_calls_correct_url(self):
        """Audit trail loader should call api_base_url/api/audit/summary."""
        from agent.governance_ui.controllers.audit_loaders import (
            register_audit_loader_controllers,
        )

        state = MagicMock()
        ctrl = MagicMock()
        state.audit_filter_entity_type = None
        state.audit_filter_action_type = None
        state.audit_filter_entity_id = None
        state.audit_filter_correlation_id = None
        state.active_view = "audit"

        api_url = "http://test-host:9999"
        result = register_audit_loader_controllers(state, ctrl, api_url)

        with patch("agent.governance_ui.controllers.audit_loaders.httpx") as mock_httpx:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"total_entries": 5}
            mock_httpx.get.return_value = mock_resp

            result["load_audit_trail"]()

            calls = [str(c) for c in mock_httpx.get.call_args_list]
            assert any("test-host:9999" in c for c in calls), (
                f"Expected api_base_url in calls, got: {calls}"
            )
            assert not any("localhost:8082" in c for c in calls), (
                "Should NOT fall back to localhost:8082"
            )


class TestAuditNavigateToSession:
    """BUG-AUDIT-NAV-001: navigate_to_entity should use ctrl.select_session."""

    def test_navigate_to_session_calls_select_session(self):
        """Navigating to a session should trigger select_session controller."""
        state = MagicMock()
        ctrl = MagicMock()
        state.sessions = [{"session_id": "SESSION-TEST-123"}]
        state.active_view = "audit"

        from agent.governance_ui.controllers.audit_loaders import (
            register_audit_loader_controllers,
        )
        register_audit_loader_controllers(state, ctrl, "http://localhost:8082")

        # Find the navigate_to_entity trigger
        trigger_calls = [c for c in ctrl.trigger.call_args_list]
        navigate_fn = None
        for call in trigger_calls:
            if call[0][0] == "navigate_to_entity":
                navigate_fn = call
                break

        # The navigate_to_entity is registered via @ctrl.trigger decorator
        # We need to call it through the decorator pattern
        # Instead, verify the source code uses ctrl.select_session
        import inspect
        source = inspect.getsource(register_audit_loader_controllers)
        assert "ctrl.select_session" in source, (
            "navigate_to_entity should call ctrl.select_session for sessions"
        )

    def test_navigate_to_rule_still_works(self):
        """Rule navigation should still use local state lookup."""
        import inspect
        from agent.governance_ui.controllers.audit_loaders import (
            register_audit_loader_controllers,
        )
        source = inspect.getsource(register_audit_loader_controllers)
        # Rules should still use the local state pattern
        assert 'entity_type_lower == "rule"' in source
        assert "state.selected_rule = rule" in source


# ---- Monitor Tab Tests ----

class TestMonitorStateInit:
    """BUG-MONITOR-STATE-001: Monitor state vars must be initialized."""

    def test_monitor_headers_initialized(self):
        """monitor_headers should be in initial state."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "monitor_headers" in state, "monitor_headers missing from initial state"
        assert isinstance(state["monitor_headers"], list)
        assert len(state["monitor_headers"]) > 0

    def test_monitor_event_type_filter_initialized(self):
        """monitor_event_type_filter should be in initial state."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "monitor_event_type_filter" in state
        assert state["monitor_event_type_filter"] == ""

    def test_monitor_headers_match_view_columns(self):
        """State headers should match the view's expected columns."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        headers = state["monitor_headers"]
        keys = [h["key"] for h in headers]
        # These are the columns used in monitor_view.py VDataTable
        assert "event_type" in keys
        assert "source" in keys
        assert "severity" in keys
        assert "timestamp" in keys
        assert "rule_id" in keys


# ---- Projects Tab Tests ----

class TestProjectBackButton:
    """BUG-PROJECT-BACK-001: Back button should clear project_sessions."""

    def test_back_button_clears_project_sessions(self):
        """Project detail back button should reset project_sessions state."""
        import inspect
        from agent.governance_ui.views.projects.list import _build_project_detail
        source = inspect.getsource(_build_project_detail)
        assert "project_sessions = []" in source, (
            "Back button should clear project_sessions on navigation"
        )

    def test_back_button_clears_selected_project(self):
        """Project detail back button should nullify selected_project."""
        import inspect
        from agent.governance_ui.views.projects.list import _build_project_detail
        source = inspect.getsource(_build_project_detail)
        assert "selected_project = null" in source


class TestProjectSessionsTrace:
    """BUG-PROJECT-TRACE-001: Sessions endpoint should have API trace."""

    def test_sessions_endpoint_traced(self):
        """select_project should trace the sessions API call."""
        import inspect
        from agent.governance_ui.controllers.projects import (
            register_project_controllers,
        )
        source = inspect.getsource(register_project_controllers)
        # Should trace the sessions endpoint
        assert "api/projects/" in source
        assert "sessions" in source
        assert "add_api_trace" in source
        # Count add_api_trace calls — should be at least 2 (project + sessions)
        assert source.count("add_api_trace") >= 2, (
            "Should trace both project GET and sessions GET"
        )


# ---- Tests Tab Tests ----

class TestPollingTimeout:
    """BUG-TESTS-POLL-001: Polling timeout should match runner timeout."""

    def test_poll_for_results_timeout_matches_runner(self):
        """poll_for_results should poll for at least 5 minutes (300s)."""
        import inspect
        from agent.governance_ui.controllers.tests import (
            register_tests_controllers,
        )
        source = inspect.getsource(register_tests_controllers)
        # Find max_polls in poll_for_results (not poll_for_regression)
        # The value × 2 seconds should be >= 300
        assert "max_polls = 150" in source, (
            "poll_for_results should use 150 polls (5 min at 2s interval)"
        )

    def test_regression_polling_has_longer_timeout(self):
        """Regression polling should have at least 3 min timeout."""
        import inspect
        from agent.governance_ui.controllers.tests import (
            register_tests_controllers,
        )
        source = inspect.getsource(register_tests_controllers)
        assert "max_polls = 90" in source, (
            "poll_for_regression should use 90 polls (3 min)"
        )


class TestRobotSummaryTrace:
    """BUG-TESTS-ROBOT-001: Robot summary should have error trace."""

    def test_robot_summary_error_traced(self):
        """load_robot_summary should call add_error_trace on failure."""
        import inspect
        from agent.governance_ui.controllers.tests import (
            register_tests_controllers,
        )
        source = inspect.getsource(register_tests_controllers)
        # Find the robot summary section
        robot_idx = source.index("load_robot_summary")
        robot_section = source[robot_idx:robot_idx + 500]
        assert "add_error_trace" in robot_section, (
            "on_load_robot_summary should call add_error_trace on exception"
        )
        assert "robot/summary" in robot_section


# ---- Cross-Tab State Integrity ----

class TestStateIntegrity:
    """Verify all UI tabs have required state variables initialized."""

    def test_all_monitor_state_vars_present(self):
        """Monitor tab state variables should all be initialized."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        required = [
            "monitor_feed", "monitor_alerts", "monitor_stats",
            "monitor_filter", "monitor_event_type_filter",
            "monitor_headers", "auto_refresh", "top_rules",
            "hourly_stats", "monitor_last_updated",
        ]
        for var in required:
            assert var in state, f"Missing monitor state var: {var}"

    def test_all_audit_state_vars_present(self):
        """Audit tab state variables should all be initialized."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        required = [
            "audit_summary", "audit_entries", "audit_loading",
            "audit_filter_entity_type", "audit_filter_action_type",
            "audit_filter_entity_id", "audit_filter_correlation_id",
            "audit_entity_types", "audit_action_types",
        ]
        for var in required:
            assert var in state, f"Missing audit state var: {var}"

    def test_all_tests_state_vars_present(self):
        """Tests tab state variables should all be initialized."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        required = [
            "tests_loading", "tests_running", "tests_current_run",
            "tests_recent_runs", "tests_cvp_status",
            "tests_category_filter", "robot_summary",
        ]
        for var in required:
            assert var in state, f"Missing tests state var: {var}"

    def test_all_projects_state_vars_present(self):
        """Projects tab state variables should all be initialized."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        required = [
            "projects", "selected_project", "project_sessions",
            "projects_headers",
        ]
        for var in required:
            assert var in state, f"Missing projects state var: {var}"

    def test_no_import_os_in_audit_loaders(self):
        """audit_loaders.py should not import os (removed getenv usage)."""
        import inspect
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        # os import should be removed since we no longer use os.getenv
        assert "import os" not in source, (
            "audit_loaders should not import os — use api_base_url param"
        )
