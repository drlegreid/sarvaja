"""
Unit tests for Tasks CRUD Routes.

Per DOC-SIZE-01-v1: Tests for routes/tasks/crud.py module.
Tests: list_tasks, create_task, get_task, update_task, delete_task,
       link_task_to_rule, link_task_to_session.
"""

from unittest.mock import patch, MagicMock

import pytest
from fastapi import HTTPException

_P = "governance.routes.tasks.crud"
_SVC = f"{_P}.task_service"


# ── list_tasks ───────────────────────────────────────────────────


class TestListTasks:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.tasks.crud import list_tasks
        svc_result = {
            "items": [{"task_id": "T-1", "description": "d", "status": "OPEN", "phase": "VALIDATE"}],
            "total": 1, "offset": 0, "limit": 50, "has_more": False,
        }
        with patch(f"{_SVC}.list_tasks", return_value=svc_result):
            result = await list_tasks(
                offset=0, limit=50, sort_by="task_id", order="asc",
                phase=None, status=None, agent_id=None,
            )
        assert result.pagination.total == 1
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_typedb_unavailable(self):
        from governance.routes.tasks.crud import list_tasks
        from governance.stores import TypeDBUnavailable
        with patch(f"{_SVC}.list_tasks", side_effect=TypeDBUnavailable("no db")):
            with pytest.raises(HTTPException) as exc:
                await list_tasks(
                    offset=0, limit=50, sort_by="task_id", order="asc",
                    phase=None, status=None, agent_id=None,
                )
            assert exc.value.status_code == 503

    @pytest.mark.asyncio
    async def test_connection_error(self):
        from governance.routes.tasks.crud import list_tasks
        with patch(f"{_SVC}.list_tasks", side_effect=ConnectionError("no db")):
            with pytest.raises(HTTPException) as exc:
                await list_tasks(
                    offset=0, limit=50, sort_by="task_id", order="asc",
                    phase=None, status=None, agent_id=None,
                )
            assert exc.value.status_code == 503

    @pytest.mark.asyncio
    async def test_with_filters(self):
        from governance.routes.tasks.crud import list_tasks
        svc_result = {
            "items": [], "total": 0, "offset": 0, "limit": 10, "has_more": False,
        }
        with patch(f"{_SVC}.list_tasks", return_value=svc_result) as mock:
            await list_tasks(
                offset=0, limit=10, sort_by="task_id", order="desc",
                phase="IMPLEMENT", status="IN_PROGRESS", agent_id="code-agent",
            )
        mock.assert_called_once_with(
            status="IN_PROGRESS", phase="IMPLEMENT", agent_id="code-agent",
            sort_by="task_id", order="desc", offset=0, limit=10,
        )


# ── create_task ──────────────────────────────────────────────────


class TestCreateTask:
    @pytest.mark.asyncio
    async def test_success_dict(self):
        from governance.routes.tasks.crud import create_task
        from governance.models import TaskCreate
        data = {"task_id": "T-NEW", "description": "test", "status": "OPEN", "phase": "VALIDATE"}
        task = TaskCreate(task_id="T-NEW", description="test", phase="VALIDATE")
        with patch(f"{_SVC}.create_task", return_value=data):
            result = await create_task(task)
        assert result.task_id == "T-NEW"

    @pytest.mark.asyncio
    async def test_success_response_object(self):
        from governance.routes.tasks.crud import create_task
        from governance.models import TaskCreate, TaskResponse
        resp = TaskResponse(task_id="T-OBJ", description="t", status="OPEN", phase="VALIDATE")
        task = TaskCreate(task_id="T-OBJ", description="t", phase="VALIDATE")
        with patch(f"{_SVC}.create_task", return_value=resp):
            result = await create_task(task)
        assert result.task_id == "T-OBJ"

    @pytest.mark.asyncio
    async def test_conflict(self):
        from governance.routes.tasks.crud import create_task
        from governance.models import TaskCreate
        task = TaskCreate(task_id="T-DUP", description="dup", phase="VALIDATE")
        with patch(f"{_SVC}.create_task", side_effect=ValueError("exists")):
            with pytest.raises(HTTPException) as exc:
                await create_task(task)
            assert exc.value.status_code == 409


# ── get_task ─────────────────────────────────────────────────────


