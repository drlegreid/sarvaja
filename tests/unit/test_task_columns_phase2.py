"""Tests for EPIC-TASK-QUALITY-V1 Phase 2: Table Columns Rework.

FIX-COL-002: Workspace column presence
FIX-COL-003: Column order verification (Phase column removed per hierarchy redesign)
FIX-COL-004: Gap column removal
FIX-COL-005: Completed column presence
FIX-COL-006: workspace_id API filter
"""

import pytest
from unittest.mock import patch, MagicMock


# ── FIX-COL-002/003/004/005: Column definitions ─────────────────────

class TestColumnDefinitions:
    """Verify column order, presence, and absence in both list.py and initial.py."""

    EXPECTED_KEYS_ORDER = [
        "project_name", "workspace_id", "task_id", "summary", "priority",
        "task_type", "status", "first_session", "agent_id",
        "created_at", "completed_at", "doc_count",
    ]

    def test_initial_state_headers_order(self):
        """FIX-COL-003: initial.py tasks_headers match target order."""
        from agent.governance_ui.state.initial import get_initial_state
        headers = get_initial_state()["tasks_headers"]
        keys = [h["key"] for h in headers]
        assert keys == self.EXPECTED_KEYS_ORDER

    def test_initial_state_no_gap_column(self):
        """FIX-COL-004: Gap column removed from initial.py."""
        from agent.governance_ui.state.initial import get_initial_state
        headers = get_initial_state()["tasks_headers"]
        keys = [h["key"] for h in headers]
        assert "gap_id" not in keys

    def test_initial_state_no_phase_column(self):
        """Phase column removed — hierarchy replaces flat phase labels."""
        from agent.governance_ui.state.initial import get_initial_state
        headers = get_initial_state()["tasks_headers"]
        keys = [h["key"] for h in headers]
        assert "phase" not in keys

    def test_initial_state_has_completed_column(self):
        """FIX-COL-005: Completed column present in initial.py."""
        from agent.governance_ui.state.initial import get_initial_state
        headers = get_initial_state()["tasks_headers"]
        keys = [h["key"] for h in headers]
        assert "completed_at" in keys

    def test_initial_state_has_workspace_column(self):
        """FIX-COL-002: Workspace column present in initial.py."""
        from agent.governance_ui.state.initial import get_initial_state
        headers = get_initial_state()["tasks_headers"]
        keys = [h["key"] for h in headers]
        assert "workspace_id" in keys

    def test_column_count_is_12(self):
        """Target: 12 columns (Phase 3 added Project from workspace→project_id)."""
        from agent.governance_ui.state.initial import get_initial_state
        headers = get_initial_state()["tasks_headers"]
        assert len(headers) == 12

    def test_summary_not_description(self):
        """FIX-COL-003: Summary column, not description."""
        from agent.governance_ui.state.initial import get_initial_state
        headers = get_initial_state()["tasks_headers"]
        keys = [h["key"] for h in headers]
        assert "summary" in keys
        assert "description" not in keys

    def test_has_project_column(self):
        """FIX-HIER-001: Project column derived from workspace→project_id."""
        from agent.governance_ui.state.initial import get_initial_state
        headers = get_initial_state()["tasks_headers"]
        keys = [h["key"] for h in headers]
        assert "project_name" in keys


# ── FIX-COL-006: workspace_id filter ─────────────────────────────────

class TestWorkspaceFilter:
    """Test workspace_id filter in service layer."""

    def test_apply_post_filters_workspace_id(self):
        """workspace_id filter returns only matching tasks."""
        from governance.services.tasks import _apply_post_filters
        tasks = [
            {"task_id": "T-1", "workspace_id": "sarvaja-platform"},
            {"task_id": "T-2", "workspace_id": "buntu-ger"},
            {"task_id": "T-3", "workspace_id": None},
            {"task_id": "T-4"},
        ]
        result = _apply_post_filters(tasks, workspace_id="sarvaja-platform")
        assert len(result) == 1
        assert result[0]["task_id"] == "T-1"

    def test_apply_post_filters_workspace_id_none_passes_all(self):
        """No workspace_id filter passes all tasks through."""
        from governance.services.tasks import _apply_post_filters
        tasks = [
            {"task_id": "T-1", "workspace_id": "sarvaja-platform"},
            {"task_id": "T-2", "workspace_id": None},
        ]
        result = _apply_post_filters(tasks, workspace_id=None)
        assert len(result) == 2

    @patch("governance.services.tasks.get_all_tasks_from_typedb")
    def test_list_tasks_passes_workspace_id(self, mock_get):
        """list_tasks forwards workspace_id to _apply_post_filters."""
        mock_get.return_value = [
            {"task_id": "T-1", "workspace_id": "proj-a"},
            {"task_id": "T-2", "workspace_id": "proj-b"},
        ]
        from governance.services.tasks import list_tasks
        result = list_tasks(workspace_id="proj-a")
        assert result["total"] == 1
        assert result["items"][0]["task_id"] == "T-1"

    @patch("governance.services.tasks.get_all_tasks_from_typedb")
    def test_list_tasks_no_workspace_filter(self, mock_get):
        """list_tasks without workspace_id returns all."""
        mock_get.return_value = [
            {"task_id": "T-1", "workspace_id": "proj-a"},
            {"task_id": "T-2", "workspace_id": "proj-b"},
        ]
        from governance.services.tasks import list_tasks
        result = list_tasks()
        assert result["total"] == 2


class TestWorkspaceFilterAPI:
    """Test workspace_id query param wired into API route."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client with tasks router."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from governance.routes.tasks.crud import router
        app = FastAPI()
        app.include_router(router, prefix="/api")
        return TestClient(app)

    @patch("governance.routes.tasks.crud.task_service.list_tasks")
    def test_workspace_id_query_param(self, mock_list, client):
        """GET /api/tasks?workspace_id=X forwards to service."""
        mock_list.return_value = {
            "items": [], "total": 0, "offset": 0,
            "limit": 50, "has_more": False,
        }
        resp = client.get("/api/tasks?workspace_id=sarvaja-platform")
        assert resp.status_code == 200
        mock_list.assert_called_once()
        call_kwargs = mock_list.call_args[1]
        assert call_kwargs["workspace_id"] == "sarvaja-platform"
