"""
Unit tests for DONE Gate Validation Source — SRVJ-BUG-DONE-GATE-01 (P5).

RED phase: These tests MUST fail until the DONE gate propagates
validation_source ("typedb" | "cache") into the update_task() response.

Tests:
1. TypeDB reachable → validation_source="typedb" in response
2. TypeDB unreachable → validation_source="cache" in response
3. TypeDB unreachable + stale cache missing required field → ValueError still raised
4. Cache warning logged with task_id when source is "cache"
"""

import logging
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from governance.services.tasks_mutations import update_task
from governance.stores import _tasks_store


@pytest.fixture(autouse=True)
def clear_store():
    """Clear task store between tests."""
    _tasks_store.clear()
    yield
    _tasks_store.clear()


def _seed_done_ready_task(task_id: str = "T-DONE-001", *, task_type: str = "chore") -> dict:
    """Seed a task with all mandatory fields for DONE gate (chore = minimal DoD)."""
    _tasks_store[task_id] = {
        "task_id": task_id,
        "description": "Test task for DONE gate",
        "phase": "P5",
        "status": "IN_PROGRESS",
        "agent_id": "code-agent",
        "summary": "Testing > DoneGate > ValidationSource",
        "linked_sessions": ["SESSION-TEST-001"],
        "linked_documents": [".claude/plans/test-plan.md"],
        "evidence": "Automated test evidence",
        "created_at": "2026-03-27T10:00:00",
        "task_type": task_type,
    }
    return _tasks_store[task_id]


def _mock_typedb_task_obj(task_data: dict) -> MagicMock:
    """Create a MagicMock mimicking a TypeDB task entity."""
    obj = MagicMock()
    obj.name = task_data.get("description", "")
    obj.status = task_data.get("status", "IN_PROGRESS")
    obj.agent_id = task_data.get("agent_id")
    obj.phase = task_data.get("phase", "")
    obj.created_at = datetime.fromisoformat(task_data.get("created_at", "2026-03-27T10:00:00"))
    obj.priority = task_data.get("priority")
    obj.task_type = task_data.get("task_type")
    obj.evidence = task_data.get("evidence")
    obj.resolution = None
    obj.claimed_at = None
    obj.completed_at = None
    obj.document_path = None
    obj.linked_rules = []
    obj.linked_sessions = task_data.get("linked_sessions", [])
    obj.linked_commits = []
    obj.linked_documents = task_data.get("linked_documents", [])
    obj.summary = task_data.get("summary")
    obj.workspace_id = None
    obj.resolution_notes = None
    obj.body = None
    obj.gap_id = None
    obj.layer = None
    obj.concern = None
    obj.method = None
    return obj


class TestDoneGateValidationSourceTypeDB:
    """When TypeDB is reachable, validation_source should be 'typedb'."""

    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.services.tasks_mutations.get_typedb_client")
    @patch("governance.services.tasks_preload.get_typedb_client")
    def test_done_gate_typedb_reachable_returns_validation_source_typedb(
        self, mock_preload_client_fn, mock_mut_client_fn, mock_log, mock_audit,
    ):
        """DONE gate with TypeDB reachable → response includes validation_source='typedb'."""
        task_data = _seed_done_ready_task()
        task_obj = _mock_typedb_task_obj(task_data)

        # Preload client returns task (TypeDB reachable)
        mock_preload_client = MagicMock()
        mock_preload_client.get_task.return_value = task_obj
        mock_preload_client_fn.return_value = mock_preload_client

        # Mutations client also returns task
        mock_mut_client = MagicMock()
        mock_mut_client.get_task.return_value = task_obj
        mock_mut_client.update_task_status.return_value = task_obj
        mock_mut_client_fn.return_value = mock_mut_client

        result = update_task("T-DONE-001", status="DONE")

        assert result is not None
        assert result["status"] == "DONE"
        assert "validation_source" in result, (
            "DONE gate must include validation_source in response"
        )
        assert result["validation_source"] == "typedb"


class TestDoneGateValidationSourceCache:
    """When TypeDB is unreachable, validation_source should be 'cache'."""

    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_preload.get_typedb_client", return_value=None)
    def test_done_gate_typedb_unreachable_returns_validation_source_cache(
        self, mock_preload_client, mock_mut_client, mock_log, mock_audit,
    ):
        """DONE gate with TypeDB unreachable → response includes validation_source='cache'."""
        _seed_done_ready_task()

        result = update_task("T-DONE-001", status="DONE")

        assert result is not None
        assert result["status"] == "DONE"
        assert "validation_source" in result, (
            "DONE gate must include validation_source in response"
        )
        assert result["validation_source"] == "cache"

    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_preload.get_typedb_client", return_value=None)
    def test_done_gate_cache_missing_required_field_still_blocks(
        self, mock_preload_client, mock_mut_client, mock_log, mock_audit,
    ):
        """TypeDB unreachable + stale cache missing summary → ValueError raised."""
        task = _seed_done_ready_task(task_type="bug")
        task["summary"] = None  # Remove required field

        with pytest.raises(ValueError, match="DONE gate validation failed"):
            update_task("T-DONE-001", status="DONE")


class TestDoneGateCacheWarningLogged:
    """When validation uses cache, a WARNING must be logged with the task_id."""

    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_preload.get_typedb_client", return_value=None)
    def test_done_gate_cache_logs_warning(
        self, mock_preload_client, mock_mut_client, mock_log, mock_audit, caplog,
    ):
        """Cache fallback logs WARNING with task_id."""
        _seed_done_ready_task()

        with caplog.at_level(logging.WARNING, logger="governance.services.tasks_mutations"):
            update_task("T-DONE-001", status="DONE")

        cache_warnings = [r for r in caplog.records
                          if "validation_source" in r.message.lower()
                          or "cache" in r.message.lower()]
        assert len(cache_warnings) >= 1, (
            "Expected WARNING log when DONE gate uses cache data"
        )
        assert "T-DONE-001" in cache_warnings[0].message


class TestDoneGateValidationSourceNotSetForNonDone:
    """validation_source should only appear on DONE transitions."""

    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    def test_non_done_transition_has_no_validation_source(
        self, mock_client, mock_log, mock_audit,
    ):
        """IN_PROGRESS transition should NOT have validation_source."""
        _seed_done_ready_task()
        _tasks_store["T-DONE-001"]["status"] = "TODO"

        result = update_task("T-DONE-001", status="IN_PROGRESS")

        assert result is not None
        assert result.get("validation_source") is None, (
            "validation_source must only appear on DONE transitions"
        )