class TestGetTask:
    @pytest.mark.asyncio
    async def test_success_dict(self):
        from governance.routes.tasks.crud import get_task
        data = {"task_id": "T-1", "description": "d", "status": "OPEN", "phase": "VALIDATE"}
        with patch(f"{_SVC}.get_task", return_value=data):
            result = await get_task("T-1")
        assert result.task_id == "T-1"

    @pytest.mark.asyncio
    async def test_success_response_object(self):
        from governance.routes.tasks.crud import get_task
        from governance.models import TaskResponse
        resp = TaskResponse(task_id="T-1", description="d", status="OPEN", phase="VALIDATE")
        with patch(f"{_SVC}.get_task", return_value=resp):
            result = await get_task("T-1")
        assert result.task_id == "T-1"

    @pytest.mark.asyncio
    async def test_not_found(self):
        from governance.routes.tasks.crud import get_task
        with patch(f"{_SVC}.get_task", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await get_task("T-MISS")
            assert exc.value.status_code == 404


# ── update_task ──────────────────────────────────────────────────


class TestUpdateTask:
    @pytest.mark.asyncio
    async def test_success_dict(self):
        from governance.routes.tasks.crud import update_task
        from governance.models import TaskUpdate
        data = {"task_id": "T-1", "description": "updated", "status": "IN_PROGRESS", "phase": "IMPLEMENT"}
        update = TaskUpdate(description="updated", status="IN_PROGRESS")
        with patch(f"{_SVC}.update_task", return_value=data):
            result = await update_task("T-1", update)
        assert result.description == "updated"

    @pytest.mark.asyncio
    async def test_success_response_object(self):
        from governance.routes.tasks.crud import update_task
        from governance.models import TaskUpdate, TaskResponse
        resp = TaskResponse(task_id="T-1", description="up", status="DONE", phase="CERTIFY")
        update = TaskUpdate(status="DONE")
        with patch(f"{_SVC}.update_task", return_value=resp):
            result = await update_task("T-1", update)
        assert result.status == "DONE"

    @pytest.mark.asyncio
    async def test_not_found(self):
        from governance.routes.tasks.crud import update_task
        from governance.models import TaskUpdate
        update = TaskUpdate(status="DONE")
        with patch(f"{_SVC}.update_task", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await update_task("T-MISS", update)
            assert exc.value.status_code == 404


# ── delete_task ──────────────────────────────────────────────────


class TestDeleteTask:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.tasks.crud import delete_task
        with patch(f"{_SVC}.delete_task", return_value=True):
            result = await delete_task("T-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_not_found(self):
        from governance.routes.tasks.crud import delete_task
        with patch(f"{_SVC}.delete_task", return_value=False):
            with pytest.raises(HTTPException) as exc:
                await delete_task("T-MISS")
            assert exc.value.status_code == 404


# ── link_task_to_rule ────────────────────────────────────────────


class TestLinkTaskToRule:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.tasks.crud import link_task_to_rule
        with patch(f"{_SVC}.link_task_to_rule", return_value=True):
            result = await link_task_to_rule("T-1", "R-1")
        assert result["linked"] is True
        assert result["task_id"] == "T-1"
        assert result["rule_id"] == "R-1"

    @pytest.mark.asyncio
    async def test_failure(self):
        from governance.routes.tasks.crud import link_task_to_rule
        with patch(f"{_SVC}.link_task_to_rule", return_value=False):
            with pytest.raises(HTTPException) as exc:
                await link_task_to_rule("T-1", "R-1")
            assert exc.value.status_code == 400


# ── link_task_to_session ─────────────────────────────────────────


class TestLinkTaskToSession:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.tasks.crud import link_task_to_session
        with patch(f"{_SVC}.link_task_to_session", return_value=True):
            result = await link_task_to_session("T-1", "SESSION-1")
        assert result["linked"] is True
        assert result["session_id"] == "SESSION-1"

    @pytest.mark.asyncio
    async def test_failure(self):
        from governance.routes.tasks.crud import link_task_to_session
        with patch(f"{_SVC}.link_task_to_session", return_value=False):
            with pytest.raises(HTTPException) as exc:
                await link_task_to_session("T-1", "SESSION-1")
            assert exc.value.status_code == 400
