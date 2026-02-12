"""
Unit tests for Tasks Workflow Routes.

Per DOC-SIZE-01-v1: Tests for routes/tasks/workflow.py module.
Tests: list_available_tasks, claim_task, complete_task, promote_task_resolution.
"""

from unittest.mock import patch, MagicMock

import pytest

from governance.models import TaskResponse


_P_CLIENT = "governance.routes.tasks.workflow.get_typedb_client"
_P_STORE = "governance.routes.tasks.workflow._tasks_store"
_P_AGENTS = "governance.routes.tasks.workflow._agents_store"
_P_TO_RESP = "governance.routes.tasks.workflow.task_to_response"
_P_HELPERS = "governance.routes.tasks.workflow"


def _make_task_obj(task_id="T-1", status="TODO", agent_id=None,
                   resolution="NONE", evidence=None):
    t = MagicMock()
    t.id = task_id
    t.status = status
    t.agent_id = agent_id
    t.resolution = resolution
    t.evidence = evidence
    t.name = "Test Task"
    t.phase = "P1"
    return t


def _make_response(**kwargs):
    defaults = {
        "task_id": "T-1",
        "description": "Test",
        "phase": "P1",
        "status": "TODO",
    }
    defaults.update(kwargs)
    return TaskResponse(**defaults)


class TestListAvailableTasks:
    @pytest.mark.asyncio
    async def test_from_typedb(self):
        client = MagicMock()
        client.get_available_tasks.return_value = [_make_task_obj()]
        resp = _make_response()

        with patch(_P_CLIENT, return_value=client), \
             patch(_P_TO_RESP, return_value=resp):
            from governance.routes.tasks.workflow import list_available_tasks
            result = await list_available_tasks()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_fallback_to_memory(self):
        store = {
            "T-1": {"task_id": "T-1", "description": "Test", "phase": "P1",
                     "status": "TODO", "agent_id": None},
            "T-2": {"task_id": "T-2", "description": "Claimed", "phase": "P1",
                     "status": "TODO", "agent_id": "agent-1"},
        }
        with patch(_P_CLIENT, return_value=None), \
             patch(_P_STORE, store):
            from governance.routes.tasks.workflow import list_available_tasks
            result = await list_available_tasks()
        # T-2 has agent_id, so only T-1 is available
        assert len(result) == 1


class TestClaimTask:
    @pytest.mark.asyncio
    async def test_typedb_success(self):
        client = MagicMock()
        client.get_task.return_value = _make_task_obj()
        client.update_task_status.return_value = _make_task_obj(status="IN_PROGRESS")
        resp = _make_response(status="IN_PROGRESS")

        with patch(_P_CLIENT, return_value=client), \
             patch(_P_TO_RESP, return_value=resp), \
             patch(f"{_P_HELPERS}._update_agent_metrics_on_claim"), \
             patch(f"{_P_HELPERS}.try_link_task_to_session"):
            from governance.routes.tasks.workflow import claim_task
            result = await claim_task("T-1", agent_id="agent-1")
        assert result.status == "IN_PROGRESS"

    @pytest.mark.asyncio
    async def test_already_claimed(self):
        from fastapi import HTTPException
        client = MagicMock()
        client.get_task.return_value = _make_task_obj(agent_id="other-agent")

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.tasks.workflow import claim_task
            with pytest.raises(HTTPException) as exc_info:
                await claim_task("T-1", agent_id="agent-1")
            assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_not_found(self):
        from fastapi import HTTPException
        client = MagicMock()
        client.get_task.return_value = None

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.tasks.workflow import claim_task
            with pytest.raises(HTTPException) as exc_info:
                await claim_task("NONEXISTENT", agent_id="agent-1")
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_wrong_status(self):
        from fastapi import HTTPException
        client = MagicMock()
        client.get_task.return_value = _make_task_obj(status="IN_PROGRESS")

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.tasks.workflow import claim_task
            with pytest.raises(HTTPException) as exc_info:
                await claim_task("T-1", agent_id="agent-1")
            assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_fallback_claim(self):
        store = {
            "T-1": {"task_id": "T-1", "description": "Test", "phase": "P1",
                     "status": "TODO", "agent_id": None},
        }
        with patch(_P_CLIENT, return_value=None), \
             patch(_P_STORE, store), \
             patch(_P_AGENTS, {}), \
             patch(f"{_P_HELPERS}.update_agent_metrics_on_claim_fallback"):
            from governance.routes.tasks.workflow import claim_task
            result = await claim_task("T-1", agent_id="agent-1")
        assert result.status == "IN_PROGRESS"


class TestCompleteTask:
    @pytest.mark.asyncio
    async def test_typedb_success(self):
        client = MagicMock()
        client.get_task.return_value = _make_task_obj(status="IN_PROGRESS",
                                                       agent_id="agent-1")
        client.update_task_status.return_value = _make_task_obj(status="DONE")
        resp = _make_response(status="DONE")

        with patch(_P_CLIENT, return_value=client), \
             patch(_P_TO_RESP, return_value=resp), \
             patch(f"{_P_HELPERS}.try_link_task_to_session"), \
             patch(f"{_P_HELPERS}.record_completion_audit"):
            from governance.routes.tasks.workflow import complete_task
            result = await complete_task("T-1", evidence="Fixed it")
        assert result.status == "DONE"

    @pytest.mark.asyncio
    async def test_already_completed(self):
        from fastapi import HTTPException
        client = MagicMock()
        client.get_task.return_value = _make_task_obj(status="DONE")

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.tasks.workflow import complete_task
            with pytest.raises(HTTPException) as exc_info:
                await complete_task("T-1")
            assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_fallback_complete(self):
        store = {
            "T-1": {"task_id": "T-1", "description": "Test", "phase": "P1",
                     "status": "IN_PROGRESS", "agent_id": "a"},
        }
        with patch(_P_CLIENT, return_value=None), \
             patch(_P_STORE, store), \
             patch(f"{_P_HELPERS}.record_completion_audit"):
            from governance.routes.tasks.workflow import complete_task
            result = await complete_task("T-1", evidence="Done")
        assert result.status == "DONE"


class TestPromoteResolution:
    @pytest.mark.asyncio
    async def test_typedb_success(self):
        client = MagicMock()
        task = _make_task_obj(status="DONE", resolution="IMPLEMENTED",
                             evidence="Existing")
        client.get_task.return_value = task
        client.update_task_status.return_value = task
        resp = _make_response(status="DONE")

        with patch(_P_CLIENT, return_value=client), \
             patch(_P_TO_RESP, return_value=resp), \
             patch(f"{_P_HELPERS}.try_link_task_to_session"):
            from governance.routes.tasks.workflow import promote_task_resolution
            result = await promote_task_resolution(
                "T-1", target_resolution="VALIDATED",
                evidence="Tests pass",
            )
        assert result is not None

    @pytest.mark.asyncio
    async def test_not_completed(self):
        from fastapi import HTTPException
        client = MagicMock()
        client.get_task.return_value = _make_task_obj(status="IN_PROGRESS")

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.tasks.workflow import promote_task_resolution
            with pytest.raises(HTTPException) as exc_info:
                await promote_task_resolution(
                    "T-1", target_resolution="VALIDATED", evidence="e",
                )
            assert exc_info.value.status_code == 409
