"""
Unit tests for Audit Trail Data Loader Controllers.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/controllers/audit_loaders.py.
Tests: register_audit_loader_controllers — load_audit_trail, navigate_to_entity.
"""

from unittest.mock import MagicMock, patch

from agent.governance_ui.controllers.audit_loaders import (
    register_audit_loader_controllers,
)


def _setup(rules=None, tasks=None, sessions=None, decisions=None):
    """Create mock ctrl + state, register handlers, return internals."""
    ctrl = MagicMock()
    state = MagicMock()

    state.rules = rules or []
    state.tasks = tasks or []
    state.sessions = sessions or []
    state.decisions = decisions or []
    state.audit_filter_entity_type = None
    state.audit_filter_action_type = None
    state.audit_filter_entity_id = None
    state.audit_filter_correlation_id = None

    triggers = {}

    def trigger_decorator(name):
        def wrapper(fn):
            triggers[name] = fn
            return fn
        return wrapper

    ctrl.trigger = MagicMock(side_effect=trigger_decorator)

    result = register_audit_loader_controllers(state, ctrl, "http://localhost:8082")

    return ctrl, state, triggers, result


# ── Registration ─────────────────────────────────────────


class TestRegistration:
    def test_registers_triggers(self):
        _, _, triggers, _ = _setup()
        assert "load_audit_trail" in triggers
        assert "navigate_to_entity" in triggers

    def test_returns_loader_function(self):
        _, _, _, result = _setup()
        assert "load_audit_trail" in result
        assert callable(result["load_audit_trail"])


# ── load_audit_trail ─────────────────────────────────────


class TestLoadAuditTrail:
    @patch("agent.governance_ui.controllers.audit_loaders.httpx")
    def test_success(self, mock_httpx):
        _, state, triggers, _ = _setup()
        summary_resp = MagicMock(status_code=200)
        summary_resp.json.return_value = {"total_entries": 42}
        entries_resp = MagicMock(status_code=200)
        entries_resp.json.return_value = [
            {"action": "create", "applied_rules": ["R-1", "R-2"]},
        ]
        mock_httpx.get.side_effect = [summary_resp, entries_resp]

        triggers["load_audit_trail"]()
        assert state.audit_summary == {"total_entries": 42}
        assert state.audit_entries[0]["applied_rules"] == "R-1, R-2"
        assert state.audit_loading is False

    @patch("agent.governance_ui.controllers.audit_loaders.httpx")
    def test_with_filters(self, mock_httpx):
        _, state, triggers, _ = _setup()
        state.audit_filter_entity_type = "rule"
        state.audit_filter_action_type = "create"

        summary_resp = MagicMock(status_code=200, json=MagicMock(return_value={}))
        entries_resp = MagicMock(status_code=200, json=MagicMock(return_value=[]))
        mock_httpx.get.side_effect = [summary_resp, entries_resp]

        triggers["load_audit_trail"]()

        # Check params include filters
        entries_call = mock_httpx.get.call_args_list[1]
        params = entries_call[1]["params"]
        assert params["entity_type"] == "rule"
        assert params["action_type"] == "create"

    @patch("agent.governance_ui.controllers.audit_loaders.httpx")
    def test_exception_sets_error(self, mock_httpx):
        _, state, triggers, _ = _setup()
        mock_httpx.get.side_effect = Exception("connection refused")

        triggers["load_audit_trail"]()
        assert "error" in state.audit_summary
        assert state.audit_entries == []
        assert state.audit_loading is False

    @patch("agent.governance_ui.controllers.audit_loaders.httpx")
    def test_applied_rules_non_list_ignored(self, mock_httpx):
        _, state, triggers, _ = _setup()
        summary_resp = MagicMock(status_code=200, json=MagicMock(return_value={}))
        entries_resp = MagicMock(status_code=200)
        entries_resp.json.return_value = [
            {"action": "update", "applied_rules": "not-a-list"},
        ]
        mock_httpx.get.side_effect = [summary_resp, entries_resp]

        triggers["load_audit_trail"]()
        # String should remain unchanged (not joined)
        assert state.audit_entries[0]["applied_rules"] == "not-a-list"


# ── navigate_to_entity ───────────────────────────────────


class TestNavigateToEntity:
    def test_rule_found(self):
        rules = [{"rule_id": "R-001", "name": "Rule 1"}]
        _, state, triggers, _ = _setup(rules=rules)
        triggers["navigate_to_entity"]("rule", "R-001")
        assert state.active_view == "rules"
        assert state.selected_rule == {"rule_id": "R-001", "name": "Rule 1"}
        assert state.show_rule_detail is True

    def test_rule_not_found(self):
        _, state, triggers, _ = _setup(rules=[])
        triggers["navigate_to_entity"]("rule", "R-MISSING")
        assert state.active_view == "rules"
        assert state.show_rule_detail is False

    def test_task_found(self):
        tasks = [{"task_id": "T-001"}]
        _, state, triggers, _ = _setup(tasks=tasks)
        triggers["navigate_to_entity"]("task", "T-001")
        assert state.active_view == "tasks"
        assert state.show_task_detail is True

    def test_session_found(self):
        sessions = [{"session_id": "S-001"}]
        _, state, triggers, _ = _setup(sessions=sessions)
        triggers["navigate_to_entity"]("session", "S-001")
        assert state.active_view == "sessions"
        assert state.show_session_detail is True

    def test_decision_found(self):
        decisions = [{"decision_id": "DEC-001"}]
        _, state, triggers, _ = _setup(decisions=decisions)
        triggers["navigate_to_entity"]("decision", "DEC-001")
        assert state.active_view == "decisions"
        assert state.show_decision_detail is True

    def test_case_insensitive(self):
        rules = [{"rule_id": "R-001"}]
        _, state, triggers, _ = _setup(rules=rules)
        triggers["navigate_to_entity"]("Rule", "R-001")
        assert state.active_view == "rules"

    def test_uses_id_fallback(self):
        tasks = [{"id": "T-002"}]
        _, state, triggers, _ = _setup(tasks=tasks)
        triggers["navigate_to_entity"]("task", "T-002")
        assert state.show_task_detail is True
