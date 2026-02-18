"""
Unit tests for Tab Deep Scan Batch 36 — Stores + TypeDB access + helpers + rules + tasks.

Covers: BUG-STORE-007 (linked_commits null-safe), BUG-STORE-008 (session relations null-safe),
BUG-HELPERS-001 (evidence str coercion), BUG-RULES-001 (get_rule_tasks None guard),
BUG-TASKS-002 (session resolution logging).
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import patch, MagicMock


# ── BUG-STORE-007: linked_commits null-safe in _task_to_dict ─────────


class TestLinkedCommitsNullSafe:
    """_task_to_dict must use 'or []' for linked_commits."""

    def test_has_or_empty_list(self):
        from governance.stores import typedb_access
        source = inspect.getsource(typedb_access._task_to_dict)
        assert "linked_commits or []" in source

    def test_consistent_with_helpers(self):
        """Both conversion functions must handle linked_commits the same way."""
        from governance.stores import typedb_access, helpers
        td_source = inspect.getsource(typedb_access._task_to_dict)
        h_source = inspect.getsource(helpers.task_to_response)
        # Both should use 'or []' pattern
        assert "linked_commits or []" in td_source
        assert "linked_commits or []" in h_source

    def test_all_list_fields_null_safe(self):
        """All list fields in _task_to_dict should use 'or []'."""
        from governance.stores import typedb_access
        source = inspect.getsource(typedb_access._task_to_dict)
        list_fields = ["linked_rules", "linked_sessions", "linked_commits", "linked_documents"]
        for field in list_fields:
            assert f"{field} or []" in source, f"Missing null-safe for {field}"

    def test_bugfix_marker(self):
        from governance.stores import typedb_access
        source = inspect.getsource(typedb_access._task_to_dict)
        assert "BUG-STORE-007" in source


# ── BUG-STORE-008: Session relation fields null-safe ─────────────────


class TestSessionRelationsNullSafe:
    """_session_to_dict must use 'or []' for list fields."""

    def test_evidence_files_null_safe(self):
        from governance.stores import typedb_access
        source = inspect.getsource(typedb_access._session_to_dict)
        assert "evidence_files or []" in source

    def test_linked_rules_null_safe(self):
        from governance.stores import typedb_access
        source = inspect.getsource(typedb_access._session_to_dict)
        assert "linked_rules_applied or []" in source

    def test_linked_decisions_null_safe(self):
        from governance.stores import typedb_access
        source = inspect.getsource(typedb_access._session_to_dict)
        assert "linked_decisions or []" in source

    def test_bugfix_marker(self):
        from governance.stores import typedb_access
        source = inspect.getsource(typedb_access._session_to_dict)
        assert "BUG-STORE-008" in source


# ── BUG-HELPERS-001: Evidence string coercion ────────────────────────


class TestEvidenceStringCoercion:
    """synthesize_execution_events must coerce evidence to str."""

    def test_has_str_coercion(self):
        from governance.stores import helpers
        source = inspect.getsource(helpers.synthesize_execution_events)
        assert "str(evidence)" in source

    def test_list_evidence_no_crash(self):
        """List-typed evidence should not crash on slicing."""
        from governance.stores.helpers import synthesize_execution_events
        # Pass task_data dict with list evidence (non-string truthy value)
        task_data = {"evidence": ["item1", "item2"], "status": "DONE"}
        events = synthesize_execution_events("TASK-1", task_data)
        ev_events = [e for e in events if e["event_type"] == "evidence"]
        assert len(ev_events) == 1
        # Should have been coerced to string representation
        assert isinstance(ev_events[0]["message"], str)

    def test_string_evidence_still_works(self):
        """Normal string evidence should work unchanged."""
        from governance.stores.helpers import synthesize_execution_events
        task_data = {"evidence": "Bug fixed in module X", "status": "DONE"}
        events = synthesize_execution_events("TASK-1", task_data)
        ev_events = [e for e in events if e["event_type"] == "evidence"]
        assert len(ev_events) == 1
        assert "Bug fixed" in ev_events[0]["message"]

    def test_long_evidence_truncated(self):
        """Evidence > 100 chars should be truncated with '...'."""
        from governance.stores.helpers import synthesize_execution_events
        task_data = {"evidence": "A" * 200, "status": "DONE"}
        events = synthesize_execution_events("TASK-1", task_data)
        ev_events = [e for e in events if e["event_type"] == "evidence"]
        assert ev_events[0]["message"].endswith("...")
        assert len(ev_events[0]["message"]) == 103  # 100 + "..."

    def test_bugfix_marker(self):
        from governance.stores import helpers
        source = inspect.getsource(helpers.synthesize_execution_events)
        assert "BUG-HELPERS-001" in source


# ── BUG-RULES-001: get_rule_tasks None guard ─────────────────────────


class TestRuleTasksNoneGuard:
    """get_rule_tasks must guard against None from TypeDB."""

    def test_has_none_guard(self):
        from governance.services import rules_relations
        source = inspect.getsource(rules_relations.get_rule_tasks)
        assert "tasks or []" in source

    def test_none_tasks_returns_empty(self):
        """When TypeDB returns None for both lookups, count should be 0."""
        from governance.services.rules_relations import get_rule_tasks
        mock_client = MagicMock()
        mock_client.get_tasks_for_rule.return_value = None
        with patch("governance.services.rules_relations._get_client_or_raise", return_value=mock_client):
            result = get_rule_tasks("RULE-001")
        assert result["count"] == 0
        assert result["implementing_tasks"] == []

    def test_valid_tasks_counted(self):
        """When TypeDB returns tasks, they should be counted."""
        from governance.services.rules_relations import get_rule_tasks
        mock_client = MagicMock()
        mock_tasks = [{"task_id": "T-1"}, {"task_id": "T-2"}]
        mock_client.get_tasks_for_rule.return_value = mock_tasks
        with patch("governance.services.rules_relations._get_client_or_raise", return_value=mock_client):
            result = get_rule_tasks("RULE-001")
        assert result["count"] == 2

    def test_bugfix_marker(self):
        from governance.services import rules_relations
        source = inspect.getsource(rules_relations.get_rule_tasks)
        assert "BUG-RULES-001" in source


# ── BUG-TASKS-002: Session resolution logging ────────────────────────


class TestSessionResolutionLogging:
    """get_sessions_for_task must log unresolved sessions."""

    def test_has_logging_for_unknown(self):
        from governance.services import tasks
        source = inspect.getsource(tasks.get_sessions_for_task)
        assert "logger.debug" in source

    def test_bugfix_marker(self):
        from governance.services import tasks
        source = inspect.getsource(tasks.get_sessions_for_task)
        assert "BUG-TASKS-002" in source


# ── Cross-layer consistency ──────────────────────────────────────────


class TestCrossLayerConsistencyBatch36:
    """Cross-cutting null-safety patterns across stores layer."""

    def test_task_to_dict_all_list_fields_safe(self):
        """_task_to_dict should not have bare list attribute access."""
        from governance.stores import typedb_access
        source = inspect.getsource(typedb_access._task_to_dict)
        # These patterns indicate unsafe access
        assert "task.linked_rules," not in source  # Should be 'or []'
        assert "task.linked_sessions," not in source
        assert "task.linked_commits," not in source
        assert "task.linked_documents," not in source

    def test_session_to_dict_all_list_fields_safe(self):
        """_session_to_dict should not have bare list attribute access for relations."""
        from governance.stores import typedb_access
        source = inspect.getsource(typedb_access._session_to_dict)
        # These key relation fields should all use 'or []'
        assert "session.evidence_files," not in source
        assert "session.linked_rules_applied," not in source
        assert "session.linked_decisions," not in source

    def test_helpers_and_typedb_access_consistent(self):
        """task_to_response and _task_to_dict should handle lists consistently."""
        from governance.stores import typedb_access, helpers
        td_source = inspect.getsource(typedb_access._task_to_dict)
        h_source = inspect.getsource(helpers.task_to_response)
        # Count 'or []' patterns — both should have at least 4
        td_count = td_source.count("or []")
        h_count = h_source.count("or []")
        assert td_count >= 4, f"_task_to_dict has only {td_count} null-safe list fields"
        assert h_count >= 4, f"task_to_response has only {h_count} null-safe list fields"
