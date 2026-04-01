"""
Unit tests for Agent-ID Standalone Persistence — SRVJ-BUG-AGENTID-PERSIST-01 (P6).

RED phase: These tests document the bug where update_task(agent_id="x") with no
other fields does NOT trigger a TypeDB write because both conditional gates
require task_obj (from preload) AND (status or evidence) or (priority or ...).

Scenario 1: agent_id-only with successful preload → client.update_task() called
Scenario 2: agent_id-only with failed preload (task_obj=None) → TypeDB write still attempted
Scenario 3: Dual-write confirmed — both _tasks_store and TypeDB updated
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, call

from governance.services.tasks_mutations import update_task
from governance.stores import _tasks_store


@pytest.fixture(autouse=True)
def clear_store():
    """Clear task store between tests."""
    _tasks_store.clear()
    yield
    _tasks_store.clear()


@pytest.fixture
def seed_task():
    """Pre-populate a task in the in-memory store with TODO status."""
    _tasks_store["T-AGENT-001"] = {
        "task_id": "T-AGENT-001",
        "description": "Agent-ID persistence test task",
        "phase": "P6",
        "status": "TODO",
        "agent_id": None,
        "summary": "Testing > AgentID > Persistence > P6",
        "linked_sessions": ["SESSION-SEED"],
        "linked_documents": [".claude/plans/concurrent-crunching-yao.md"],
        "created_at": "2026-03-27T10:00:00",
        "persistence_status": "persisted",
    }
    return _tasks_store["T-AGENT-001"]


class TestAgentIdOnlyTriggersTypeDBWrite:
    """Scenario 1: agent_id-only update with successful preload calls client.update_task()."""

    @patch("governance.services.tasks_mutations.get_typedb_client")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_agent_id_only_calls_client_update_task(
        self, mock_log, mock_audit, mock_client_fn, seed_task
    ):
        """update_task(agent_id='code-agent') with NO status/evidence/priority
        should still call client.update_task() to persist to TypeDB."""
        mock_client = MagicMock()
        mock_task_obj = MagicMock(
            name="Agent-ID test",
            status="TODO",
            agent_id=None,
            phase="P6",
            created_at=datetime.now(),
        )
        mock_client.get_task.return_value = mock_task_obj
        mock_client_fn.return_value = mock_client

        result = update_task("T-AGENT-001", agent_id="code-agent")

        assert result is not None
        assert result["agent_id"] == "code-agent"
        # THE KEY ASSERTION: client.update_task() must be called with agent_id
        mock_client.update_task.assert_called_once_with(
            "T-AGENT-001",
            priority=None,
            task_type=None,
            name=None,
            phase=None,
            summary=None,
            agent_id="code-agent",
            resolution_notes=None,
            layer=None,
            concern=None,
            method=None,
        )

    @patch("governance.services.tasks_mutations.get_typedb_client")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_agent_id_only_does_not_call_update_task_status(
        self, mock_log, mock_audit, mock_client_fn, seed_task
    ):
        """agent_id-only update should NOT call update_task_status() — that's for status/evidence."""
        mock_client = MagicMock()
        mock_task_obj = MagicMock(
            name="Agent-ID test",
            status="TODO",
            agent_id=None,
            phase="P6",
            created_at=datetime.now(),
        )
        mock_client.get_task.return_value = mock_task_obj
        mock_client_fn.return_value = mock_client

        update_task("T-AGENT-001", agent_id="code-agent")

        # update_task_status should NOT be called (no status/evidence provided)
        mock_client.update_task_status.assert_not_called()


class TestAgentIdPersistsWithoutPreload:
    """Scenario 2: agent_id-only update when preload returns None still persists."""

    @patch("governance.services.tasks_mutations.get_typedb_client")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_agent_id_persists_when_preload_returns_none(
        self, mock_log, mock_audit, mock_client_fn, seed_task
    ):
        """When client.get_task() returns None (TypeDB flaky) but task exists in
        _tasks_store, agent_id-only update should still attempt TypeDB write.

        The task exists in TypeDB — preload just failed to fetch it. We should
        attempt the write anyway rather than silently degrading to memory-only."""
        mock_client = MagicMock()
        # Preload fails — returns None
        mock_client.get_task.return_value = None
        mock_client_fn.return_value = mock_client

        result = update_task("T-AGENT-001", agent_id="code-agent")

        assert result is not None
        assert result["agent_id"] == "code-agent"
        # CRITICAL: Even though preload failed, TypeDB write should be attempted
        mock_client.update_task.assert_called_once_with(
            "T-AGENT-001",
            priority=None,
            task_type=None,
            name=None,
            phase=None,
            summary=None,
            agent_id="code-agent",
            resolution_notes=None,
            layer=None,
            concern=None,
            method=None,
        )


class TestAgentIdDualWrite:
    """Scenario 3: agent_id-only update writes to BOTH _tasks_store AND TypeDB."""

    @patch("governance.services.tasks_mutations.get_typedb_client")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_dual_write_agent_id(
        self, mock_log, mock_audit, mock_client_fn, seed_task
    ):
        """Both _tasks_store and TypeDB should reflect agent_id after update."""
        mock_client = MagicMock()
        mock_task_obj = MagicMock(
            name="Agent-ID test",
            status="TODO",
            agent_id=None,
            phase="P6",
            created_at=datetime.now(),
        )
        mock_client.get_task.return_value = mock_task_obj
        mock_client_fn.return_value = mock_client

        result = update_task("T-AGENT-001", agent_id="research-agent")

        # In-memory store updated
        assert _tasks_store["T-AGENT-001"]["agent_id"] == "research-agent"
        # TypeDB write attempted
        mock_client.update_task.assert_called_once()
        call_kwargs = mock_client.update_task.call_args
        assert call_kwargs[1]["agent_id"] == "research-agent" or call_kwargs[0][0] == "T-AGENT-001"

    @patch("governance.services.tasks_mutations.get_typedb_client")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_agent_id_with_status_uses_both_paths(
        self, mock_log, mock_audit, mock_client_fn, seed_task
    ):
        """When agent_id is provided WITH status, both update_task_status() and
        update_task() should be called — status goes via update_task_status,
        agent_id goes via update_task."""
        mock_client = MagicMock()
        mock_task_obj = MagicMock(
            name="Agent-ID test",
            status="TODO",
            agent_id=None,
            phase="P6",
            created_at=datetime.now(),
        )
        mock_client.get_task.return_value = mock_task_obj
        mock_client.update_task_status.return_value = mock_task_obj
        mock_client_fn.return_value = mock_client

        update_task("T-AGENT-001", status="IN_PROGRESS", agent_id="code-agent")

        # Both TypeDB paths should fire
        mock_client.update_task_status.assert_called_once()
        mock_client.update_task.assert_called_once()
