"""
Unit tests for Tab Deep Scan Batch 8 fixes.

Covers: Duplicate trigger resolution (claim_selected_task, complete_selected_task,
load_monitor_data), agent registration state vars, trigger-view alignment.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import MagicMock, patch

from agent.governance_ui.state.initial import get_initial_state


# ── Duplicate trigger resolution: claim/complete ─────────────────


class TestTaskDetailTriggerRename:
    """Task detail claim/complete triggers renamed to avoid backlog collision."""

    def _make_state_ctrl(self, api_base="http://localhost:8082"):
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def _trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = _trigger
        ctrl.set = _trigger

        state.tasks = []
        state.tasks_page = 1
        state.tasks_per_page = 20
        state.tasks_pagination = {}

        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, api_base)
        return state, ctrl, triggers

    def test_claim_selected_task_registered(self):
        """Tasks controller registers claim_selected_task (not claim_task)."""
        _, _, triggers = self._make_state_ctrl()
        assert "claim_selected_task" in triggers
        assert "claim_task" not in triggers

    def test_complete_selected_task_registered(self):
        """Tasks controller registers complete_selected_task (not complete_task)."""
        _, _, triggers = self._make_state_ctrl()
        assert "complete_selected_task" in triggers
        assert "complete_task" not in triggers

    def test_view_uses_claim_selected_task(self):
        """Task detail view should reference claim_selected_task trigger."""
        from agent.governance_ui.views.tasks import detail
        source = inspect.getsource(detail)
        assert "claim_selected_task" in source
        assert "trigger('claim_task')" not in source

    def test_view_uses_complete_selected_task(self):
        """Task detail view should reference complete_selected_task trigger."""
        from agent.governance_ui.views.tasks import detail
        source = inspect.getsource(detail)
        assert "complete_selected_task" in source
        assert "trigger('complete_task')" not in source


class TestBacklogTriggerUnchanged:
    """Backlog claim_task and complete_task triggers are unchanged."""

    def _make_backlog(self):
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def _trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = _trigger
        load_fn = MagicMock()

        from agent.governance_ui.controllers.backlog import register_backlog_controllers
        register_backlog_controllers(state, ctrl, "http://localhost:8082", load_fn)
        return state, ctrl, triggers

    def test_backlog_still_has_claim_task(self):
        """Backlog controller still registers claim_task trigger."""
        _, _, triggers = self._make_backlog()
        assert "claim_task" in triggers

    def test_backlog_still_has_complete_task(self):
        """Backlog controller still registers complete_task trigger."""
        _, _, triggers = self._make_backlog()
        assert "complete_task" in triggers

    def test_backlog_has_compat_aliases(self):
        """Backlog controller registers backward compat aliases."""
        _, _, triggers = self._make_backlog()
        assert "claim_backlog_task" in triggers
        assert "complete_backlog_task" in triggers


# ── Duplicate trigger resolution: load_monitor_data ──────────────


class TestLoadMonitorDataTrigger:
    """load_monitor_data should be registered by monitor.py only."""

    def test_data_loaders_no_monitor_trigger(self):
        """data_loaders.py should NOT register load_monitor_data trigger."""
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        # Should have a comment explaining the delegation, not a trigger
        assert '@ctrl.trigger("load_monitor_data")' not in source

    def test_monitor_has_trigger(self):
        """monitor.py should register load_monitor_data trigger."""
        from agent.governance_ui.controllers import monitor
        source = inspect.getsource(monitor)
        assert "load_monitor_data" in source

    def test_monitor_has_error_handling(self):
        """monitor load_monitor_data should have error handling."""
        from agent.governance_ui.controllers import monitor
        source = inspect.getsource(monitor)
        assert "except Exception" in source

    def test_monitor_uses_filter(self):
        """monitor load_monitor_data should use monitor_filter."""
        from agent.governance_ui.controllers import monitor
        source = inspect.getsource(monitor)
        assert "monitor_filter" in source


# ── Agent registration state vars ────────────────────────────────


class TestAgentRegistrationStateVars:
    """reg_agent_* vars must be in initial state for v_model binding."""

    def test_reg_agent_name(self):
        state = get_initial_state()
        assert "reg_agent_name" in state
        assert state["reg_agent_name"] == ""

    def test_reg_agent_id(self):
        state = get_initial_state()
        assert "reg_agent_id" in state
        assert state["reg_agent_id"] == ""

    def test_reg_agent_type(self):
        state = get_initial_state()
        assert "reg_agent_type" in state
        assert state["reg_agent_type"] == ""

    def test_reg_agent_model(self):
        state = get_initial_state()
        assert "reg_agent_model" in state
        assert state["reg_agent_model"] == ""

    def test_reg_agent_rules(self):
        state = get_initial_state()
        assert "reg_agent_rules" in state
        assert state["reg_agent_rules"] == []

    def test_reg_agent_instructions(self):
        state = get_initial_state()
        assert "reg_agent_instructions" in state
        assert state["reg_agent_instructions"] == ""

    def test_reg_agent_loading(self):
        state = get_initial_state()
        assert "reg_agent_loading" in state
        assert state["reg_agent_loading"] is False


# ── All v_model bindings have matching state vars (regression) ────


class TestVModelStateCompleteness:
    """Spot-check critical v_model bindings exist in state."""

    def test_trace_filter_in_state(self):
        """trace_filter is in initial state (via trace_store)."""
        state = get_initial_state()
        assert "trace_filter" in state

    def test_metrics_search_query_in_state(self):
        """metrics_search_query is in initial state (via metrics module)."""
        state = get_initial_state()
        assert "metrics_search_query" in state

    def test_metrics_active_tab_in_state(self):
        """metrics_active_tab is in initial state (via metrics module)."""
        state = get_initial_state()
        assert "metrics_active_tab" in state

    def test_executive_expanded_sections_in_state(self):
        """executive_expanded_sections must be in state."""
        state = get_initial_state()
        assert "executive_expanded_sections" in state

    def test_form_decision_options_in_state(self):
        """form_decision_options must be in state."""
        state = get_initial_state()
        assert "form_decision_options" in state

    def test_show_agent_registration_in_state(self):
        """show_agent_registration must be in state."""
        state = get_initial_state()
        assert "show_agent_registration" in state
