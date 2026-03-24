"""
Unit tests for Task Detail Section Routes.

Batch 132: Tests for governance/routes/tasks/details.py
- GET /tasks/{task_id}/details: TypeDB + memory fallback
- PUT /tasks/{task_id}/details: Batch update with validation
"""

from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from governance.routes.tasks.details import router


_SVC = "governance.services.tasks"
_SVQ = "governance.services.tasks_queries"

app = FastAPI()
app.include_router(router, prefix="/api")
test_client = TestClient(app)


# ── GET /tasks/{task_id}/details ─────────────────────────


class TestGetTaskDetails:

    @patch(f"{_SVC}.get_task_details", return_value=None)
    def test_not_found_returns_404(self, mock_get):
        resp = test_client.get("/api/tasks/MISSING/details")
        assert resp.status_code == 404

    @patch(f"{_SVC}.get_task_details")
    def test_returns_all_sections(self, mock_get):
        mock_get.return_value = {
            "task_id": "T-1",
            "business": "User needs X",
            "design": "Component Y",
            "architecture": "Service Z",
            "test_section": "Test plan W",
        }
        resp = test_client.get("/api/tasks/T-1/details")
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == "T-1"
        assert data["business"] == "User needs X"
        assert data["design"] == "Component Y"
        assert data["architecture"] == "Service Z"
        assert data["test_section"] == "Test plan W"

    @patch(f"{_SVC}.get_task_details")
    def test_returns_null_sections(self, mock_get):
        mock_get.return_value = {
            "task_id": "T-2",
            "business": None,
            "design": None,
            "architecture": None,
            "test_section": None,
        }
        resp = test_client.get("/api/tasks/T-2/details")
        assert resp.status_code == 200
        data = resp.json()
        assert data["business"] is None
        assert data["design"] is None

    @patch(f"{_SVC}.get_task_details")
    def test_partial_sections(self, mock_get):
        mock_get.return_value = {
            "task_id": "T-3",
            "business": "Only business filled",
            "design": None,
            "architecture": None,
            "test_section": None,
        }
        resp = test_client.get("/api/tasks/T-3/details")
        assert resp.status_code == 200
        data = resp.json()
        assert data["business"] == "Only business filled"
        assert data["architecture"] is None


# ── PUT /tasks/{task_id}/details ─────────────────────────


