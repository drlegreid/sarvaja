"""TDD Tests for Cycle 9-10: Audit applied_rules Structure Preservation.

Gap: applied_rules comma-joined at UI layer loses structure.
Fix: Keep as list, add applied_rules_display for table rendering.
"""
from unittest.mock import patch, MagicMock

import pytest


class TestAuditRulesNotCommaJoined:
    """audit_loaders no longer comma-joins applied_rules."""

    @patch("agent.governance_ui.controllers.audit_loaders.httpx")
    def test_applied_rules_remains_list(self, mock_httpx):
        """After load_audit_trail, applied_rules stays as list."""
        mock_summary = MagicMock()
        mock_summary.status_code = 200
        mock_summary.json.return_value = {"total_entries": 1}

        mock_entries = MagicMock()
        mock_entries.status_code = 200
        mock_entries.json.return_value = [
            {
                "audit_id": "AUD-001",
                "entity_id": "TASK-001",
                "entity_type": "task",
                "action_type": "UPDATE",
                "actor_id": "code-agent",
                "applied_rules": ["H-TASK-002", "H-TASK-005"],
                "timestamp": "2026-02-15T10:00:00",
                "correlation_id": "CORR-001",
            }
        ]
        mock_httpx.get.side_effect = [mock_summary, mock_entries]

        class SimpleState:
            def __init__(self):
                self.audit_summary = {}
                self.audit_entries = []
                self.audit_loading = True
                self.audit_filter_entity_type = None
                self.audit_filter_action_type = None
                self.audit_filter_entity_id = ""
                self.audit_filter_correlation_id = ""
                self.active_view = "audit"

            def change(self, *args, **kwargs):
                return lambda f: f

        state = SimpleState()
        ctrl = MagicMock()
        ctrl.trigger = MagicMock(return_value=lambda f: f)

        from agent.governance_ui.controllers.audit_loaders import register_audit_loader_controllers
        loaders = register_audit_loader_controllers(state, ctrl, "http://localhost:8082")

        loaders["load_audit_trail"]()

        assert len(state.audit_entries) == 1
        rules = state.audit_entries[0]["applied_rules"]
        assert isinstance(rules, list), f"Expected list, got {type(rules)}: {rules}"
        assert rules == ["H-TASK-002", "H-TASK-005"]

    @patch("agent.governance_ui.controllers.audit_loaders.httpx")
    def test_applied_rules_display_field_added(self, mock_httpx):
        """Each entry gets applied_rules_display for table rendering."""
        mock_summary = MagicMock()
        mock_summary.status_code = 200
        mock_summary.json.return_value = {"total_entries": 1}

        mock_entries = MagicMock()
        mock_entries.status_code = 200
        mock_entries.json.return_value = [
            {
                "audit_id": "AUD-002",
                "entity_id": "TASK-002",
                "entity_type": "task",
                "action_type": "CREATE",
                "actor_id": "code-agent",
                "applied_rules": ["RULE-001", "RULE-002", "RULE-003"],
                "timestamp": "2026-02-15T11:00:00",
                "correlation_id": "CORR-002",
            }
        ]
        mock_httpx.get.side_effect = [mock_summary, mock_entries]

        class SimpleState:
            def __init__(self):
                self.audit_summary = {}
                self.audit_entries = []
                self.audit_loading = True
                self.audit_filter_entity_type = None
                self.audit_filter_action_type = None
                self.audit_filter_entity_id = ""
                self.audit_filter_correlation_id = ""
                self.active_view = "audit"

            def change(self, *args, **kwargs):
                return lambda f: f

        state = SimpleState()
        ctrl = MagicMock()
        ctrl.trigger = MagicMock(return_value=lambda f: f)

        from agent.governance_ui.controllers.audit_loaders import register_audit_loader_controllers
        loaders = register_audit_loader_controllers(state, ctrl, "http://localhost:8082")

        loaders["load_audit_trail"]()

        entry = state.audit_entries[0]
        assert "applied_rules_display" in entry
        assert entry["applied_rules_display"] == "RULE-001, RULE-002, RULE-003"
        assert isinstance(entry["applied_rules"], list)

    @patch("agent.governance_ui.controllers.audit_loaders.httpx")
    def test_empty_applied_rules_handled(self, mock_httpx):
        """Empty applied_rules list results in empty display."""
        mock_summary = MagicMock()
        mock_summary.status_code = 200
        mock_summary.json.return_value = {"total_entries": 1}

        mock_entries = MagicMock()
        mock_entries.status_code = 200
        mock_entries.json.return_value = [
            {
                "audit_id": "AUD-003",
                "entity_id": "TASK-003",
                "entity_type": "task",
                "action_type": "DELETE",
                "actor_id": "admin",
                "applied_rules": [],
                "timestamp": "2026-02-15T12:00:00",
                "correlation_id": "CORR-003",
            }
        ]
        mock_httpx.get.side_effect = [mock_summary, mock_entries]

        class SimpleState:
            def __init__(self):
                self.audit_summary = {}
                self.audit_entries = []
                self.audit_loading = True
                self.audit_filter_entity_type = None
                self.audit_filter_action_type = None
                self.audit_filter_entity_id = ""
                self.audit_filter_correlation_id = ""
                self.active_view = "audit"

            def change(self, *args, **kwargs):
                return lambda f: f

        state = SimpleState()
        ctrl = MagicMock()
        ctrl.trigger = MagicMock(return_value=lambda f: f)

        from agent.governance_ui.controllers.audit_loaders import register_audit_loader_controllers
        loaders = register_audit_loader_controllers(state, ctrl, "http://localhost:8082")

        loaders["load_audit_trail"]()

        entry = state.audit_entries[0]
        assert entry["applied_rules"] == []
        assert entry["applied_rules_display"] == ""


class TestAuditViewUsesDisplayField:
    """Audit view table uses applied_rules_display column."""

    def test_table_header_uses_display_key(self):
        """Table header for rules uses applied_rules_display key."""
        import inspect
        from agent.governance_ui.views.audit_view import build_audit_table
        source = inspect.getsource(build_audit_table)
        assert "applied_rules_display" in source
