"""
Unit tests for Tab Deep Scan Batch 15 — Pagination edge cases + double-click guards.

Covers: pagination display formula, double-click protection on destructive actions,
empty state pagination display, loading guard consistency.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import MagicMock, patch


# ── Double-click guard on destructive actions (BUG-UI-DOUBLECLICK-001) ────


class TestDoubleClickGuardTasks:
    """Tasks controllers must guard against double-click race conditions."""

    def test_delete_task_has_loading_guard(self):
        """delete_task must return early if is_loading is True."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "BUG-UI-DOUBLECLICK-001" in source

    @patch("agent.governance_ui.controllers.tasks.httpx")
    @patch("agent.governance_ui.controllers.tasks.add_error_trace")
    def test_delete_task_skips_when_loading(self, mock_err, mock_httpx):
        """delete_task must not call API when is_loading is True."""
        state = MagicMock()
        state.selected_task = {"task_id": "T1"}
        state.is_loading = True
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, "http://localhost:8082")
        triggers["delete_task"]()
        mock_httpx.Client.assert_not_called()

    @patch("agent.governance_ui.controllers.tasks.httpx")
    @patch("agent.governance_ui.controllers.tasks.add_error_trace")
    def test_submit_task_edit_skips_when_loading(self, mock_err, mock_httpx):
        """submit_task_edit must not call API when is_loading is True."""
        state = MagicMock()
        state.selected_task = {"task_id": "T1"}
        state.is_loading = True
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, "http://localhost:8082")
        triggers["submit_task_edit"]()
        mock_httpx.Client.assert_not_called()

    @patch("agent.governance_ui.controllers.tasks.httpx")
    @patch("agent.governance_ui.controllers.tasks.add_error_trace")
    def test_create_task_skips_when_loading(self, mock_err, mock_httpx):
        """create_task must not call API when is_loading is True."""
        state = MagicMock()
        state.is_loading = True
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, "http://localhost:8082")
        triggers["create_task"]()
        mock_httpx.Client.assert_not_called()


class TestDoubleClickGuardDecisions:
    """Decisions controllers must guard against double-click."""

    def test_submit_decision_has_loading_guard(self):
        from agent.governance_ui.controllers import decisions
        source = inspect.getsource(decisions)
        assert "BUG-UI-DOUBLECLICK-001" in source

    @patch("agent.governance_ui.controllers.decisions.httpx")
    @patch("agent.governance_ui.controllers.decisions.add_error_trace")
    def test_submit_decision_skips_when_loading(self, mock_err, mock_httpx):
        state = MagicMock()
        state.is_loading = True
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.decisions import register_decisions_controllers
        register_decisions_controllers(state, ctrl, "http://localhost:8082")
        triggers["submit_decision_form"]()
        mock_httpx.Client.assert_not_called()

    @patch("agent.governance_ui.controllers.decisions.httpx")
    @patch("agent.governance_ui.controllers.decisions.add_error_trace")
    def test_delete_decision_skips_when_loading(self, mock_err, mock_httpx):
        state = MagicMock()
        state.selected_decision = {"id": "D1"}
        state.is_loading = True
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.decisions import register_decisions_controllers
        register_decisions_controllers(state, ctrl, "http://localhost:8082")
        triggers["delete_decision"]()
        mock_httpx.Client.assert_not_called()


