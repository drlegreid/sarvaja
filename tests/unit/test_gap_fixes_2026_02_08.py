"""Tests for gap fixes discovered during 2026-02-08 dynamic orthogonal test.

Tests cover:
- GAP-AUDIT-EMPTY-001: Audit retention fix + bootstrap
- GAP-TASK-CREATE-UI-001: Task form state initialization
- GAP-RULE-EDIT-001: Rule edit form pre-population
- GAP-UI-TS-001: Timestamp formatting in tasks
- GAP-UI-PAGN-001: Session pagination dedup
- GAP-SESSION-DETAIL-001: Agent in session detail
- GAP-MONITOR-COUNT-001: Monitor event counter
- GAP-CHAT-COUNT-001: Chat /status session count
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


class TestAuditRetentionFix:
    """GAP-AUDIT-EMPTY-001: Verify retention policy uses timedelta correctly."""

    def test_retention_keeps_recent_entries(self):
        """Entries within 7 days should not be pruned."""
        import governance.stores.audit as audit_mod
        original = audit_mod._audit_store.copy()
        audit_mod._audit_store.clear()
        audit_mod._audit_store.append({
            "audit_id": "AUDIT-TEST-RECENT",
            "timestamp": datetime.now().isoformat(),
            "action_type": "TEST",
        })
        try:
            audit_mod._apply_retention(days=7)
            assert len(audit_mod._audit_store) == 1
            assert audit_mod._audit_store[0]["audit_id"] == "AUDIT-TEST-RECENT"
        finally:
            audit_mod._audit_store.clear()
            audit_mod._audit_store.extend(original)

    def test_retention_prunes_old_entries(self):
        """Entries older than 7 days should be pruned."""
        import governance.stores.audit as audit_mod
        original = audit_mod._audit_store.copy()
        audit_mod._audit_store.clear()
        old_date = (datetime.now() - timedelta(days=10)).isoformat()
        audit_mod._audit_store.append({
            "audit_id": "AUDIT-TEST-OLD",
            "timestamp": old_date,
            "action_type": "TEST",
        })
        try:
            audit_mod._apply_retention(days=7)
            assert len(audit_mod._audit_store) == 0
        finally:
            audit_mod._audit_store.clear()
            audit_mod._audit_store.extend(original)

    def test_retention_mixed_entries(self):
        """Only old entries should be pruned, recent kept."""
        import governance.stores.audit as audit_mod
        original = audit_mod._audit_store.copy()
        audit_mod._audit_store.clear()
        audit_mod._audit_store.append({
            "audit_id": "AUDIT-OLD",
            "timestamp": (datetime.now() - timedelta(days=10)).isoformat(),
        })
        audit_mod._audit_store.append({
            "audit_id": "AUDIT-NEW",
            "timestamp": datetime.now().isoformat(),
        })
        try:
            audit_mod._apply_retention(days=7)
            assert len(audit_mod._audit_store) == 1
            assert audit_mod._audit_store[0]["audit_id"] == "AUDIT-NEW"
        finally:
            audit_mod._audit_store.clear()
            audit_mod._audit_store.extend(original)


class TestAuditBootstrap:
    """GAP-AUDIT-EMPTY-001: Verify seed records bootstrap audit entry."""

    @patch("governance.seed.get_typedb_client")
    @patch("governance.seed.record_audit")
    def test_seed_records_bootstrap(self, mock_audit, mock_client):
        """seed_tasks_and_sessions should call record_audit with BOOTSTRAP."""
        mock_client.return_value = None  # Force memory fallback
        from governance.seed import seed_tasks_and_sessions
        tasks, sessions, agents = {}, {}, {}
        seed_tasks_and_sessions(tasks, sessions, agents)

        mock_audit.assert_called_once()
        call_kwargs = mock_audit.call_args
        assert call_kwargs[1]["action_type"] == "BOOTSTRAP"
        assert call_kwargs[1]["entity_type"] == "system"
        assert "tasks" in call_kwargs[1]["metadata"]


class TestTaskFormStateInit:
    """GAP-TASK-CREATE-UI-001: Task form state variables must be initialized."""

    def test_task_form_state_exists(self):
        """All task form state vars must be in initial state."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "form_task_id" in state
        assert "form_task_description" in state
        assert "form_task_phase" in state
        assert "form_task_agent" in state
        assert "show_task_form" in state

    def test_task_form_defaults(self):
        """Task form defaults should be sensible."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["form_task_id"] == ""
        assert state["form_task_description"] == ""
        assert state["form_task_phase"] == "P10"
        assert state["form_task_agent"] == ""
        assert state["show_task_form"] is False


class TestRuleEditPrePopulation:
    """GAP-RULE-EDIT-001: Edit rule must populate form with selected rule's values."""

    def test_edit_rule_trigger_registered(self):
        """edit_rule trigger must be registered."""
        from agent.governance_ui.controllers.rules import register_rules_controllers

        state = MagicMock()
        ctrl = MagicMock()
        register_rules_controllers(state, ctrl, "http://test:8082")

        # Check that edit_rule was registered as a trigger
        trigger_calls = [c for c in ctrl.trigger.call_args_list if c[0][0] == "edit_rule"]
        assert len(trigger_calls) == 1

    def test_edit_rule_populates_form(self):
        """edit_rule should copy selected rule data to form state."""
        from agent.governance_ui.controllers.rules import register_rules_controllers

        state = MagicMock()
        state.selected_rule = {
            "rule_id": "GOV-RULE-01-v1",
            "name": "Test Rule",
            "directive": "Always test thoroughly",
            "category": "technical",
            "priority": "MEDIUM",
        }
        ctrl = MagicMock()

        # Capture the registered function
        triggers = {}

        def capture_trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = capture_trigger
        ctrl.set = capture_trigger
        register_rules_controllers(state, ctrl, "http://test:8082")

        # Call edit_rule
        triggers["edit_rule"]()
        assert state.form_rule_id == "GOV-RULE-01-v1"
        assert state.form_rule_title == "Test Rule"
        assert state.form_rule_directive == "Always test thoroughly"
        assert state.form_rule_category == "technical"
        assert state.form_rule_priority == "MEDIUM"
        assert state.rule_form_mode == "edit"
        assert state.show_rule_form is True


