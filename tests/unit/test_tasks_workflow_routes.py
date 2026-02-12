"""
Unit tests for Tasks Workflow Routes.

Per DOC-SIZE-01-v1: Tests for routes/tasks/workflow.py module.
Tests: list_available_tasks, claim_task, complete_task, promote_task_resolution.
"""

from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

import pytest

_P = "governance.routes.tasks.workflow"


def _make_task_obj(task_id="T-1", status="TODO", agent_id=None,
                   evidence=None, resolution=None):
    t = MagicMock()
    t.task_id = task_id
    t.status = status
    t.agent_id = agent_id
    t.evidence = evidence
    t.resolution = resolution
    return t


@pytest.fixture(autouse=True)
def _patch_stores():
    with patch(f"{_P}._tasks_store", {
        "T-1": {"task_id": "T-1", "title": "Test Task", "status": "TODO",
                "priority": "HIGH", "description": "Desc", "agent_id": None,
                "evidence": None, "resolution": "NONE",
                "created_at": "2026-01-01T00:00:00"},
        "T-2": {"task_id": "T-2", "title": "In Progress Task", "status": "IN_PROGRESS",
                "priority": "MEDIUM", "description": "Desc", "agent_id": "code-agent",
                "evidence": None, "resolution": "NONE",
                "created_at": "2026-01-01T00:00:00"},
        "T-3": {"task_id": "T-3", "title": "Done Task", "status": "DONE",
                "priority": "LOW", "description": "Desc", "agent_id": "code-agent",
                "evidence": "Fixed it", "resolution": "IMPLEMENTED",
                "created_at": "2026-01-01T00:00:00"},
    }), \
        patch(f"{_P}._agents_store", {
            "code-agent": {"tasks_executed": 5, "last_active": None,
                           "trust_score": 0.85},
        }), \
        patch(f"{_P}._AGENT_BASE_CONFIG", {
            "code-agent": {"base_trust": 0.85},
        }), \
        patch(f"{_P}._load_agent_metrics", return_value={}), \
        patch(f"{_P}._save_agent_metrics"), \
        patch(f"{_P}._calculate_trust_score", return_value=0.85), \
        patch(f"{_P}._update_agent_metrics_on_claim"), \
        patch(f"{_P}.record_completion_audit"), \
        patch(f"{_P}.try_link_task_to_session"):
        yield


@pytest.fixture
def _mock_task_response():
    with patch(f"{_P}.TaskResponse") as mock_cls:
        mock_cls.side_effect = lambda **kwargs: kwargs
        yield mock_cls


# ── list_available_tasks ─────────────────────────────────────────


class TestListAvailableTasks:
    @pytest.mark.asyncio
    async def test_fallback_returns_available(self):
        from governance.routes.tasks.workflow import list_available_tasks
        with patch(f"{_P}.get_typedb_client", return_value=None), \
             patch(f"{_P}.TaskResponse", side_effect=lambda **kw: kw):
            result = await list_available_tasks()
        # Only T-1 has status TODO and no agent_id
        assert len(result) == 1
        assert result[0]["task_id"] == "T-1"

    @pytest.mark.asyncio
    async def test_typedb_returns_tasks(self):
        from governance.routes.tasks.workflow import list_available_tasks
        mock_client = MagicMock()
        mock_client.get_available_tasks.return_value = [
            _make_task_obj("T-10", "TODO"),
        ]
        with patch(f"{_P}.get_typedb_client", return_value=mock_client), \
             patch(f"{_P}.task_to_response", side_effect=lambda t: {"task_id": t.task_id}):
            result = await list_available_tasks()
        assert len(result) == 1
        assert result[0]["task_id"] == "T-10"

    @pytest.mark.asyncio
    async def test_typedb_empty_falls_through(self):
        from governance.routes.tasks.workflow import list_available_tasks
        mock_client = MagicMock()
        mock_client.get_available_tasks.return_value = []
        with patch(f"{_P}.get_typedb_client", return_value=mock_client), \
             patch(f"{_P}.TaskResponse", side_effect=lambda **kw: kw):
            result = await list_available_tasks()
        assert len(result) == 1  # fallback to in-memory T-1

    @pytest.mark.asyncio
    async def test_typedb_exception_fallback(self):
        from governance.routes.tasks.workflow import list_available_tasks
        mock_client = MagicMock()
        mock_client.get_available_tasks.side_effect = Exception("DB error")
        with patch(f"{_P}.get_typedb_client", return_value=mock_client), \
             patch(f"{_P}.TaskResponse", side_effect=lambda **kw: kw):
            result = await list_available_tasks()
        assert len(result) == 1


