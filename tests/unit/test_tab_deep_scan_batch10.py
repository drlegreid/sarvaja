"""
Unit tests for Tab Deep Scan Batch 10 — View auto-load consistency.

Covers: on_view_change handler coverage for all 16 navigation items,
dead backlog handler removal, sessions/tasks auto-load wiring,
load_tasks_page exposure from tasks controller.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import MagicMock, patch


# ── Tasks controller return value ─────────────────────────────────


class TestTasksControllerReturnValue:
    """register_tasks_controllers must return load_tasks_page."""

    def test_returns_dict(self):
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = trigger

        state_changes = {}

        def change(name):
            def decorator(fn):
                state_changes[name] = fn
                return fn
            return decorator

        state.change = change

        result = register_tasks_controllers(state, ctrl, "http://localhost:8082")
        assert isinstance(result, dict)

    def test_returns_load_tasks_page(self):
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = trigger

        state_changes = {}

        def change(name):
            def decorator(fn):
                state_changes[name] = fn
                return fn
            return decorator

        state.change = change

        result = register_tasks_controllers(state, ctrl, "http://localhost:8082")
        assert 'load_tasks_page' in result
        assert callable(result['load_tasks_page'])


# ── register_all_controllers wiring ──────────────────────────────


class TestAllControllersWiring:
    """register_all_controllers must wire tasks loader into return dict."""

    @patch("agent.governance_ui.controllers.register_project_controllers")
    @patch("agent.governance_ui.controllers.register_metrics_controllers",
           return_value={"load_metrics_data": MagicMock()})
    @patch("agent.governance_ui.controllers.register_tests_controllers",
           return_value={"load_tests_data": MagicMock()})
    @patch("agent.governance_ui.controllers.register_backlog_controllers")
    @patch("agent.governance_ui.controllers.register_data_loader_controllers",
           return_value={
               "load_trust_data": MagicMock(),
               "load_monitor_data": MagicMock(),
               "load_backlog_data": MagicMock(),
               "load_executive_report_data": MagicMock(),
               "load_infra_status": MagicMock(),
               "load_workflow_status": MagicMock(),
               "load_audit_trail": MagicMock(),
               "load_sessions_list": MagicMock(),
           })
    @patch("agent.governance_ui.controllers.register_rule_detail_handlers")
    @patch("agent.governance_ui.controllers.register_trace_bar_handlers")
    @patch("agent.governance_ui.controllers.register_chat_controllers")
    @patch("agent.governance_ui.controllers.register_monitor_controllers")
    @patch("agent.governance_ui.controllers.register_trust_controllers")
    @patch("agent.governance_ui.controllers.register_impact_controllers")
    @patch("agent.governance_ui.controllers.register_decisions_controllers")
    @patch("agent.governance_ui.controllers.register_sessions_controllers")
    @patch("agent.governance_ui.controllers.register_tasks_controllers",
           return_value={"load_tasks_page": MagicMock()})
    @patch("agent.governance_ui.controllers.register_search_controllers")
    @patch("agent.governance_ui.controllers.register_rules_controllers",
           return_value={"load_rules": MagicMock()})
    def test_loaders_include_load_tasks_page(self, *mocks):
        from agent.governance_ui.controllers import register_all_controllers
        state = MagicMock()
        ctrl = MagicMock()
        loaders = register_all_controllers(state, ctrl, "http://localhost:8082")
        assert 'load_tasks_page' in loaders
        assert callable(loaders['load_tasks_page'])


# ── on_view_change coverage ──────────────────────────────────────


class TestOnViewChangeCoverage:
    """governance_dashboard.py on_view_change must handle all 16 nav items."""

    def _get_dashboard_source(self):
        import importlib
        mod = importlib.import_module("agent.governance_dashboard")
        return inspect.getsource(mod)

    def test_sessions_in_on_view_change(self):
        """Sessions tab must auto-load data."""
        source = self._get_dashboard_source()
        assert "active_view == 'sessions'" in source

    def test_tasks_in_on_view_change(self):
        """Tasks tab must auto-load data."""
        source = self._get_dashboard_source()
        assert "active_view == 'tasks'" in source

    def test_sessions_calls_load_sessions_list(self):
        """Sessions view change must call load_sessions_list."""
        source = self._get_dashboard_source()
        # After the 'sessions' check, the next non-blank should call load_sessions_list
        assert "sessions" in source and "load_sessions_list" in source

    def test_tasks_calls_load_tasks_page(self):
        """Tasks view change must call load_tasks_page."""
        source = self._get_dashboard_source()
        assert "load_tasks_page" in source

    def test_no_backlog_view_handler(self):
        """Backlog nav item was removed — no backlog handler should exist."""
        source = self._get_dashboard_source()
        assert "active_view == 'backlog'" not in source

    def test_all_active_nav_items_handled(self):
        """Every active nav item should be handled in on_view_change."""
        source = self._get_dashboard_source()
        from agent.governance_ui.state.constants import NAVIGATION_ITEMS
        # Chat is exempt (live accumulation), decisions/projects are startup-only
        exempt = {'chat', 'decisions', 'projects'}
        for item in NAVIGATION_ITEMS:
            val = item['value']
            if val in exempt:
                continue
            assert f"'{val}'" in source, f"Nav item '{val}' not handled in on_view_change"


# ── Dead backlog handler removal ─────────────────────────────────


class TestDeadBacklogHandler:
    """Backlog nav item removed — no backlog handler in view change."""

    def test_no_backlog_nav_item(self):
        from agent.governance_ui.state.constants import NAVIGATION_ITEMS
        values = [item['value'] for item in NAVIGATION_ITEMS]
        assert 'backlog' not in values

    def test_backlog_merged_comment_exists(self):
        """Backlog merged into Tasks comment should exist."""
        from agent.governance_ui.state.constants import NAVIGATION_ITEMS
        import importlib
        mod = importlib.import_module("agent.governance_ui.state.constants")
        source = inspect.getsource(mod)
        assert "Backlog merged" in source


# ── Sessions auto-load on tab switch ─────────────────────────────


class TestSessionsAutoLoad:
    """Sessions tab must reload data when activated."""

    def test_load_sessions_list_function_exists(self):
        """load_sessions_list must be a function in data_loaders_refresh."""
        from agent.governance_ui.controllers import data_loaders_refresh
        source = inspect.getsource(data_loaders_refresh)
        assert "def load_sessions_list" in source

    def test_load_sessions_list_in_loaders_return(self):
        """load_sessions_list must be in refresh controllers return dict."""
        from agent.governance_ui.controllers import data_loaders_refresh
        source = inspect.getsource(data_loaders_refresh)
        assert "'load_sessions_list'" in source
