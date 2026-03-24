"""
Unit tests for Task Service Mutations.

Per DOC-SIZE-01-v1: Tests for extracted tasks_mutations.py module.
Tests: update_task, delete_task, link_task_to_rule, link_task_to_session.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from governance.services.tasks_mutations import (
    update_task,
    delete_task,
    link_task_to_rule,
    link_task_to_session,
)
from governance.stores import _tasks_store


@pytest.fixture(autouse=True)
def clear_store():
    """Clear task store between tests."""
    _tasks_store.clear()
    yield
    _tasks_store.clear()


@pytest.fixture
def seed_task():
    """Pre-populate a task in the in-memory store."""
    _tasks_store["T-001"] = {
        "task_id": "T-001",
        "description": "Test task",
        "phase": "P10",
        "status": "TODO",
        "agent_id": "code-agent",
        "summary": "Test > Task > Seed > Fixture",
        "linked_sessions": ["SESSION-SEED"],
        "linked_documents": [".claude/plans/test-plan.md"],
        "created_at": "2026-02-11T10:00:00",
    }
    return _tasks_store["T-001"]


class TestUpdateTask:
    """Tests for update_task()."""

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_update_description(self, mock_log, mock_audit, mock_client, seed_task):
        result = update_task("T-001", description="Updated desc")
        assert result is not None
        assert result["description"] == "Updated desc"

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_update_status(self, mock_log, mock_audit, mock_client, seed_task):
        result = update_task("T-001", status="IN_PROGRESS", agent_id="code-agent")
        assert result["status"] == "IN_PROGRESS"
        assert result["agent_id"] == "code-agent"

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_update_status_done_sets_completed_at(self, mock_log, mock_audit, mock_client, seed_task):
        result = update_task("T-001", status="DONE")
        assert result["status"] == "DONE"
        assert "completed_at" in result

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_h_task_002_auto_assigns_agent(self, mock_log, mock_audit, mock_client, seed_task):
        """Per H-TASK-002: IN_PROGRESS without agent_id auto-assigns 'code-agent'."""
        result = update_task("T-001", status="IN_PROGRESS")
        assert result["agent_id"] == "code-agent"

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_h_task_002_preserves_existing_agent(self, mock_log, mock_audit, mock_client):
        _tasks_store["T-002"] = {
            "task_id": "T-002", "description": "Agent task",
            "status": "TODO", "agent_id": "research-agent",
        }
        result = update_task("T-002", status="IN_PROGRESS")
        assert result["agent_id"] == "research-agent"

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_update_nonexistent_returns_none(self, mock_log, mock_audit, mock_client):
        result = update_task("T-NOPE", description="foo")
        assert result is None

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_update_multiple_fields(self, mock_log, mock_audit, mock_client, seed_task):
        result = update_task(
            "T-001", description="New desc", phase="P12",
            body="Task body", evidence="Evidence here",
        )
        assert result["description"] == "New desc"
        assert result["phase"] == "P12"
        assert result["body"] == "Task body"
        assert result["evidence"] == "Evidence here"

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_update_records_audit(self, mock_log, mock_audit, mock_client, seed_task):
        update_task("T-001", status="IN_PROGRESS", agent_id="code-agent")
        mock_audit.assert_called_once()
        call_args = mock_audit.call_args
        assert call_args[0][0] == "UPDATE"
        assert call_args[0][1] == "task"
        assert call_args[0][2] == "T-001"

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_update_linked_sessions(self, mock_log, mock_audit, mock_client, seed_task):
        result = update_task("T-001", linked_sessions=["SESSION-1", "SESSION-2"])
        assert result["linked_sessions"] == ["SESSION-1", "SESSION-2"]

    @patch("governance.services.tasks_mutations.get_typedb_client")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_update_with_typedb_persists_sessions(self, mock_log, mock_audit, mock_client_fn, seed_task):
        mock_client = MagicMock()
        mock_client.get_task.return_value = MagicMock(
            name="Test", status="TODO", agent_id=None,
            phase="P10", created_at=datetime.now(),
        )
        mock_client.update_task_status.return_value = None
        mock_client_fn.return_value = mock_client
        update_task("T-001", status="IN_PROGRESS", linked_sessions=["S-1"])
        mock_client.link_task_to_session.assert_called_once_with("T-001", "S-1")


class TestDeleteTask:
    """Tests for delete_task()."""

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_delete_existing(self, mock_log, mock_audit, mock_client, seed_task):
        assert delete_task("T-001") is True
        assert "T-001" not in _tasks_store

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_delete_nonexistent(self, mock_log, mock_audit, mock_client):
        assert delete_task("T-NOPE") is False

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_delete_records_audit(self, mock_log, mock_audit, mock_client, seed_task):
        delete_task("T-001")
        mock_audit.assert_called_once()
        assert mock_audit.call_args[0][0] == "DELETE"

    @patch("governance.services.tasks_mutations.get_typedb_client")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_delete_with_typedb(self, mock_log, mock_audit, mock_client_fn, seed_task):
        mock_client = MagicMock()
        mock_client.get_task.return_value = MagicMock()
        mock_client.delete_task.return_value = True
        mock_client_fn.return_value = mock_client
        assert delete_task("T-001") is True
        mock_client.delete_task.assert_called_once_with("T-001")

    @patch("governance.services.tasks_mutations.get_typedb_client")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_delete_typedb_error_falls_back(self, mock_log, mock_audit, mock_client_fn, seed_task):
        mock_client = MagicMock()
        mock_client.get_task.side_effect = Exception("TypeDB down")
        mock_client_fn.return_value = mock_client
        assert delete_task("T-001") is True
        assert "T-001" not in _tasks_store


class TestLinkTaskToRule:
    """Tests for link_task_to_rule()."""

    @patch("governance.services.tasks_mutations_linking.get_typedb_client", return_value=None)
    def test_no_client_returns_false(self, mock_client):
        assert link_task_to_rule("T-001", "RULE-001") is False

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_task_not_found_returns_false(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client.get_task.return_value = None
        mock_client_fn.return_value = mock_client
        assert link_task_to_rule("T-NOPE", "RULE-001") is False

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_successful_link(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client.get_task.return_value = MagicMock()
        mock_client.link_task_to_rule.return_value = True
        mock_client_fn.return_value = mock_client
        assert link_task_to_rule("T-001", "RULE-001") is True
        mock_client.link_task_to_rule.assert_called_once_with("T-001", "RULE-001")

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_link_error_returns_false(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client.get_task.return_value = MagicMock()
        mock_client.link_task_to_rule.side_effect = Exception("fail")
        mock_client_fn.return_value = mock_client
        assert link_task_to_rule("T-001", "RULE-001") is False


class TestLinkTaskToSession:
    """Tests for link_task_to_session()."""

    @patch("governance.services.tasks_mutations_linking.get_typedb_client", return_value=None)
    def test_no_client_returns_false(self, mock_client):
        assert link_task_to_session("T-001", "SESSION-001") is False

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_task_not_found_returns_false(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client.get_task.return_value = None
        mock_client_fn.return_value = mock_client
        assert link_task_to_session("T-NOPE", "SESSION-001") is False

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_successful_link(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client.get_task.return_value = MagicMock()
        mock_client.link_task_to_session.return_value = True
        mock_client_fn.return_value = mock_client
        assert link_task_to_session("T-001", "SESSION-001") is True

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_link_error_returns_false(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client.get_task.return_value = MagicMock()
        mock_client.link_task_to_session.side_effect = Exception("fail")
        mock_client_fn.return_value = mock_client
        assert link_task_to_session("T-001", "SESSION-001") is False