# ── claim_task ───────────────────────────────────────────────────


class TestClaimTask:
    @pytest.mark.asyncio
    async def test_claim_fallback_success(self):
        from governance.routes.tasks.workflow import claim_task
        with patch(f"{_P}.get_typedb_client", return_value=None), \
             patch(f"{_P}.TaskResponse", side_effect=lambda **kw: kw), \
             patch(f"{_P}.update_agent_metrics_on_claim_fallback"):
            result = await claim_task("T-1", agent_id="code-agent")
        assert result["agent_id"] == "code-agent"
        assert result["status"] == "IN_PROGRESS"

    @pytest.mark.asyncio
    async def test_claim_not_found(self):
        from governance.routes.tasks.workflow import claim_task
        from fastapi import HTTPException
        with patch(f"{_P}.get_typedb_client", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await claim_task("NONEXISTENT", agent_id="code-agent")
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_claim_already_claimed(self):
        from governance.routes.tasks.workflow import claim_task
        from fastapi import HTTPException
        with patch(f"{_P}.get_typedb_client", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await claim_task("T-2", agent_id="other-agent")
            assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_claim_wrong_status(self):
        from governance.routes.tasks.workflow import claim_task
        from fastapi import HTTPException
        with patch(f"{_P}.get_typedb_client", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await claim_task("T-3", agent_id="code-agent")
            assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_claim_typedb_success(self):
        from governance.routes.tasks.workflow import claim_task
        mock_client = MagicMock()
        mock_client.get_task.return_value = _make_task_obj("T-1", "TODO")
        updated = _make_task_obj("T-1", "IN_PROGRESS", "code-agent")
        mock_client.update_task_status.return_value = updated
        with patch(f"{_P}.get_typedb_client", return_value=mock_client), \
             patch(f"{_P}.task_to_response", side_effect=lambda t: {"task_id": t.task_id}):
            result = await claim_task("T-1", agent_id="code-agent")
        assert result["task_id"] == "T-1"

    @pytest.mark.asyncio
    async def test_claim_typedb_not_found(self):
        from governance.routes.tasks.workflow import claim_task
        from fastapi import HTTPException
        mock_client = MagicMock()
        mock_client.get_task.return_value = None
        with patch(f"{_P}.get_typedb_client", return_value=mock_client):
            with pytest.raises(HTTPException) as exc:
                await claim_task("T-999", agent_id="code-agent")
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_claim_typedb_already_claimed(self):
        from governance.routes.tasks.workflow import claim_task
        from fastapi import HTTPException
        mock_client = MagicMock()
        mock_client.get_task.return_value = _make_task_obj("T-2", "IN_PROGRESS", "other")
        with patch(f"{_P}.get_typedb_client", return_value=mock_client):
            with pytest.raises(HTTPException) as exc:
                await claim_task("T-2", agent_id="code-agent")
            assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_claim_typedb_wrong_status(self):
        from governance.routes.tasks.workflow import claim_task
        from fastapi import HTTPException
        mock_client = MagicMock()
        mock_client.get_task.return_value = _make_task_obj("T-3", "DONE")
        with patch(f"{_P}.get_typedb_client", return_value=mock_client):
            with pytest.raises(HTTPException) as exc:
                await claim_task("T-3", agent_id="code-agent")
            assert exc.value.status_code == 409


# ── complete_task ────────────────────────────────────────────────


class TestCompleteTask:
    @pytest.mark.asyncio
    async def test_complete_fallback_success(self):
        from governance.routes.tasks.workflow import complete_task
        with patch(f"{_P}.get_typedb_client", return_value=None), \
             patch(f"{_P}.TaskResponse", side_effect=lambda **kw: kw):
            result = await complete_task("T-2", evidence="Fixed the bug")
        assert result["status"] == "DONE"

    @pytest.mark.asyncio
    async def test_complete_not_found(self):
        from governance.routes.tasks.workflow import complete_task
        from fastapi import HTTPException
        with patch(f"{_P}.get_typedb_client", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await complete_task("NONEXISTENT")
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_complete_already_done(self):
        from governance.routes.tasks.workflow import complete_task
        from fastapi import HTTPException
        with patch(f"{_P}.get_typedb_client", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await complete_task("T-3")
            assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_complete_typedb_success(self):
        from governance.routes.tasks.workflow import complete_task
        mock_client = MagicMock()
        task_obj = _make_task_obj("T-2", "IN_PROGRESS", "code-agent")
        mock_client.get_task.return_value = task_obj
        updated = _make_task_obj("T-2", "DONE", "code-agent")
        mock_client.update_task_status.return_value = updated
        with patch(f"{_P}.get_typedb_client", return_value=mock_client), \
             patch(f"{_P}.task_to_response", side_effect=lambda t: {"task_id": t.task_id}):
            result = await complete_task("T-2", evidence="Done")
        assert result["task_id"] == "T-2"

    @pytest.mark.asyncio
    async def test_complete_typedb_already_done(self):
        from governance.routes.tasks.workflow import complete_task
        from fastapi import HTTPException
        mock_client = MagicMock()
        mock_client.get_task.return_value = _make_task_obj("T-3", "DONE")
        with patch(f"{_P}.get_typedb_client", return_value=mock_client):
            with pytest.raises(HTTPException) as exc:
                await complete_task("T-3")
            assert exc.value.status_code == 409


# ── promote_task_resolution ──────────────────────────────────────


class TestPromoteTaskResolution:
    @pytest.mark.asyncio
    async def test_promote_fallback_success(self):
        from governance.routes.tasks.workflow import promote_task_resolution
        with patch(f"{_P}.get_typedb_client", return_value=None), \
             patch(f"{_P}.TaskResponse", side_effect=lambda **kw: kw), \
             patch(f"{_P}.validate_promotion", return_value=(True, None)):
            result = await promote_task_resolution(
                "T-3", target_resolution="VALIDATED",
                evidence="Tests pass",
            )
        assert result["resolution"] == "VALIDATED"

    @pytest.mark.asyncio
    async def test_promote_not_found(self):
        from governance.routes.tasks.workflow import promote_task_resolution
        from fastapi import HTTPException
        with patch(f"{_P}.get_typedb_client", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await promote_task_resolution(
                    "NONEXISTENT", target_resolution="VALIDATED",
                    evidence="Tests pass",
                )
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_promote_invalid_transition(self):
        from governance.routes.tasks.workflow import promote_task_resolution
        from fastapi import HTTPException
        with patch(f"{_P}.get_typedb_client", return_value=None), \
             patch(f"{_P}.validate_promotion", return_value=(False, "Cannot promote")):
            with pytest.raises(HTTPException) as exc:
                await promote_task_resolution(
                    "T-3", target_resolution="VALIDATED",
                    evidence="Tests pass",
                )
            assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_promote_typedb_success(self):
        from governance.routes.tasks.workflow import promote_task_resolution
        mock_client = MagicMock()
        task_obj = _make_task_obj("T-3", "DONE", "code-agent",
                                  evidence="Original", resolution="IMPLEMENTED")
        mock_client.get_task.return_value = task_obj
        updated = _make_task_obj("T-3", "DONE", "code-agent",
                                  resolution="VALIDATED")
        mock_client.update_task_status.return_value = updated
        with patch(f"{_P}.get_typedb_client", return_value=mock_client), \
             patch(f"{_P}.task_to_response", side_effect=lambda t: {"task_id": t.task_id}):
            result = await promote_task_resolution(
                "T-3", target_resolution="VALIDATED",
                evidence="Tests pass",
            )
        assert result["task_id"] == "T-3"

    @pytest.mark.asyncio
    async def test_promote_typedb_not_completed(self):
        from governance.routes.tasks.workflow import promote_task_resolution
        from fastapi import HTTPException
        mock_client = MagicMock()
        mock_client.get_task.return_value = _make_task_obj("T-2", "IN_PROGRESS")
        with patch(f"{_P}.get_typedb_client", return_value=mock_client):
            with pytest.raises(HTTPException) as exc:
                await promote_task_resolution(
                    "T-2", target_resolution="VALIDATED",
                    evidence="Tests pass",
                )
            assert exc.value.status_code == 409
