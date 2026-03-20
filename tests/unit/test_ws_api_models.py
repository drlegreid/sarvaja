"""TDD tests for Phase 6b: BUG-WS-API-001 — Pydantic model + route fixes.

Covers:
- TaskCreate model accepts workspace_id
- TaskUpdate model accepts workspace_id
- POST /tasks route passes workspace_id to service
- PUT /tasks/{id} route passes workspace_id to service

Per EPIC-GOV-TASKS-V2 Phase 6b, TEST-GUARD-01.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestBugWsApi001Models:
    """TaskCreate and TaskUpdate Pydantic models must accept workspace_id."""

    def test_task_create_accepts_workspace_id(self):
        """TaskCreate model must have optional workspace_id field."""
        from governance.models import TaskCreate

        task = TaskCreate(
            description="Test task",
            phase="P1",
            workspace_id="WS-123",
        )
        assert task.workspace_id == "WS-123"

    def test_task_create_workspace_id_defaults_none(self):
        """TaskCreate.workspace_id defaults to None when omitted."""
        from governance.models import TaskCreate

        task = TaskCreate(
            description="Test task",
            phase="P1",
        )
        assert task.workspace_id is None

    def test_task_update_accepts_workspace_id(self):
        """TaskUpdate model must have optional workspace_id field."""
        from governance.models import TaskUpdate

        update = TaskUpdate(workspace_id="WS-456")
        assert update.workspace_id == "WS-456"

    def test_task_update_workspace_id_defaults_none(self):
        """TaskUpdate.workspace_id defaults to None when omitted."""
        from governance.models import TaskUpdate

        update = TaskUpdate()
        assert update.workspace_id is None

    def test_task_response_has_workspace_id(self):
        """TaskResponse already has workspace_id (no change needed)."""
        from governance.models import TaskResponse

        resp = TaskResponse(
            task_id="FEAT-001",
            description="Test",
            phase="P1",
            status="OPEN",
            workspace_id="WS-789",
        )
        assert resp.workspace_id == "WS-789"


class TestBugWsApi001Routes:
    """REST API routes must pass workspace_id to service layer."""

    @pytest.fixture
    def client(self):
        """FastAPI test client for task routes."""
        from fastapi.testclient import TestClient
        from governance.routes.tasks.crud import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api")
        return TestClient(app)

    @patch("governance.routes.tasks.crud.task_service")
    def test_post_tasks_passes_workspace_id(self, mock_svc, client):
        """POST /api/tasks with workspace_id passes it to service.create_task."""
        from governance.models import TaskResponse

        mock_svc.create_task.return_value = TaskResponse(
            task_id="FEAT-050",
            description="With workspace",
            phase="P1",
            status="TODO",
            workspace_id="WS-ABC",
        )

        resp = client.post("/api/tasks", json={
            "description": "With workspace",
            "phase": "P1",
            "workspace_id": "WS-ABC",
        })

        assert resp.status_code == 201
        # Verify workspace_id was passed to service
        call_kwargs = mock_svc.create_task.call_args
        assert call_kwargs.kwargs.get("workspace_id") == "WS-ABC"

    @patch("governance.routes.tasks.crud.task_service")
    def test_post_tasks_without_workspace_id_passes_none(self, mock_svc, client):
        """POST /api/tasks without workspace_id passes None."""
        from governance.models import TaskResponse

        mock_svc.create_task.return_value = TaskResponse(
            task_id="FEAT-051",
            description="No workspace",
            phase="P1",
            status="TODO",
        )

        resp = client.post("/api/tasks", json={
            "description": "No workspace",
            "phase": "P1",
        })

        assert resp.status_code == 201
        call_kwargs = mock_svc.create_task.call_args
        assert call_kwargs.kwargs.get("workspace_id") is None

    @patch("governance.routes.tasks.crud.task_service")
    def test_put_tasks_passes_workspace_id(self, mock_svc, client):
        """PUT /api/tasks/{id} with workspace_id passes it to service.update_task."""
        from governance.models import TaskResponse

        mock_svc.update_task.return_value = TaskResponse(
            task_id="FEAT-060",
            description="Updated",
            phase="P1",
            status="OPEN",
            workspace_id="WS-DEF",
        )

        resp = client.put("/api/tasks/FEAT-060", json={
            "workspace_id": "WS-DEF",
        })

        assert resp.status_code == 200
        call_kwargs = mock_svc.update_task.call_args
        assert call_kwargs.kwargs.get("workspace_id") == "WS-DEF"

    @patch("governance.routes.tasks.crud.task_service")
    def test_put_tasks_without_workspace_id_passes_none(self, mock_svc, client):
        """PUT /api/tasks/{id} without workspace_id passes None."""
        from governance.models import TaskResponse

        mock_svc.update_task.return_value = TaskResponse(
            task_id="FEAT-061",
            description="No ws update",
            phase="P1",
            status="OPEN",
        )

        resp = client.put("/api/tasks/FEAT-061", json={
            "status": "IN_PROGRESS",
        })

        assert resp.status_code == 200
        call_kwargs = mock_svc.update_task.call_args
        assert call_kwargs.kwargs.get("workspace_id") is None

    @patch("governance.routes.tasks.crud.task_service")
    def test_post_response_includes_workspace_id(self, mock_svc, client):
        """POST response body must include workspace_id."""
        from governance.models import TaskResponse

        mock_svc.create_task.return_value = TaskResponse(
            task_id="FEAT-070",
            description="Response check",
            phase="P1",
            status="TODO",
            workspace_id="WS-XYZ",
        )

        resp = client.post("/api/tasks", json={
            "description": "Response check",
            "phase": "P1",
            "workspace_id": "WS-XYZ",
        })

        assert resp.status_code == 201
        assert resp.json()["workspace_id"] == "WS-XYZ"


class TestBugWsApi001WorkspaceDetailUI:
    """Workspace detail view linked tasks component tests."""

    def test_linked_tasks_module_exists(self):
        """Linked tasks UI component must be importable."""
        from agent.governance_ui.views.workspaces.linked_tasks import (
            build_workspace_linked_tasks,
        )
        assert callable(build_workspace_linked_tasks)

    def test_detail_view_module_importable(self):
        """Workspace detail view must still be importable after changes."""
        from agent.governance_ui.views.workspaces.detail import (
            build_workspace_detail_view,
        )
        assert callable(build_workspace_detail_view)
