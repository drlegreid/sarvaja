"""TDD tests for Phase 6b: Task-Workspace Linking Bugfixes.

Covers:
- BUG-WS-CREATE-001: Transaction rollback fix (workspace link in separate TX)
- BUG-STATUS-CASE-001: Status case normalization
- GAP-WS-TASKS-API: GET /api/workspaces/{id}/tasks endpoint

Per EPIC-GOV-TASKS-V2 Phase 6b, TEST-GUARD-01.
"""

import pytest
from unittest.mock import patch, MagicMock


# ── BUG-WS-CREATE-001: Transaction rollback fix ──────────────────────


class TestBugWsCreate001:
    """MCP task_create with workspace_id must NOT roll back the task insert
    when workspace doesn't exist in TypeDB."""

    @patch("governance.typedb.queries.tasks.crud.logger")
    def test_insert_task_with_nonexistent_workspace_still_creates_task(self, mock_logger):
        """CRITICAL: Task insert must commit even if workspace link fails."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations

        crud = TaskCRUDOperations.__new__(TaskCRUDOperations)
        crud.database = "test-db"

        mock_driver = MagicMock()
        crud._driver = mock_driver

        mock_tx = MagicMock()
        mock_driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        mock_driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        mock_task = MagicMock()
        mock_task.task_id = "FEAT-001"
        mock_task.name = "Test task"
        mock_task.status = "OPEN"
        crud.get_task = MagicMock(return_value=mock_task)
        crud.link_task_to_workspace = MagicMock(return_value=False)

        result = crud.insert_task(
            task_id="FEAT-001",
            name="Test task",
            status="OPEN",
            phase="P1",
            workspace_id="WS-NONEXISTENT",
        )

        assert result is not None
        assert result.task_id == "FEAT-001"
        mock_tx.commit.assert_called_once()

    @patch("governance.typedb.queries.tasks.crud.logger")
    def test_insert_task_with_valid_workspace_links_successfully(self, mock_logger):
        """When workspace exists, task is created AND linked."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations

        crud = TaskCRUDOperations.__new__(TaskCRUDOperations)
        crud.database = "test-db"

        mock_driver = MagicMock()
        crud._driver = mock_driver

        mock_tx = MagicMock()
        mock_driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        mock_driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        mock_task = MagicMock()
        mock_task.task_id = "FEAT-002"
        crud.get_task = MagicMock(return_value=mock_task)
        crud.link_task_to_workspace = MagicMock(return_value=True)

        result = crud.insert_task(
            task_id="FEAT-002",
            name="Linked task",
            status="OPEN",
            phase="P1",
            workspace_id="WS-VALID",
        )

        assert result is not None
        crud.link_task_to_workspace.assert_called_once_with("WS-VALID", "FEAT-002")

    @patch("governance.typedb.queries.tasks.crud.logger")
    def test_insert_task_without_workspace_id_skips_linking(self, mock_logger):
        """No workspace_id -> no link attempt."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations

        crud = TaskCRUDOperations.__new__(TaskCRUDOperations)
        crud.database = "test-db"

        mock_driver = MagicMock()
        crud._driver = mock_driver

        mock_tx = MagicMock()
        mock_driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        mock_driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        mock_task = MagicMock()
        mock_task.task_id = "FEAT-003"
        crud.get_task = MagicMock(return_value=mock_task)
        crud.link_task_to_workspace = MagicMock()

        crud.insert_task(
            task_id="FEAT-003",
            name="No workspace",
            status="OPEN",
            phase="P1",
        )

        crud.link_task_to_workspace.assert_not_called()

    @patch("governance.typedb.queries.tasks.crud.logger")
    def test_workspace_link_failure_logged_as_warning(self, mock_logger):
        """Failed workspace link should warn, not error (task still created)."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations

        crud = TaskCRUDOperations.__new__(TaskCRUDOperations)
        crud.database = "test-db"

        mock_driver = MagicMock()
        crud._driver = mock_driver

        mock_tx = MagicMock()
        mock_driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        mock_driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        mock_task = MagicMock()
        mock_task.task_id = "FEAT-004"
        crud.get_task = MagicMock(return_value=mock_task)
        crud.link_task_to_workspace = MagicMock(return_value=False)

        result = crud.insert_task(
            task_id="FEAT-004",
            name="Link fails",
            status="OPEN",
            phase="P1",
            workspace_id="WS-MISSING",
        )

        assert result is not None
        assert result.task_id == "FEAT-004"


