"""
Tests for BUG-TASK-UI-001: MCP-created tasks invisible in Dashboard.

Root cause: create_task() writes to TypeDB but NOT _tasks_store on success.
When TypeDB query later fails, fallback returns empty _tasks_store.
Also: get_all_tasks_from_typedb() does NOT merge orphan memory tasks (unlike sessions).

TDD: These tests define the fix contract.
Per DOC-SIZE-01-v1: <=300 lines.
"""

from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

_SVC = "governance.services.tasks"
_TDA = "governance.stores.typedb_access"


@pytest.fixture(autouse=True)
def _reset_stores():
    with patch(f"{_SVC}._tasks_store", {}) as tasks, \
         patch(f"{_SVC}.record_audit"), \
         patch(f"{_SVC}.log_event"):
        yield tasks, {}


def _make_task_entity(task_id, name="Test", status="OPEN", phase="P9",
                      priority="MEDIUM", task_type="chore"):
    """Create a mock Task entity matching TypeDB shape."""
    t = MagicMock()
    t.id = task_id
    t.name = name
    t.status = status
    t.phase = phase
    t.priority = priority
    t.task_type = task_type
    t.agent_id = None
    t.body = None
    t.description = name
    t.resolution = None
    t.gap_id = None
    t.evidence = None
    t.document_path = None
    t.linked_rules = []
    t.linked_sessions = []
    t.linked_commits = []
    t.linked_documents = []
    t.workspace_id = None
    t.created_at = datetime(2026, 3, 21, 10, 0, 0)
    t.claimed_at = None
    t.completed_at = None
    return t


# ── BUG-TASK-UI-001: MCP task must be cached in memory after TypeDB insert ──


class TestMCPTaskCachedInMemory:
    """After successful TypeDB insert, task MUST also be in _tasks_store."""

    def test_create_task_typedb_success_caches_in_memory(self, _reset_stores):
        """create_task() must write to _tasks_store even when TypeDB succeeds."""
        tasks_store, _ = _reset_stores
        mock_client = MagicMock()
        mock_client.get_task.return_value = None  # No duplicate
        mock_task = _make_task_entity("CHORE-005")
        mock_client.insert_task.return_value = mock_task

        with patch(f"{_SVC}.get_typedb_client", return_value=mock_client), \
             patch(f"{_SVC}._monitor"):
            from governance.services.tasks import create_task
            result = create_task(
                task_id="CHORE-005", description="Test chore",
                status="OPEN", phase="P9", task_type="chore",
                source="mcp",
            )

        assert result is not None
        # KEY ASSERTION: task must be cached in _tasks_store
        assert "CHORE-005" in tasks_store, \
            "MCP-created task not cached in _tasks_store — BUG-TASK-UI-001"

    def test_cached_task_has_required_fields(self, _reset_stores):
        """Cached task must have all fields needed by Dashboard."""
        tasks_store, _ = _reset_stores
        mock_client = MagicMock()
        mock_client.get_task.return_value = None
        mock_task = _make_task_entity("BUG-042", priority="HIGH", task_type="bug")
        mock_client.insert_task.return_value = mock_task

        with patch(f"{_SVC}.get_typedb_client", return_value=mock_client), \
             patch(f"{_SVC}._monitor"):
            from governance.services.tasks import create_task
            create_task(
                task_id="BUG-042", description="Critical bug",
                status="OPEN", phase="P9", priority="HIGH",
                task_type="bug", source="mcp",
            )

        cached = tasks_store.get("BUG-042", {})
        for field in ("task_id", "description", "status", "phase",
                      "priority", "task_type"):
            assert field in cached, f"Cached task missing field: {field}"


# ── BUG-TASK-UI-001: Orphan memory tasks must merge into TypeDB results ──


class TestOrphanTaskMerge:
    """get_all_tasks_from_typedb must merge orphan _tasks_store entries
    (tasks in memory but not in TypeDB results) — same pattern as sessions."""

    def test_memory_only_tasks_appear_in_typedb_results(self):
        """Tasks in _tasks_store but NOT in TypeDB results must be merged."""
        orphan = {
            "task_id": "ORPHAN-001", "description": "Memory only",
            "status": "OPEN", "phase": "P9", "priority": "LOW",
            "task_type": "chore",
        }
        typedb_task = _make_task_entity("TDB-001")

        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [typedb_task]

        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {"ORPHAN-001": orphan}):
            from governance.stores.typedb_access import get_all_tasks_from_typedb
            result = get_all_tasks_from_typedb(allow_fallback=True)

        task_ids = {t["task_id"] for t in result}
        assert "TDB-001" in task_ids
        assert "ORPHAN-001" in task_ids, \
            "Orphan memory task not merged into TypeDB results"

    def test_orphan_has_persistence_status(self):
        """Merged orphan tasks must have persistence_status='memory_only'."""
        orphan = {
            "task_id": "ORPHAN-002", "description": "Orphan",
            "status": "OPEN", "phase": "P9",
        }
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = []

        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {"ORPHAN-002": orphan}):
            from governance.stores.typedb_access import get_all_tasks_from_typedb
            result = get_all_tasks_from_typedb(allow_fallback=True)

        orphan_result = [t for t in result if t["task_id"] == "ORPHAN-002"]
        assert len(orphan_result) == 1
        assert orphan_result[0].get("persistence_status") == "memory_only"

    def test_no_duplicate_when_task_in_both(self):
        """Task existing in BOTH TypeDB and memory should NOT be duplicated."""
        mem_task = {
            "task_id": "DUP-001", "description": "In both",
            "status": "OPEN", "phase": "P9",
        }
        typedb_task = _make_task_entity("DUP-001")

        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [typedb_task]

        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {"DUP-001": mem_task}):
            from governance.stores.typedb_access import get_all_tasks_from_typedb
            result = get_all_tasks_from_typedb(allow_fallback=True)

        dup_results = [t for t in result if t["task_id"] == "DUP-001"]
        assert len(dup_results) == 1, "Duplicate task detected"

    def test_orphan_filters_apply(self):
        """Orphan tasks must respect filter params (status, phase)."""
        orphan_open = {
            "task_id": "O-OPEN", "description": "Open",
            "status": "OPEN", "phase": "P9",
        }
        orphan_done = {
            "task_id": "O-DONE", "description": "Done",
            "status": "DONE", "phase": "P9",
        }
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = []

        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {
                 "O-OPEN": orphan_open, "O-DONE": orphan_done,
             }):
            from governance.stores.typedb_access import get_all_tasks_from_typedb
            result = get_all_tasks_from_typedb(status="OPEN", allow_fallback=True)

        task_ids = {t["task_id"] for t in result}
        assert "O-OPEN" in task_ids
        assert "O-DONE" not in task_ids


# ── Data flow: list_tasks returns TypeDB data ──


class TestListTasksDataFlow:
    """Verify list_tasks service returns TypeDB-sourced data."""

    def test_list_tasks_uses_typedb(self, _reset_stores):
        """list_tasks must get data from TypeDB, not just _tasks_store."""
        typedb_task = _make_task_entity("TDB-ONLY")
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [typedb_task]

        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks()

        items = result["items"]
        assert any(t["task_id"] == "TDB-ONLY" for t in items)

    def test_list_tasks_includes_priority_and_type(self, _reset_stores):
        """list_tasks results must include priority and task_type fields."""
        typedb_task = _make_task_entity("T-1", priority="HIGH", task_type="bug")
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [typedb_task]

        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks()

        item = result["items"][0]
        assert item.get("priority") == "HIGH"
        assert item.get("task_type") == "bug"