class TestDoubleClickGuardSessions:
    """Sessions controllers must guard against double-click."""

    def test_session_controllers_have_loading_guard(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "BUG-UI-DOUBLECLICK-001" in source

    @patch("agent.governance_ui.controllers.sessions.httpx")
    @patch("agent.governance_ui.controllers.sessions.register_session_detail_loaders")
    @patch("agent.governance_ui.controllers.sessions.register_sessions_pagination")
    @patch("agent.governance_ui.controllers.sessions.log_action")
    def test_delete_session_skips_when_loading(self, mock_log, mock_pag, mock_loaders, mock_httpx):
        mock_loaders.return_value = {
            "load_evidence": MagicMock(), "load_tasks": MagicMock(),
            "load_tool_calls": MagicMock(), "load_thinking_items": MagicMock(),
            "build_timeline": MagicMock(), "load_evidence_rendered": MagicMock(),
            "load_transcript": MagicMock(),
        }
        mock_pag.return_value = MagicMock()

        state = MagicMock()
        state.selected_session = {"session_id": "S1"}
        state.is_loading = True
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.sessions import register_sessions_controllers
        register_sessions_controllers(state, ctrl, "http://localhost:8082")
        triggers["delete_session"]()
        mock_httpx.Client.assert_not_called()

    @patch("agent.governance_ui.controllers.sessions.httpx")
    @patch("agent.governance_ui.controllers.sessions.register_session_detail_loaders")
    @patch("agent.governance_ui.controllers.sessions.register_sessions_pagination")
    @patch("agent.governance_ui.controllers.sessions.log_action")
    def test_submit_session_skips_when_loading(self, mock_log, mock_pag, mock_loaders, mock_httpx):
        mock_loaders.return_value = {
            "load_evidence": MagicMock(), "load_tasks": MagicMock(),
            "load_tool_calls": MagicMock(), "load_thinking_items": MagicMock(),
            "build_timeline": MagicMock(), "load_evidence_rendered": MagicMock(),
            "load_transcript": MagicMock(),
        }
        mock_pag.return_value = MagicMock()

        state = MagicMock()
        state.is_loading = True
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.sessions import register_sessions_controllers
        register_sessions_controllers(state, ctrl, "http://localhost:8082")
        triggers["submit_session_form"]()
        mock_httpx.Client.assert_not_called()


class TestDoubleClickGuardRules:
    """Rules controllers must guard against double-click."""

    def test_rules_have_loading_guard(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        assert "BUG-UI-DOUBLECLICK-001" in source

    @patch("agent.governance_ui.controllers.rules.httpx")
    @patch("agent.governance_ui.controllers.rules.add_error_trace")
    def test_delete_rule_skips_when_loading(self, mock_err, mock_httpx):
        state = MagicMock()
        state.selected_rule = {"rule_id": "R1"}
        state.is_loading = True
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.rules import register_rules_controllers
        register_rules_controllers(state, ctrl, "http://localhost:8082")
        triggers["delete_rule"]()
        mock_httpx.Client.assert_not_called()


# ── Pagination display formula (BUG-UI-PAGINATION-002) ────────────────


class TestPaginationDisplay:
    """Pagination must show 'Page 1 of 1' when total=0, not 'Page 1 of 0'."""

    def test_tasks_pagination_uses_math_max(self):
        """Tasks page info must use Math.max(1, ...) like sessions does."""
        from agent.governance_ui.views.tasks import list as tasks_list
        source = inspect.getsource(tasks_list)
        assert "Math.max(1, Math.ceil(tasks_pagination.total / tasks_per_page))" in source

    def test_sessions_pagination_uses_math_max(self):
        """Sessions page info must use Math.max(1, ...) for empty state."""
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert "Math.max(1, Math.ceil(sessions_pagination.total / sessions_per_page))" in source


# ── Pagination state initialization ───────────────────────────────────


class TestPaginationStateInit:
    """All pagination state vars must be properly initialized."""

    def test_tasks_pagination_init(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        pag = state["tasks_pagination"]
        assert pag["total"] == 0
        assert pag["offset"] == 0
        assert pag["has_more"] is False

    def test_sessions_pagination_init(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        pag = state["sessions_pagination"]
        assert pag["total"] == 0
        assert pag["offset"] == 0
        assert pag["has_more"] is False

    def test_tasks_page_starts_at_one(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["tasks_page"] == 1

    def test_sessions_page_starts_at_one(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["sessions_page"] == 1


# ── Empty list metric safety ──────────────────────────────────────────


class TestEmptyListMetricSafety:
    """Metric computations must handle empty lists without errors."""

    def test_compute_session_metrics_empty(self):
        from agent.governance_ui.utils import compute_session_metrics
        result = compute_session_metrics([])
        assert result["duration"] == "0h"
        assert result["avg_tasks"] == 0

    def test_compute_session_duration_empty_strings(self):
        from agent.governance_ui.utils import compute_session_duration
        result = compute_session_duration("", "")
        assert result is not None  # Should not crash

    def test_compute_timeline_data_empty(self):
        from agent.governance_ui.utils import compute_timeline_data
        vals, labels = compute_timeline_data([])
        # Returns 14-day zero-filled arrays (last 14 days)
        assert len(vals) == 14
        assert all(v == 0 for v in vals)
        assert len(labels) == 14

    def test_format_timestamps_empty(self):
        from agent.governance_ui.utils import format_timestamps_in_list
        result = format_timestamps_in_list([], ["start_time"])
        assert result == []
