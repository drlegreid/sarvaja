"""
Unit tests for Task Verification Routes.

Batch 127: Tests for governance/routes/tasks/verification.py
- create_verification_subtasks: L1/L2/L3 hierarchy, TypeDB + memory fallback
- get_verification_status: resolution mismatch detection
"""

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from governance.routes.tasks.verification import router


_MOD = "governance.routes.tasks.verification"

app = FastAPI()
app.include_router(router, prefix="/api")
test_client = TestClient(app)


def _make_parent_task(task_id="T-1", phase="P1", resolution="NONE"):
    task = MagicMock()
    task.id = task_id
    task.phase = phase
    task.resolution = resolution
    task.status = "IN_PROGRESS"
    return task


# ── create_verification_subtasks ─────────────────────────


class TestCreateVerificationSubtasks:

    @patch(f"{_MOD}.get_typedb_client", return_value=None)
    @patch(f"{_MOD}._tasks_store", {})
    def test_task_not_found_returns_404(self, mock_get):
        resp = test_client.post("/api/tasks/MISSING/create-verification-subtasks")
        assert resp.status_code == 404

    @patch(f"{_MOD}.get_typedb_client", return_value=None)
    @patch(f"{_MOD}._tasks_store", {
        "T-1": {"task_id": "T-1", "description": "Task", "phase": "P1", "status": "IN_PROGRESS"}
    })
    def test_creates_l1_l2_in_memory(self, mock_get):
        with patch(f"{_MOD}._tasks_store", {
            "T-1": {"task_id": "T-1", "description": "Task", "phase": "P1", "status": "IN_PROGRESS"}
        }) as store:
            resp = test_client.post("/api/tasks/T-1/create-verification-subtasks")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 2
            ids = [t["task_id"] for t in data]
            assert "T-1-L1-VERIFY" in ids
            assert "T-1-L2-VERIFY" in ids

    @patch(f"{_MOD}.get_typedb_client", return_value=None)
    def test_creates_l3_when_requested(self, mock_get):
        with patch(f"{_MOD}._tasks_store", {
            "T-1": {"task_id": "T-1", "description": "Task", "phase": "P1", "status": "OPEN"}
        }):
            resp = test_client.post(
                "/api/tasks/T-1/create-verification-subtasks?include_l3=true"
            )
            data = resp.json()
            assert len(data) == 3
            ids = [t["task_id"] for t in data]
            assert "T-1-L3-VERIFY" in ids

    @patch(f"{_MOD}.get_typedb_client")
    def test_uses_typedb_parent_task(self, mock_get):
        mock_db = MagicMock()
        mock_db.get_task.side_effect = lambda tid: (
            _make_parent_task() if tid == "T-1" else None
        )
        mock_db.create_task.return_value = MagicMock()
        mock_get.return_value = mock_db

        with patch(f"{_MOD}.task_to_response") as mock_resp:
            mock_resp.return_value = {"task_id": "T-1-L1-VERIFY", "description": "test",
                                       "phase": "P1", "status": "TODO"}
            resp = test_client.post("/api/tasks/T-1/create-verification-subtasks")
            assert resp.status_code == 200

    @patch(f"{_MOD}.get_typedb_client")
    def test_existing_subtask_returned_not_recreated(self, mock_get):
        mock_db = MagicMock()
        parent = _make_parent_task()
        existing_l1 = MagicMock()
        existing_l1.id = "T-1-L1-VERIFY"
        existing_l1.status = "DONE"

        def get_task_side_effect(tid):
            if tid == "T-1":
                return parent
            if tid == "T-1-L1-VERIFY":
                return existing_l1
            return None

        mock_db.get_task.side_effect = get_task_side_effect
        mock_db.create_task.return_value = MagicMock()
        mock_get.return_value = mock_db

        with patch(f"{_MOD}.task_to_response") as mock_resp:
            mock_resp.return_value = {"task_id": "test", "description": "test",
                                       "phase": "P1", "status": "TODO"}
            resp = test_client.post("/api/tasks/T-1/create-verification-subtasks")
            # L1 exists, L2 created — should have 2 subtasks
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 2

    @patch(f"{_MOD}.get_typedb_client")
    def test_typedb_create_failure_falls_back_to_memory(self, mock_get):
        mock_db = MagicMock()
        mock_db.get_task.side_effect = lambda tid: (
            _make_parent_task() if tid == "T-1" else None
        )
        mock_db.create_task.side_effect = Exception("TypeDB write failed")

        mock_get.return_value = mock_db

        with patch(f"{_MOD}._tasks_store", {}) as store:
            resp = test_client.post("/api/tasks/T-1/create-verification-subtasks")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 2
            # Stored in memory fallback
            assert "T-1-L1-VERIFY" in store
            assert "T-1-L2-VERIFY" in store