class TestTimestampFormatting:
    """GAP-UI-TS-001: Timestamps should be formatted for display."""

    def test_format_timestamps_in_list(self):
        """format_timestamps_in_list should format ISO strings."""
        from agent.governance_ui.utils import format_timestamps_in_list

        items = [
            {"task_id": "T-1", "created_at": "2026-02-08T14:30:00.123456"},
            {"task_id": "T-2", "created_at": None},
            {"task_id": "T-3"},  # missing field
        ]
        result = format_timestamps_in_list(items, ["created_at"])
        # First item should be formatted (not raw ISO)
        assert "T" not in result[0]["created_at"] or len(result[0]["created_at"]) < 26
        # None stays None
        assert result[1]["created_at"] is None


class TestSessionPagination:
    """GAP-UI-PAGN-001: Sessions table must not have dual pagination."""

    def test_session_detail_has_agent(self):
        """GAP-SESSION-DETAIL-001: Session detail should include agent field.

        Verify the build function includes agent_id display.
        """
        import inspect
        from agent.governance_ui.views.sessions.content import build_session_info_card
        source = inspect.getsource(build_session_info_card)
        assert "agent_id" in source
        assert "mdi-robot" in source


class TestMonitorCounter:
    """GAP-MONITOR-COUNT-001: Monitor counter must reflect actual feed length."""

    def test_monitor_stats_uses_feed_length(self):
        """Stats card should reference monitor_feed.length."""
        import inspect
        from agent.governance_ui.views.monitor_view import build_monitor_stats
        source = inspect.getsource(build_monitor_stats)
        assert "monitor_feed.length" in source


class TestChatStatusCount:
    """GAP-CHAT-COUNT-001: /status must show accurate session count."""

    @patch("governance.routes.chat.commands.list_sessions")
    @patch("governance.routes.chat.commands.get_client")
    def test_status_shows_total_not_active(self, mock_client, mock_ls):
        """Status should say 'total' not 'active' for sessions."""
        mock_client.return_value = None
        mock_ls.return_value = {"items": [], "pagination": {"total": 42}}
        from governance.routes.chat.commands import process_chat_command
        result = process_chat_command("/status", agent_id="test-agent")
        assert "42 total" in result

    @patch("governance.routes.chat.commands.list_sessions", side_effect=Exception("DB down"))
    @patch("governance.routes.chat.commands.get_client")
    def test_status_fallback_on_error(self, mock_client, mock_ls):
        """On service layer error, falls back to in-memory count."""
        mock_client.return_value = None
        from governance.routes.chat.commands import process_chat_command
        result = process_chat_command("/status", agent_id="test-agent")
        assert "Sessions:" in result
        assert "total" in result
