"""
Unit tests for Task Verification Routes.

Per DOC-SIZE-01-v1: Tests for routes/tasks/verification.py module.
Tests: create_verification_subtasks, get_verification_status.
"""

from unittest.mock import MagicMock, patch

import pytest

_P = "governance.routes.tasks.verification"


def _make_task_obj(task_id="T-1", status="DONE", phase="P10",
                   resolution="IMPLEMENTED", **extra):
    t = MagicMock()
    t.task_id = task_id
    t.status = status
    t.phase = phase
    t.resolution = resolution
    for k, v in extra.items():
        setattr(t, k, v)
    return t


@pytest.fixture(autouse=True)
def _patch_stores():
    with patch(f"{_P}._tasks_store", {
        "T-1": {"task_id": "T-1", "description": "Parent task",
                "status": "DONE", "phase": "P10",
                "resolution": "IMPLEMENTED"},
    }) as store:
        yield store


# ── create_verification_subtasks ─────────────────────────────────


class TestCreateVerificationSubtasks:
    @pytest.mark.asyncio
    async def test_creates_l1_l2(self):
        from governance.routes.tasks.verification import create_verification_subtasks
        with patch(f"{_P}.get_typedb_client", return_value=None), \
             patch(f"{_P}.TaskResponse", side_effect=lambda **kw: kw):
            # Query(False) is truthy when called directly, pass explicit False
            result = await create_verification_subtasks("T-1", include_l3=False)
        assert len(result) == 2
        ids = [r["task_id"] for r in result]
        assert "T-1-L1-VERIFY" in ids
        assert "T-1-L2-VERIFY" in ids

    @pytest.mark.asyncio
    async def test_includes_l3(self):
        from governance.routes.tasks.verification import create_verification_subtasks
        with patch(f"{_P}.get_typedb_client", return_value=None), \
             patch(f"{_P}.TaskResponse", side_effect=lambda **kw: kw):
            result = await create_verification_subtasks("T-1", include_l3=True)
        assert len(result) == 3
        ids = [r["task_id"] for r in result]
        assert "T-1-L3-VERIFY" in ids

    @pytest.mark.asyncio
    async def test_not_found(self):
        from governance.routes.tasks.verification import create_verification_subtasks
        from fastapi import HTTPException
        with patch(f"{_P}.get_typedb_client", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await create_verification_subtasks("NONEXISTENT")
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_typedb_parent(self):
        from governance.routes.tasks.verification import create_verification_subtasks
        mock_client = MagicMock()
        mock_client.get_task.side_effect = lambda tid: (
            _make_task_obj("T-1") if tid == "T-1" else None
        )
        mock_client.create_task.return_value = _make_task_obj("T-1-L1-VERIFY", "TODO")
        mock_client.link_parent_task.return_value = True
        with patch(f"{_P}.get_typedb_client", return_value=mock_client), \
             patch(f"{_P}.task_to_response", side_effect=lambda t: {"task_id": t.task_id}):
            result = await create_verification_subtasks("T-1", include_l3=False)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_existing_subtask_skipped(self):
        from governance.routes.tasks.verification import create_verification_subtasks
        mock_client = MagicMock()
        mock_client.get_task.side_effect = lambda tid: (
            _make_task_obj(tid) if tid in ("T-1", "T-1-L1-VERIFY") else None
        )
        mock_client.create_task.return_value = _make_task_obj("T-1-L2-VERIFY", "TODO")
        mock_client.link_parent_task.return_value = True
        with patch(f"{_P}.get_typedb_client", return_value=mock_client), \
             patch(f"{_P}.task_to_response", side_effect=lambda t: {"task_id": t.task_id}):
            result = await create_verification_subtasks("T-1", include_l3=False)
        # L1 existed, L2 created
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_typedb_create_failure_fallback(self):
        from governance.routes.tasks.verification import create_verification_subtasks
        mock_client = MagicMock()
        mock_client.get_task.side_effect = lambda tid: (
            _make_task_obj("T-1") if tid == "T-1" else None
        )
        mock_client.create_task.side_effect = Exception("DB error")
        with patch(f"{_P}.get_typedb_client", return_value=mock_client), \
             patch(f"{_P}.TaskResponse", side_effect=lambda **kw: kw):
            result = await create_verification_subtasks("T-1", include_l3=False)
        assert len(result) == 2  # fell back to in-memory


# ── get_verification_status ──────────────────────────────────────


class TestGetVerificationStatus:
    @pytest.mark.asyncio
    async def test_no_subtasks(self):
        from governance.routes.tasks.verification import get_verification_status
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = await get_verification_status("T-1")
        assert result["task_id"] == "T-1"
        assert result["highest_completed"] is None
        assert result["expected_resolution"] == "NONE"

    @pytest.mark.asyncio
    async def test_not_found(self):
        from governance.routes.tasks.verification import get_verification_status
        from fastapi import HTTPException
        with patch(f"{_P}.get_typedb_client", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await get_verification_status("NONEXISTENT")
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_l1_completed(self, _patch_stores):
        from governance.routes.tasks.verification import get_verification_status
        _patch_stores["T-1-L1-VERIFY"] = {
            "task_id": "T-1-L1-VERIFY", "status": "DONE",
        }
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = await get_verification_status("T-1")
        assert result["highest_completed"] == "L1"
        assert result["expected_resolution"] == "IMPLEMENTED"

    @pytest.mark.asyncio
    async def test_l2_completed(self, _patch_stores):
        from governance.routes.tasks.verification import get_verification_status
        _patch_stores["T-1-L1-VERIFY"] = {"task_id": "T-1-L1-VERIFY", "status": "DONE"}
        _patch_stores["T-1-L2-VERIFY"] = {"task_id": "T-1-L2-VERIFY", "status": "DONE"}
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = await get_verification_status("T-1")
        assert result["highest_completed"] == "L2"
        assert result["expected_resolution"] == "VALIDATED"

    @pytest.mark.asyncio
    async def test_l3_completed(self, _patch_stores):
        from governance.routes.tasks.verification import get_verification_status
        _patch_stores["T-1-L1-VERIFY"] = {"task_id": "T-1-L1-VERIFY", "status": "DONE"}
        _patch_stores["T-1-L2-VERIFY"] = {"task_id": "T-1-L2-VERIFY", "status": "DONE"}
        _patch_stores["T-1-L3-VERIFY"] = {"task_id": "T-1-L3-VERIFY", "status": "DONE"}
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = await get_verification_status("T-1")
        assert result["highest_completed"] == "L3"
        assert result["expected_resolution"] == "CERTIFIED"

    @pytest.mark.asyncio
    async def test_resolution_mismatch(self, _patch_stores):
        from governance.routes.tasks.verification import get_verification_status
        _patch_stores["T-1-L1-VERIFY"] = {"task_id": "T-1-L1-VERIFY", "status": "DONE"}
        _patch_stores["T-1-L2-VERIFY"] = {"task_id": "T-1-L2-VERIFY", "status": "DONE"}
        # Parent has IMPLEMENTED but L2 is done → expected VALIDATED
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = await get_verification_status("T-1")
        assert result["resolution_mismatch"] is True
        assert "VALIDATED" in result["recommendation"]

    @pytest.mark.asyncio
    async def test_typedb_parent(self):
        from governance.routes.tasks.verification import get_verification_status
        mock_client = MagicMock()
        mock_client.get_task.side_effect = lambda tid: (
            _make_task_obj("T-1") if tid == "T-1" else None
        )
        with patch(f"{_P}.get_typedb_client", return_value=mock_client):
            result = await get_verification_status("T-1")
        assert result["task_id"] == "T-1"