class TestBugWsCreate001ServiceLayer:
    """Service layer must pass workspace_id through and handle link failure."""

    @patch("governance.services.tasks._tasks_store", {})
    @patch("governance.services.tasks.get_typedb_client")
    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks.log_event")
    def test_create_task_service_passes_workspace_id(
        self, mock_log, mock_audit, mock_client_fn
    ):
        """Service layer must pass workspace_id to TypeDB insert_task."""
        from governance.services.tasks import create_task
        from governance.typedb.entities import Task

        mock_client = MagicMock()
        mock_client.get_task.return_value = None
        # Use a proper Task entity so task_to_response works
        mock_task = Task(
            id="FEAT-010", name="Test", description="Test",
            status="OPEN", phase="P1", workspace_id="WS-ABC",
        )
        mock_client.insert_task.return_value = mock_task
        mock_client_fn.return_value = mock_client

        result = create_task(
            task_id="FEAT-010",
            description="Test",
            workspace_id="WS-ABC",
        )

        mock_client.insert_task.assert_called_once()
        call_kwargs = mock_client.insert_task.call_args.kwargs
        assert call_kwargs.get("workspace_id") == "WS-ABC"


# ── BUG-STATUS-CASE-001: Status case normalization ───────────────────


class TestBugStatusCase001:
    """Status values must be normalized to uppercase in service layer."""

    @patch("governance.services.tasks._tasks_store", {})
    @patch("governance.services.tasks.get_typedb_client", return_value=None)
    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks.log_event")
    def test_create_task_normalizes_lowercase_status(
        self, mock_log, mock_audit, mock_client
    ):
        """create_task('in_progress') should store 'IN_PROGRESS'."""
        from governance.services.tasks import create_task

        result = create_task(
            task_id="BUG-100",
            description="Test lowercase",
            status="in_progress",
        )

        assert result["status"] == "IN_PROGRESS"

    @patch("governance.services.tasks._tasks_store", {})
    @patch("governance.services.tasks.get_typedb_client", return_value=None)
    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks.log_event")
    def test_create_task_normalizes_mixed_case_status(
        self, mock_log, mock_audit, mock_client
    ):
        """create_task('Open') should store 'OPEN'."""
        from governance.services.tasks import create_task

        result = create_task(
            task_id="BUG-101",
            description="Test mixed case",
            status="Open",
        )

        assert result["status"] == "OPEN"

    @patch("governance.services.tasks._tasks_store", {})
    @patch("governance.services.tasks.get_typedb_client", return_value=None)
    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks.log_event")
    def test_create_task_preserves_already_uppercase_status(
        self, mock_log, mock_audit, mock_client
    ):
        """create_task('DONE') should stay 'DONE'."""
        from governance.services.tasks import create_task

        result = create_task(
            task_id="BUG-102",
            description="Already uppercase",
            status="DONE",
        )

        assert result["status"] == "DONE"

    @patch("governance.services.tasks_mutations._tasks_store", {"BUG-200": {
        "task_id": "BUG-200", "description": "Existing", "phase": "P1",
        "status": "OPEN", "agent_id": None, "created_at": "2026-01-01",
        "linked_rules": [], "linked_sessions": [], "linked_documents": [],
    }})
    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_update_task_normalizes_lowercase_status(
        self, mock_log, mock_audit, mock_client
    ):
        """update_task(status='in_progress') should store 'IN_PROGRESS'."""
        from governance.services.tasks_mutations import update_task

        result = update_task(
            task_id="BUG-200",
            status="in_progress",
        )

        assert result is not None
        assert result["status"] == "IN_PROGRESS"

    @patch("governance.services.tasks_mutations._tasks_store", {"BUG-201": {
        "task_id": "BUG-201", "description": "Existing", "phase": "P1",
        "status": "TODO", "agent_id": None, "created_at": "2026-01-01",
        "linked_rules": [], "linked_sessions": [], "linked_documents": [],
    }})
    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_update_task_normalizes_pending_to_open(
        self, mock_log, mock_audit, mock_client
    ):
        """update_task(status='pending') should store 'PENDING'."""
        from governance.services.tasks_mutations import update_task

        result = update_task(
            task_id="BUG-201",
            status="pending",
        )

        assert result is not None
        assert result["status"] == "PENDING"


