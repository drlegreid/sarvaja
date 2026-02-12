"""
Unit tests for Initial State Factory.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/state/initial.py module.
Tests: get_initial_state — verifies all key state sections are present
       and default values are correct.
"""

from unittest.mock import patch

import pytest


_P = "agent.governance_ui.state.initial"


@pytest.fixture(autouse=True)
def _mock_deps():
    with patch(f"{_P}.get_initial_loader_states", return_value={"loader_rules": False}), \
         patch(f"{_P}.get_initial_trace_state", return_value={"trace_visible": False}), \
         patch(f"{_P}.get_metrics_initial_state", return_value={"metrics_data": {}}):
        yield


# ── Theme ────────────────────────────────────────────────────────


class TestThemeState:
    def test_dark_mode_default(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["dark_mode"] is False


# ── Navigation ───────────────────────────────────────────────────


class TestNavigationState:
    def test_active_view_default(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["active_view"] == "rules"


# ── Data lists ───────────────────────────────────────────────────


class TestDataLists:
    def test_empty_by_default(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["rules"] == []
        assert state["decisions"] == []
        assert state["sessions"] == []
        assert state["tasks"] == []


# ── Selection state ──────────────────────────────────────────────


class TestSelectionState:
    def test_nothing_selected(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["selected_rule"] is None
        assert state["selected_session"] is None
        assert state["selected_decision"] is None
        assert state["show_session_detail"] is False


# ── Form states ──────────────────────────────────────────────────


class TestFormStates:
    def test_rule_form(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["show_rule_form"] is False
        assert state["rule_form_mode"] == "create"
        assert state["form_rule_category"] == "governance"

    def test_decision_form(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["show_decision_form"] is False
        assert state["form_decision_status"] == "PENDING"

    def test_session_form(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["show_session_form"] is False
        assert state["form_session_status"] == "ACTIVE"

    def test_task_form(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["show_task_form"] is False
        assert state["form_task_phase"] == "P10"


# ── Filter states ────────────────────────────────────────────────


class TestFilterStates:
    def test_rules_filters(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["rules_status_filter"] is None
        assert state["rules_category_filter"] is None
        assert state["rules_search_query"] == ""
        assert state["rules_sort_asc"] is True

    def test_sessions_filters(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["sessions_search_query"] == ""
        assert state["sessions_filter_status"] is None
        assert state["sessions_view_mode"] == "table"

    def test_tasks_filters(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["tasks_search_query"] == ""
        assert state["tasks_status_filter"] is None
        assert state["tasks_phase_filter"] is None


# ── Pagination ───────────────────────────────────────────────────


class TestPaginationState:
    def test_tasks_pagination(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["tasks_page"] == 1
        assert state["tasks_per_page"] == 20
        assert state["tasks_pagination"]["total"] == 0

    def test_sessions_pagination(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["sessions_page"] == 1
        assert state["sessions_pagination"]["has_more"] is False


# ── Agent / Chat ─────────────────────────────────────────────────


class TestAgentChatState:
    def test_agents_empty(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["agents"] == []
        assert state["show_agent_detail"] is False

    def test_chat_default(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["chat_messages"] == []
        assert state["chat_loading"] is False
        assert state["chat_session_id"] is None


# ── Infra / Monitor ──────────────────────────────────────────────


class TestInfraState:
    def test_infra_defaults(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["infra_loading"] is False
        assert state["infra_log_container"] == "dashboard"
        assert state["infra_stats"]["status"] == "unknown"


# ── Projects state (GOV-PROJECT-01-v1) ──────────────────────────


class TestProjectsState:
    def test_projects_empty_by_default(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["projects"] == []

    def test_selected_project_none(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["selected_project"] is None

    def test_project_sessions_empty(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["project_sessions"] == []

    def test_projects_headers_shape(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        headers = state["projects_headers"]
        assert len(headers) == 5
        keys = [h["key"] for h in headers]
        assert "project_id" in keys
        assert "name" in keys
        assert "session_count" in keys


# ── Factory freshness ────────────────────────────────────────────


class TestFactoryFreshness:
    def test_returns_new_dict_each_call(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state1 = get_initial_state()
        state2 = get_initial_state()
        assert state1 is not state2
        state1["dark_mode"] = True
        assert state2["dark_mode"] is False

    def test_includes_loader_states(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "loader_rules" in state

    def test_includes_trace_states(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "trace_visible" in state

    def test_includes_metrics_states(self, _mock_deps):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "metrics_data" in state
