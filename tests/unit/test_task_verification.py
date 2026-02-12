"""
Unit tests for Task Verification Routes.

Per DOC-SIZE-01-v1: Tests for routes/tasks/verification.py module.
Tests: create_verification_subtasks, get_verification_status.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from governance.routes.tasks.verification import router

# We test route handler functions directly
_P_CLIENT = "governance.routes.tasks.verification.get_typedb_client"
_P_STORE = "governance.routes.tasks.verification._tasks_store"
_P_TO_RESP = "governance.routes.tasks.verification.task_to_response"


def _make_task(task_id="TASK-001", phase="IMPLEMENTATION", status="IN_PROGRESS",
               resolution="NONE"):
    t = MagicMock()
    t.id = task_id
    t.phase = phase
    t.status = status
    t.resolution = resolution
    return t


def _make_client(parent=None, subtasks=None, connect=True):
    c = MagicMock()
    c.connect.return_value = connect

    def _get_task(tid):
        if parent and tid == parent.id:
            return parent
        if subtasks:
            for s in subtasks:
                if s.id == tid:
                    return s
        return None

    c.get_task.side_effect = _get_task
    c.create_task.side_effect = lambda t: t
    c.link_parent_task.return_value = True
    return c


class TestCreateVerificationSubtasks:
    @pytest.mark.asyncio
    async def test_creates_l1_l2(self):
        parent = _make_task()
        client = _make_client(parent=parent)

        resp = MagicMock()
        resp.task_id = "TASK-001-L1-VERIFY"

        with patch(_P_CLIENT, return_value=client), \
             patch(_P_STORE, {}), \
             patch(_P_TO_RESP, return_value=resp):
            from governance.routes.tasks.verification import create_verification_subtasks
            result = await create_verification_subtasks("TASK-001", include_l3=False)

        assert len(result) == 2
        # Verify create_task was called twice (L1, L2)
        assert client.create_task.call_count == 2

    @pytest.mark.asyncio
    async def test_creates_l1_l2_l3(self):
        parent = _make_task()
        client = _make_client(parent=parent)

        resp = MagicMock()
        with patch(_P_CLIENT, return_value=client), \
             patch(_P_STORE, {}), \
             patch(_P_TO_RESP, return_value=resp):
            from governance.routes.tasks.verification import create_verification_subtasks
            result = await create_verification_subtasks("TASK-001", include_l3=True)

        assert len(result) == 3
        assert client.create_task.call_count == 3

    @pytest.mark.asyncio
    async def test_skips_existing_subtask(self):
        parent = _make_task()
        existing_l1 = _make_task(task_id="TASK-001-L1-VERIFY", status="DONE")
        client = _make_client(parent=parent, subtasks=[existing_l1])

        resp = MagicMock()
        with patch(_P_CLIENT, return_value=client), \
             patch(_P_STORE, {}), \
             patch(_P_TO_RESP, return_value=resp):
            from governance.routes.tasks.verification import create_verification_subtasks
            result = await create_verification_subtasks("TASK-001", include_l3=False)

        assert len(result) == 2
        # L1 already exists, only L2 created
        assert client.create_task.call_count == 1

    @pytest.mark.asyncio
    async def test_fallback_to_memory(self):
        store = {"TASK-001": {
            "task_id": "TASK-001", "phase": "VERIFICATION", "status": "IN_PROGRESS",
        }}

        with patch(_P_CLIENT, return_value=None), \
             patch(_P_STORE, store):
            from governance.routes.tasks.verification import create_verification_subtasks
            result = await create_verification_subtasks("TASK-001", include_l3=False)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_404_not_found(self):
        from fastapi import HTTPException
        with patch(_P_CLIENT, return_value=None), \
             patch(_P_STORE, {}):
            from governance.routes.tasks.verification import create_verification_subtasks
            with pytest.raises(HTTPException) as exc_info:
                await create_verification_subtasks("NONEXISTENT", include_l3=False)
            assert exc_info.value.status_code == 404


class TestGetVerificationStatus:
    @pytest.mark.asyncio
    async def test_no_subtasks(self):
        parent = _make_task(resolution="NONE")
        client = _make_client(parent=parent)

        with patch(_P_CLIENT, return_value=client), \
             patch(_P_STORE, {}):
            from governance.routes.tasks.verification import get_verification_status
            result = await get_verification_status("TASK-001")

        assert result["task_id"] == "TASK-001"
        assert result["highest_completed"] is None
        assert result["expected_resolution"] == "NONE"
        assert result["resolution_mismatch"] is False

    @pytest.mark.asyncio
    async def test_l1_completed(self):
        parent = _make_task(resolution="NONE")
        l1 = _make_task(task_id="TASK-001-L1-VERIFY", status="DONE")
        client = _make_client(parent=parent, subtasks=[l1])

        with patch(_P_CLIENT, return_value=client), \
             patch(_P_STORE, {}):
            from governance.routes.tasks.verification import get_verification_status
            result = await get_verification_status("TASK-001")

        assert result["highest_completed"] == "L1"
        assert result["expected_resolution"] == "IMPLEMENTED"
        assert result["resolution_mismatch"] is True  # NONE != IMPLEMENTED

    @pytest.mark.asyncio
    async def test_l2_completed(self):
        parent = _make_task(resolution="VALIDATED")
        l1 = _make_task(task_id="TASK-001-L1-VERIFY", status="DONE")
        l2 = _make_task(task_id="TASK-001-L2-VERIFY", status="DONE")
        client = _make_client(parent=parent, subtasks=[l1, l2])

        with patch(_P_CLIENT, return_value=client), \
             patch(_P_STORE, {}):
            from governance.routes.tasks.verification import get_verification_status
            result = await get_verification_status("TASK-001")

        assert result["highest_completed"] == "L2"
        assert result["expected_resolution"] == "VALIDATED"
        assert result["resolution_mismatch"] is False

    @pytest.mark.asyncio
    async def test_l3_completed(self):
        parent = _make_task(resolution="CERTIFIED")
        l1 = _make_task(task_id="TASK-001-L1-VERIFY", status="DONE")
        l2 = _make_task(task_id="TASK-001-L2-VERIFY", status="DONE")
        l3 = _make_task(task_id="TASK-001-L3-VERIFY", status="completed")
        client = _make_client(parent=parent, subtasks=[l1, l2, l3])

        with patch(_P_CLIENT, return_value=client), \
             patch(_P_STORE, {}):
            from governance.routes.tasks.verification import get_verification_status
            result = await get_verification_status("TASK-001")

        assert result["highest_completed"] == "L3"
        assert result["expected_resolution"] == "CERTIFIED"

    @pytest.mark.asyncio
    async def test_404_not_found(self):
        from fastapi import HTTPException
        with patch(_P_CLIENT, return_value=None), \
             patch(_P_STORE, {}):
            from governance.routes.tasks.verification import get_verification_status
            with pytest.raises(HTTPException) as exc_info:
                await get_verification_status("NONEXISTENT")
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_memory_fallback(self):
        store = {
            "TASK-001": {
                "task_id": "TASK-001", "status": "IN_PROGRESS",
                "resolution": "NONE",
            },
        }
        with patch(_P_CLIENT, return_value=None), \
             patch(_P_STORE, store):
            from governance.routes.tasks.verification import get_verification_status
            result = await get_verification_status("TASK-001")

        assert result["task_id"] == "TASK-001"
        assert result["resolution"] == "NONE"