# ── get_verification_status ──────────────────────────────


class TestGetVerificationStatus:

    @patch(f"{_MOD}.get_typedb_client", return_value=None)
    @patch(f"{_MOD}._tasks_store", {})
    def test_task_not_found_returns_404(self, mock_get):
        resp = test_client.get("/api/tasks/MISSING/verification-status")
        assert resp.status_code == 404

    @patch(f"{_MOD}.get_typedb_client", return_value=None)
    def test_no_subtasks(self, mock_get):
        with patch(f"{_MOD}._tasks_store", {
            "T-1": {"task_id": "T-1", "resolution": "NONE"}
        }):
            resp = test_client.get("/api/tasks/T-1/verification-status")
            data = resp.json()
            assert data["highest_completed"] is None
            assert data["expected_resolution"] == "NONE"
            assert data["resolution_mismatch"] is False

    @patch(f"{_MOD}.get_typedb_client", return_value=None)
    def test_l1_completed(self, mock_get):
        with patch(f"{_MOD}._tasks_store", {
            "T-1": {"task_id": "T-1", "resolution": "NONE"},
            "T-1-L1-VERIFY": {"task_id": "T-1-L1-VERIFY", "status": "DONE"},
        }):
            resp = test_client.get("/api/tasks/T-1/verification-status")
            data = resp.json()
            assert data["highest_completed"] == "L1"
            assert data["expected_resolution"] == "IMPLEMENTED"
            assert data["resolution_mismatch"] is True

    @patch(f"{_MOD}.get_typedb_client", return_value=None)
    def test_l2_completed(self, mock_get):
        with patch(f"{_MOD}._tasks_store", {
            "T-1": {"task_id": "T-1", "resolution": "IMPLEMENTED"},
            "T-1-L1-VERIFY": {"task_id": "T-1-L1-VERIFY", "status": "DONE"},
            "T-1-L2-VERIFY": {"task_id": "T-1-L2-VERIFY", "status": "CLOSED"},
        }):
            resp = test_client.get("/api/tasks/T-1/verification-status")
            data = resp.json()
            assert data["highest_completed"] == "L2"
            assert data["expected_resolution"] == "VALIDATED"
            assert data["resolution_mismatch"] is True

    @patch(f"{_MOD}.get_typedb_client", return_value=None)
    def test_l3_completed_no_mismatch(self, mock_get):
        with patch(f"{_MOD}._tasks_store", {
            "T-1": {"task_id": "T-1", "resolution": "CERTIFIED"},
            "T-1-L1-VERIFY": {"task_id": "T-1-L1-VERIFY", "status": "DONE"},
            "T-1-L2-VERIFY": {"task_id": "T-1-L2-VERIFY", "status": "DONE"},
            "T-1-L3-VERIFY": {"task_id": "T-1-L3-VERIFY", "status": "completed"},
        }):
            resp = test_client.get("/api/tasks/T-1/verification-status")
            data = resp.json()
            assert data["highest_completed"] == "L3"
            assert data["expected_resolution"] == "CERTIFIED"
            assert data["resolution_mismatch"] is False

    @patch(f"{_MOD}.get_typedb_client")
    def test_uses_typedb_for_parent_and_subtasks(self, mock_get):
        mock_db = MagicMock()
        parent = _make_parent_task(resolution="VALIDATED")

        l1_task = MagicMock()
        l1_task.status = "DONE"
        l2_task = MagicMock()
        l2_task.status = "DONE"

        def get_task_side_effect(tid):
            if tid == "T-1":
                return parent
            if tid == "T-1-L1-VERIFY":
                return l1_task
            if tid == "T-1-L2-VERIFY":
                return l2_task
            return None

        mock_db.get_task.side_effect = get_task_side_effect
        mock_get.return_value = mock_db

        with patch(f"{_MOD}._tasks_store", {}):
            resp = test_client.get("/api/tasks/T-1/verification-status")
            data = resp.json()
            assert data["verification_levels"]["L1"]["completed"] is True
            assert data["verification_levels"]["L2"]["completed"] is True
            assert data["verification_levels"]["L3"]["exists"] is False

    @patch(f"{_MOD}.get_typedb_client", return_value=None)
    def test_l1_not_done(self, mock_get):
        with patch(f"{_MOD}._tasks_store", {
            "T-1": {"task_id": "T-1", "resolution": "NONE"},
            "T-1-L1-VERIFY": {"task_id": "T-1-L1-VERIFY", "status": "TODO"},
        }):
            resp = test_client.get("/api/tasks/T-1/verification-status")
            data = resp.json()
            assert data["verification_levels"]["L1"]["exists"] is True
            assert data["verification_levels"]["L1"]["completed"] is False
            assert data["highest_completed"] is None