# ── GAP-WS-TASKS-API: GET /api/workspaces/{id}/tasks ─────────────────


class TestGapWsTasksApi:
    """New endpoint GET /api/workspaces/{workspace_id}/tasks."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        from fastapi.testclient import TestClient
        from governance.routes.workspaces.crud import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api")
        return TestClient(app)

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_get_workspace_tasks_returns_list(self, mock_svc, client):
        """GET /api/workspaces/{id}/tasks returns linked tasks."""
        mock_svc.get_workspace_tasks.return_value = {
            "items": [
                {"task_id": "FEAT-001", "description": "Task A", "status": "OPEN",
                 "phase": "P1"},
                {"task_id": "BUG-001", "description": "Task B", "status": "DONE",
                 "phase": "P2"},
            ],
            "total": 2,
        }

        resp = client.get("/api/workspaces/WS-123/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_get_workspace_tasks_empty(self, mock_svc, client):
        """GET /api/workspaces/{id}/tasks returns empty list when no tasks."""
        mock_svc.get_workspace_tasks.return_value = {
            "items": [],
            "total": 0,
        }

        resp = client.get("/api/workspaces/WS-EMPTY/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_get_workspace_tasks_404_when_workspace_missing(self, mock_svc, client):
        """GET /api/workspaces/{id}/tasks returns 404 if workspace not found."""
        mock_svc.get_workspace_tasks.return_value = None

        resp = client.get("/api/workspaces/WS-GONE/tasks")
        assert resp.status_code == 404

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_get_workspace_tasks_pagination(self, mock_svc, client):
        """GET /api/workspaces/{id}/tasks supports offset/limit."""
        mock_svc.get_workspace_tasks.return_value = {
            "items": [
                {"task_id": "FEAT-005", "description": "Task E", "status": "OPEN",
                 "phase": "P1"},
            ],
            "total": 10,
        }

        resp = client.get("/api/workspaces/WS-123/tasks?offset=4&limit=1")
        assert resp.status_code == 200
        mock_svc.get_workspace_tasks.assert_called_once_with(
            "WS-123", offset=4, limit=1,
        )


class TestGapWsTasksService:
    """Workspace service get_workspace_tasks method."""

    @patch("governance.services.workspaces._get_typedb_client")
    def test_get_workspace_tasks_from_typedb(self, mock_client_fn):
        """get_workspace_tasks queries TypeDB workspace-has-task relation."""
        from governance.services.workspaces import get_workspace_tasks
        from governance.typedb.entities import Task

        mock_client = MagicMock()
        mock_client.get_tasks_for_workspace.return_value = ["FEAT-001", "BUG-002"]
        mock_client.get_task.side_effect = [
            Task(
                id="FEAT-001", name="Task A", status="OPEN", phase="P1",
                workspace_id="WS-123",
            ),
            Task(
                id="BUG-002", name="Task B", status="DONE", phase="P2",
                priority="HIGH", task_type="bug", agent_id="code-agent",
                workspace_id="WS-123",
            ),
        ]
        mock_client_fn.return_value = mock_client

        result = get_workspace_tasks("WS-123")

        assert result is not None
        assert result["total"] == 2
        assert len(result["items"]) == 2

    @patch("governance.services.workspaces._get_typedb_client", return_value=None)
    def test_get_workspace_tasks_no_client_returns_empty(self, mock_client):
        """No TypeDB client -> empty result."""
        from governance.services.workspaces import get_workspace_tasks

        result = get_workspace_tasks("WS-123")

        assert result is not None
        assert result["total"] == 0
        assert result["items"] == []
