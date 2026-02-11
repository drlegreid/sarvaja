"""
Unit tests for Composite Traceability helpers.

Per A3: Tests for _trace_task, _trace_session, _trace_rule internal functions.
Tests: Pure helper functions (no MCP registration).
"""

import pytest
from unittest.mock import MagicMock

from governance.mcp_tools.traceability import (
    _trace_task,
    _trace_session,
    _trace_rule,
)


class _FakeEntity:
    """Minimal object with attribute access for TypeDB entity mocking."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# ---------------------------------------------------------------------------
# _trace_task
# ---------------------------------------------------------------------------
class TestTraceTask:
    """Tests for _trace_task() helper."""

    def test_not_found(self):
        client = MagicMock()
        client.get_task.return_value = None
        result = _trace_task(client, "T-999")
        assert result["task_id"] == "T-999"
        assert result["error"] == "not found"

    def test_basic_trace(self):
        client = MagicMock()
        client.get_task.return_value = _FakeEntity(
            description="Fix bug", status="DONE", phase="validate",
            gap_id="GAP-001", linked_rules=["R-1"], linked_sessions=["S-1"],
        )
        client.get_task_evidence.return_value = ["ev1.md"]
        client.get_task_commits.return_value = ["abc123"]
        result = _trace_task(client, "T-1")
        assert result["task_id"] == "T-1"
        assert result["description"] == "Fix bug"
        assert result["status"] == "DONE"
        assert result["phase"] == "validate"
        assert result["gap_id"] == "GAP-001"
        assert result["linked_rules"] == ["R-1"]
        assert result["linked_sessions"] == ["S-1"]
        assert result["evidence_files"] == ["ev1.md"]
        assert result["commits"] == ["abc123"]

    def test_none_linked_defaults_empty(self):
        client = MagicMock()
        client.get_task.return_value = _FakeEntity(
            description=None, status=None, phase=None,
            gap_id=None, linked_rules=None, linked_sessions=None,
        )
        client.get_task_evidence.return_value = None
        client.get_task_commits.return_value = None
        result = _trace_task(client, "T-2")
        assert result["linked_rules"] == []
        assert result["linked_sessions"] == []
        assert result["evidence_files"] == []
        assert result["commits"] == []

    def test_missing_attributes_graceful(self):
        client = MagicMock()
        client.get_task.return_value = _FakeEntity()  # no attributes
        client.get_task_evidence.return_value = []
        client.get_task_commits.return_value = []
        result = _trace_task(client, "T-3")
        assert result["description"] is None
        assert result["status"] is None


# ---------------------------------------------------------------------------
# _trace_session
# ---------------------------------------------------------------------------
class TestTraceSession:
    """Tests for _trace_session() helper."""

    def test_not_found(self):
        client = MagicMock()
        client.get_session.return_value = None
        result = _trace_session(client, "S-999")
        assert result["session_id"] == "S-999"
        assert result["error"] == "not found"

    def test_basic_trace(self):
        client = MagicMock()
        client.get_session.return_value = _FakeEntity(status="COMPLETED")
        client.get_session_evidence.return_value = ["ev.md"]
        client.get_session_rules.return_value = ["R-1"]
        client.get_session_decisions.return_value = [{"id": "D-1"}]
        client.get_tasks_for_session.return_value = [
            {"task_id": "T-1"}, {"task_id": "T-2"},
        ]
        result = _trace_session(client, "S-1")
        assert result["session_id"] == "S-1"
        assert result["status"] == "COMPLETED"
        assert result["evidence_files"] == ["ev.md"]
        assert result["rules_applied"] == ["R-1"]
        assert result["decisions"] == [{"id": "D-1"}]
        assert result["task_ids"] == ["T-1", "T-2"]

    def test_tasks_as_entities(self):
        client = MagicMock()
        client.get_session.return_value = _FakeEntity(status="ACTIVE")
        client.get_session_evidence.return_value = []
        client.get_session_rules.return_value = []
        client.get_session_decisions.return_value = []
        client.get_tasks_for_session.return_value = [
            _FakeEntity(task_id="T-A"),
        ]
        result = _trace_session(client, "S-2")
        assert result["task_ids"] == ["T-A"]

    def test_null_tasks_data(self):
        client = MagicMock()
        client.get_session.return_value = _FakeEntity(status="ACTIVE")
        client.get_session_evidence.return_value = None
        client.get_session_rules.return_value = None
        client.get_session_decisions.return_value = None
        client.get_tasks_for_session.return_value = None
        result = _trace_session(client, "S-3")
        assert result["task_ids"] == []
        assert result["evidence_files"] == []
        assert result["rules_applied"] == []
        assert result["decisions"] == []

    def test_task_without_task_id(self):
        """Tasks missing task_id attribute are skipped."""
        client = MagicMock()
        client.get_session.return_value = _FakeEntity(status="ACTIVE")
        client.get_session_evidence.return_value = []
        client.get_session_rules.return_value = []
        client.get_session_decisions.return_value = []
        client.get_tasks_for_session.return_value = [
            {"other": "data"},  # no task_id key
            {"task_id": "T-OK"},
        ]
        result = _trace_session(client, "S-4")
        assert result["task_ids"] == ["T-OK"]


# ---------------------------------------------------------------------------
# _trace_rule
# ---------------------------------------------------------------------------
class TestTraceRule:
    """Tests for _trace_rule() helper."""

    def test_not_found(self):
        client = MagicMock()
        client.get_rule_by_id.return_value = None
        result = _trace_rule(client, "R-999")
        assert result["rule_id"] == "R-999"
        assert result["error"] == "not found"

    def test_basic_trace(self):
        client = MagicMock()
        client.get_rule_by_id.return_value = _FakeEntity(
            name="Evidence Rule", category="governance",
            priority="CRITICAL", status="ACTIVE",
        )
        client.get_rule_dependencies.return_value = ["R-2"]
        client.get_rules_depending_on.return_value = ["R-3", "R-4"]
        result = _trace_rule(client, "R-1")
        assert result["rule_id"] == "R-1"
        assert result["name"] == "Evidence Rule"
        assert result["category"] == "governance"
        assert result["priority"] == "CRITICAL"
        assert result["status"] == "ACTIVE"
        assert result["dependencies"] == ["R-2"]
        assert result["depended_by"] == ["R-3", "R-4"]

    def test_null_deps_defaults_empty(self):
        client = MagicMock()
        client.get_rule_by_id.return_value = _FakeEntity(
            name="Test", category=None, priority=None, status=None,
        )
        client.get_rule_dependencies.return_value = None
        client.get_rules_depending_on.return_value = None
        result = _trace_rule(client, "R-2")
        assert result["dependencies"] == []
        assert result["depended_by"] == []