class TestUpdateTaskDetails:

    @patch(f"{_SVC}.update_task_details", return_value=None)
    def test_not_found_returns_404(self, mock_update):
        resp = test_client.put("/api/tasks/MISSING/details", json={
            "business": "New business context"
        })
        assert resp.status_code == 404

    def test_empty_body_returns_422(self):
        resp = test_client.put("/api/tasks/T-1/details", json={})
        assert resp.status_code == 422

    @patch(f"{_SVC}.update_task_details")
    def test_update_single_section(self, mock_update):
        mock_update.return_value = {
            "task_id": "T-1",
            "business": "Updated business",
            "design": None,
            "architecture": None,
            "test_section": None,
        }
        resp = test_client.put("/api/tasks/T-1/details", json={
            "business": "Updated business"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["business"] == "Updated business"
        mock_update.assert_called_once_with(
            "T-1",
            business="Updated business",
            design=None,
            architecture=None,
            test_section=None,
        )

    @patch(f"{_SVC}.update_task_details")
    def test_update_all_sections(self, mock_update):
        mock_update.return_value = {
            "task_id": "T-1",
            "business": "Biz",
            "design": "Design",
            "architecture": "Arch",
            "test_section": "Tests",
        }
        resp = test_client.put("/api/tasks/T-1/details", json={
            "business": "Biz",
            "design": "Design",
            "architecture": "Arch",
            "test_section": "Tests",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["business"] == "Biz"
        assert data["architecture"] == "Arch"

    @patch(f"{_SVC}.update_task_details")
    def test_update_preserves_existing(self, mock_update):
        """Updating one section doesn't clear others."""
        mock_update.return_value = {
            "task_id": "T-1",
            "business": "Existing biz",
            "design": "New design",
            "architecture": "Existing arch",
            "test_section": None,
        }
        resp = test_client.put("/api/tasks/T-1/details", json={
            "design": "New design"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["design"] == "New design"
        assert data["business"] == "Existing biz"


# ── Service layer: get_task_details ──────────────────────


class TestGetTaskDetailsService:

    @patch(f"{_SVQ}.get_typedb_client")
    def test_typedb_returns_details(self, mock_client):
        mock_db = MagicMock()
        mock_db.get_task_details.return_value = {
            "business": "B", "design": "D",
            "architecture": "A", "test_section": "T",
        }
        mock_client.return_value = mock_db

        from governance.services.tasks import get_task_details
        result = get_task_details("T-1")
        assert result["task_id"] == "T-1"
        assert result["business"] == "B"

    @patch(f"{_SVQ}.get_typedb_client", return_value=None)
    def test_fallback_to_memory(self, mock_client):
        from governance.services.tasks import get_task_details
        with patch(f"{_SVQ}._tasks_store", {
            "T-1": {"business": "Mem-B", "design": "Mem-D"}
        }):
            result = get_task_details("T-1")
            assert result["task_id"] == "T-1"
            assert result["business"] == "Mem-B"
            assert result["design"] == "Mem-D"

    @patch(f"{_SVQ}.get_typedb_client", return_value=None)
    def test_not_found_returns_none(self, mock_client):
        from governance.services.tasks import get_task_details
        with patch(f"{_SVQ}._tasks_store", {}):
            result = get_task_details("NOPE")
            assert result is None

    @patch(f"{_SVQ}.get_typedb_client")
    def test_typedb_error_falls_back(self, mock_client):
        mock_db = MagicMock()
        mock_db.get_task_details.side_effect = Exception("TypeDB down")
        mock_client.return_value = mock_db

        from governance.services.tasks import get_task_details
        with patch(f"{_SVQ}._tasks_store", {
            "T-1": {"architecture": "fallback-arch"}
        }):
            result = get_task_details("T-1")
            assert result["architecture"] == "fallback-arch"


# ── Service layer: update_task_details ───────────────────


class TestUpdateTaskDetailsService:

    @patch(f"{_SVC}.get_typedb_client")
    @patch(f"{_SVC}._monitor")
    def test_typedb_update_success(self, mock_monitor, mock_client):
        mock_db = MagicMock()
        mock_db.update_task_details.return_value = True
        mock_db.get_task_details.return_value = {
            "business": "Updated", "design": None,
            "architecture": None, "test_section": None,
        }
        mock_client.return_value = mock_db

        from governance.services.tasks import update_task_details
        # Patch get_typedb_client on queries module too (get_task_details lives there)
        with patch(f"{_SVQ}.get_typedb_client", return_value=mock_db):
            result = update_task_details("T-1", business="Updated")
        assert result is not None
        mock_db.update_task_details.assert_called_once()
        mock_monitor.assert_called()

    @patch(f"{_SVC}.get_typedb_client", return_value=None)
    @patch(f"{_SVC}._monitor")
    def test_fallback_update(self, mock_monitor, mock_client):
        from governance.services.tasks import update_task_details
        store = {"T-1": {"business": "Old"}}
        with patch(f"{_SVC}._tasks_store", store), \
             patch(f"{_SVQ}._tasks_store", store), \
             patch(f"{_SVQ}.get_typedb_client", return_value=None):
            result = update_task_details("T-1", business="New")
            assert result is not None
            assert store["T-1"]["business"] == "New"

    @patch(f"{_SVC}.get_typedb_client", return_value=None)
    def test_not_found_returns_none(self, mock_client):
        from governance.services.tasks import update_task_details
        with patch(f"{_SVC}._tasks_store", {}), \
             patch(f"{_SVQ}._tasks_store", {}), \
             patch(f"{_SVQ}.get_typedb_client", return_value=None):
            result = update_task_details("NOPE", business="X")
            assert result is None


# ── Pydantic Models ──────────────────────────────────────


class TestTaskDetailsModels:

    def test_update_model_all_optional(self):
        from governance.models import TaskDetailsUpdate
        m = TaskDetailsUpdate()
        assert m.business is None
        assert m.design is None
        assert m.architecture is None
        assert m.test_section is None

    def test_update_model_with_values(self):
        from governance.models import TaskDetailsUpdate
        m = TaskDetailsUpdate(business="B", design="D")
        assert m.business == "B"
        assert m.design == "D"

    def test_response_model(self):
        from governance.models import TaskDetailsResponse
        m = TaskDetailsResponse(task_id="T-1", business="B")
        assert m.task_id == "T-1"
        assert m.business == "B"
        assert m.design is None
