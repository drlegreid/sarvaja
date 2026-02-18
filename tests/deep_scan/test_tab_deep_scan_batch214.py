"""Batch 214 — Tasks service defense tests.

Validates fixes for:
- BUG-214-003: List fields normalized to [] in fallback store
- BUG-214-008: _sessions_store iteration uses snapshot
- BUG-214-011: unlink_task_from_document in __all__
"""
from pathlib import Path
from unittest.mock import patch, MagicMock

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-214-003: List fields normalized to [] ────────────────────────

class TestTaskListFieldNormalization:
    """Fallback task_data must have [] not None for list fields."""

    def test_list_fields_not_none_in_source(self):
        """Source must use 'or []' for linked_rules, linked_sessions, linked_documents."""
        src = (SRC / "governance/services/tasks.py").read_text()
        assert "linked_rules or []" in src
        assert "linked_sessions or []" in src
        assert "linked_documents or []" in src

    def test_create_task_fallback_has_empty_lists(self):
        """When creating a task with no links, lists should be []."""
        from governance.services.tasks import create_task
        with patch("governance.services.tasks.get_typedb_client", return_value=None), \
             patch("governance.services.tasks._tasks_store", {}) as store, \
             patch("governance.services.tasks.record_audit"), \
             patch("governance.services.tasks.log_event"):
            result = create_task(
                task_id="TASK-TEST-001", description="Test",
                phase="TODO", status="TODO",
            )
        assert result["linked_rules"] == []
        assert result["linked_sessions"] == []
        assert result["linked_documents"] == []


# ── BUG-214-008: _sessions_store iteration snapshot ──────────────────

class TestSessionStoreSnapshot:
    """_get_active_session_id must use list() on _sessions_store.items()."""

    def test_snapshot_in_source(self):
        """Source must use list(_sessions_store.items())."""
        src = (SRC / "governance/services/tasks.py").read_text()
        assert "list(_sessions_store.items())" in src


# ── BUG-214-011: __all__ includes unlink_task_from_document ──────────

class TestMutationsAllExport:
    """tasks_mutations.__all__ must include unlink_task_from_document."""

    def test_unlink_in_all(self):
        from governance.services.tasks_mutations import __all__
        assert "unlink_task_from_document" in __all__

    def test_unlink_importable(self):
        from governance.services.tasks_mutations import unlink_task_from_document
        assert callable(unlink_task_from_document)


# ── Tasks service defense ────────────────────────────────────────────

class TestTasksServiceDefense:
    """Defense tests for tasks service module."""

    def test_create_task_callable(self):
        from governance.services.tasks import create_task
        assert callable(create_task)

    def test_get_task_callable(self):
        from governance.services.tasks import get_task
        assert callable(get_task)

    def test_list_tasks_callable(self):
        from governance.services.tasks import list_tasks
        assert callable(list_tasks)

    def test_update_task_callable(self):
        from governance.services.tasks import update_task
        assert callable(update_task)

    def test_delete_task_callable(self):
        from governance.services.tasks import delete_task
        assert callable(delete_task)

    def test_link_task_to_rule_callable(self):
        from governance.services.tasks import link_task_to_rule
        assert callable(link_task_to_rule)

    def test_create_task_rejects_duplicate(self):
        """Creating a task with existing ID should raise ValueError."""
        import pytest
        from governance.services.tasks import create_task
        store = {"TASK-DUP": {"task_id": "TASK-DUP"}}
        with patch("governance.services.tasks.get_typedb_client", return_value=None), \
             patch("governance.services.tasks._tasks_store", store):
            with pytest.raises(ValueError, match="already exists"):
                create_task(task_id="TASK-DUP", description="dup", phase="TODO", status="TODO")

    def test_get_active_session_id_returns_none_when_empty(self):
        from governance.services.tasks import _get_active_session_id
        with patch("governance.services.tasks._sessions_store", {}):
            result = _get_active_session_id()
        assert result is None

    def test_get_active_session_id_finds_active(self):
        from governance.services.tasks import _get_active_session_id
        store = {
            "S1": {"session_id": "S1", "status": "COMPLETED", "start_time": "2026-01-01"},
            "S2": {"session_id": "S2", "status": "ACTIVE", "start_time": "2026-02-01"},
        }
        with patch("governance.services.tasks._sessions_store", store):
            result = _get_active_session_id()
        assert result == "S2"


# ── Tasks mutations defense ──────────────────────────────────────────

class TestTasksMutationsDefense:
    """Defense tests for tasks_mutations module."""

    def test_update_task_nonexistent_returns_none(self):
        from governance.services.tasks_mutations import update_task
        with patch("governance.services.tasks_mutations.get_typedb_client", return_value=None), \
             patch("governance.services.tasks_mutations._tasks_store", {}):
            result = update_task("NONEXISTENT", status="DONE")
        assert result is None

    def test_update_task_sets_completed_at_on_done(self):
        from governance.services.tasks_mutations import update_task
        store = {"T1": {"task_id": "T1", "status": "TODO"}}
        with patch("governance.services.tasks_mutations.get_typedb_client", return_value=None), \
             patch("governance.services.tasks_mutations._tasks_store", store), \
             patch("governance.services.tasks_mutations.record_audit"), \
             patch("governance.services.tasks_mutations.log_event"):
            result = update_task("T1", status="DONE")
        assert result["completed_at"] is not None

    def test_update_task_auto_assigns_agent_for_in_progress(self):
        """H-TASK-002: IN_PROGRESS without agent_id gets 'code-agent'."""
        from governance.services.tasks_mutations import update_task
        store = {"T1": {"task_id": "T1", "status": "TODO"}}
        with patch("governance.services.tasks_mutations.get_typedb_client", return_value=None), \
             patch("governance.services.tasks_mutations._tasks_store", store), \
             patch("governance.services.tasks_mutations.record_audit"), \
             patch("governance.services.tasks_mutations.log_event"):
            result = update_task("T1", status="IN_PROGRESS")
        assert result["agent_id"] == "code-agent"
