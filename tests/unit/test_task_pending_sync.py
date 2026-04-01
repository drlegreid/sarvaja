"""Tests for sync_pending_tasks() — P4 Pending Task Sync.

Per EPIC-TASK-WORKFLOW-HEAL-01 P4 / SRVJ-BUG-DUAL-WRITE-01:
Tasks created when TypeDB is down are stored in _tasks_store as
memory_only. sync_pending_tasks() retries them to TypeDB.

TDD RED phase: These tests MUST fail before implementation.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_stores():
    """Reset _tasks_store between tests."""
    from governance.stores import _tasks_store
    _tasks_store.clear()
    yield
    _tasks_store.clear()


@pytest.fixture
def mock_typedb_client():
    """A controllable mock TypeDB client."""
    from governance.typedb.entities import Task as TypeDBTask
    client = MagicMock()
    client.get_task.return_value = None
    client.insert_task.return_value = TypeDBTask(
        id="SRVJ-BUG-PER-001", name="Persisted task", status="OPEN",
        phase="P10", agent_id=None, created_at=datetime.now(),
        body=None, gap_id=None, priority="MEDIUM", task_type="bug",
        linked_rules=[], linked_sessions=[], linked_commits=[],
        linked_documents=[], workspace_id=None, evidence=None,
        document_path=None, resolution="NONE", claimed_at=None,
        completed_at=None, summary=None, resolution_notes=None,
        layer=None, concern=None, method=None,
    )
    return client


# ---------------------------------------------------------------------------
# 1. create_task with TypeDB DOWN → persistence_status = "memory_only"
# ---------------------------------------------------------------------------

class TestCreateTaskPersistenceStatus:
    """Verify create_task sets persistence_status on both paths."""

    @patch("governance.services.tasks.get_typedb_client", return_value=None)
    def test_create_task_typedb_down_sets_memory_only(self, _mock_client):
        """When TypeDB is unavailable, task must be stored with persistence_status='memory_only'."""
        from governance.services.tasks import create_task
        from governance.stores import _tasks_store

        result = create_task(
            task_id="SRVJ-BUG-MEM-001",
            description="Memory-only task",
            status="OPEN",
            task_type="bug",
        )
        assert "SRVJ-BUG-MEM-001" in _tasks_store
        assert _tasks_store["SRVJ-BUG-MEM-001"]["persistence_status"] == "memory_only"

    @patch("governance.services.tasks.get_typedb_client")
    def test_create_task_typedb_up_sets_persisted(self, mock_get_client, mock_typedb_client):
        """When TypeDB succeeds, task must be stored with persistence_status='persisted'."""
        mock_get_client.return_value = mock_typedb_client
        mock_typedb_client.get_task.return_value = None  # no duplicate

        from governance.services.tasks import create_task
        from governance.stores import _tasks_store

        create_task(
            task_id="SRVJ-BUG-PER-001",
            description="Persisted task",
            status="OPEN",
            task_type="bug",
        )
        assert "SRVJ-BUG-PER-001" in _tasks_store
        assert _tasks_store["SRVJ-BUG-PER-001"]["persistence_status"] == "persisted"


# ---------------------------------------------------------------------------
# 2. sync_pending_tasks() behavior
# ---------------------------------------------------------------------------

class TestSyncPendingTasks:
    """Verify sync_pending_tasks() retries memory-only tasks to TypeDB."""

    def _seed_task(self, task_id, persistence_status="memory_only"):
        """Insert a task directly into _tasks_store for testing."""
        from governance.stores import _tasks_store
        _tasks_store[task_id] = {
            "task_id": task_id,
            "description": f"Test task {task_id}",
            "phase": "P10",
            "status": "OPEN",
            "priority": "MEDIUM",
            "task_type": "bug",
            "agent_id": None,
            "body": None,
            "summary": None,
            "linked_rules": [],
            "linked_sessions": [],
            "linked_documents": [],
            "gap_id": None,
            "workspace_id": None,
            "layer": None,
            "concern": None,
            "method": None,
            "created_at": datetime.now().isoformat(),
            "persistence_status": persistence_status,
        }

    @patch("governance.services.tasks.get_typedb_client", return_value=None)
    def test_sync_returns_error_when_typedb_down(self, _mock):
        """sync_pending_tasks with TypeDB unavailable returns error dict."""
        from governance.services.tasks import sync_pending_tasks
        result = sync_pending_tasks()
        assert result["error"] == "TypeDB unavailable"
        assert result["synced"] == 0
        assert result["failed"] == 0

    @patch("governance.services.tasks.get_typedb_client")
    def test_sync_two_memory_only_tasks(self, mock_get_client):
        """Two memory_only tasks → both attempted, both synced on success."""
        client = MagicMock()
        client.get_task.return_value = None  # not in TypeDB yet
        client.insert_task.return_value = True
        mock_get_client.return_value = client

        self._seed_task("TST-SYNC-001", "memory_only")
        self._seed_task("TST-SYNC-002", "memory_only")

        from governance.services.tasks import sync_pending_tasks
        from governance.stores import _tasks_store

        result = sync_pending_tasks()
        assert result["synced"] == 2
        assert result["failed"] == 0
        # Both should now be marked "persisted"
        assert _tasks_store["TST-SYNC-001"]["persistence_status"] == "persisted"
        assert _tasks_store["TST-SYNC-002"]["persistence_status"] == "persisted"

    @patch("governance.services.tasks.get_typedb_client")
    def test_sync_partial_failure(self, mock_get_client):
        """One succeeds, one fails → partial result, correct status updates."""
        client = MagicMock()
        client.get_task.return_value = None

        def insert_side_effect(**kwargs):
            if kwargs.get("task_id") == "TST-SYNC-OK":
                return True
            raise ConnectionError("TypeDB write failed")

        client.insert_task.side_effect = insert_side_effect
        mock_get_client.return_value = client

        self._seed_task("TST-SYNC-OK", "memory_only")
        self._seed_task("TST-SYNC-FAIL", "memory_only")

        from governance.services.tasks import sync_pending_tasks
        from governance.stores import _tasks_store

        result = sync_pending_tasks()
        assert result["synced"] == 1
        assert result["failed"] == 1
        assert _tasks_store["TST-SYNC-OK"]["persistence_status"] == "persisted"
        assert _tasks_store["TST-SYNC-FAIL"]["persistence_status"] == "memory_only"

    @patch("governance.services.tasks.get_typedb_client")
    def test_sync_skips_already_persisted(self, mock_get_client):
        """Tasks with persistence_status='persisted' are skipped (not re-inserted)."""
        client = MagicMock()
        mock_get_client.return_value = client

        self._seed_task("TST-ALREADY", "persisted")

        from governance.services.tasks import sync_pending_tasks

        result = sync_pending_tasks()
        assert result["synced"] == 0
        assert result["failed"] == 0
        assert result["already_persisted"] == 1
        # insert_task should NOT have been called
        client.insert_task.assert_not_called()

    @patch("governance.services.tasks.get_typedb_client")
    def test_sync_no_pending_is_noop(self, mock_get_client):
        """Empty _tasks_store → no-op, no errors."""
        client = MagicMock()
        mock_get_client.return_value = client

        from governance.services.tasks import sync_pending_tasks

        result = sync_pending_tasks()
        assert result["synced"] == 0
        assert result["failed"] == 0
        assert result.get("already_persisted", 0) == 0
        client.insert_task.assert_not_called()

    @patch("governance.services.tasks.get_typedb_client")
    def test_sync_already_in_typedb_marks_persisted(self, mock_get_client):
        """Task in _tasks_store as memory_only but already exists in TypeDB
        → marks as persisted without re-inserting."""
        client = MagicMock()
        client.get_task.return_value = MagicMock(task_id="TST-DUP")  # already in TypeDB
        mock_get_client.return_value = client

        self._seed_task("TST-DUP", "memory_only")

        from governance.services.tasks import sync_pending_tasks
        from governance.stores import _tasks_store

        result = sync_pending_tasks()
        assert result["already_persisted"] == 1
        assert result["synced"] == 0
        assert _tasks_store["TST-DUP"]["persistence_status"] == "persisted"
        client.insert_task.assert_not_called()

    @patch("governance.services.tasks.get_typedb_client")
    def test_sync_no_persistence_status_field_treated_as_memory_only(self, mock_get_client):
        """Legacy tasks without persistence_status field are treated as needing sync."""
        client = MagicMock()
        client.get_task.return_value = None
        client.insert_task.return_value = True
        mock_get_client.return_value = client

        from governance.stores import _tasks_store
        # Manually insert WITHOUT persistence_status (legacy)
        _tasks_store["TST-LEGACY"] = {
            "task_id": "TST-LEGACY",
            "description": "Legacy task",
            "phase": "P10", "status": "OPEN",
            "priority": "MEDIUM", "task_type": "bug",
            "agent_id": None, "body": None, "summary": None,
            "linked_rules": [], "linked_sessions": [],
            "linked_documents": [], "gap_id": None,
            "workspace_id": None, "layer": None,
            "concern": None, "method": None,
            "created_at": datetime.now().isoformat(),
        }

        from governance.services.tasks import sync_pending_tasks

        result = sync_pending_tasks()
        assert result["synced"] == 1
        assert _tasks_store["TST-LEGACY"]["persistence_status"] == "persisted"
