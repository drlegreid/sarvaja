"""
Tests for task filters: task_type, priority, created_at, completed_at.

Phase 9 EPIC-GOV-TASKS-V2: Add 6 filter dimensions to API + service + UI.
Existing filters (status, phase) already work — these tests cover NEW filters.

TDD: Tests define the contract. Per DOC-SIZE-01-v1: <=300 lines.
"""

from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

_SVC = "governance.services.tasks"
_TDA = "governance.stores.typedb_access"


@pytest.fixture(autouse=True)
def _reset_stores():
    with patch(f"{_SVC}._tasks_store", {}) as tasks, \
         patch(f"{_SVC}.record_audit"), \
         patch(f"{_SVC}.log_event"):
        yield tasks, {}


def _make_task_entity(task_id, **overrides):
    """Create a mock Task entity."""
    defaults = dict(
        name="Test", status="OPEN", phase="P9", priority="MEDIUM",
        task_type="chore", agent_id=None, body=None, description="Test",
        resolution=None, gap_id=None, evidence=None, document_path=None,
        linked_rules=[], linked_sessions=[], linked_commits=[],
        linked_documents=[], workspace_id=None,
        created_at=datetime(2026, 3, 21, 10, 0, 0),
        claimed_at=None, completed_at=None,
    )
    defaults.update(overrides)
    t = MagicMock()
    for k, v in defaults.items():
        setattr(t, k, v)
    t.id = task_id
    return t


# ── Filter by task_type ──


class TestFilterByTaskType:
    def test_list_tasks_accepts_task_type_param(self, _reset_stores):
        """list_tasks() must accept task_type filter parameter."""
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity("BUG-1", task_type="bug"),
            _make_task_entity("FEAT-1", task_type="feature"),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(task_type="bug")

        items = result["items"]
        assert all(t.get("task_type") == "bug" for t in items)
        assert len(items) == 1

    def test_task_type_none_returns_all(self, _reset_stores):
        """task_type=None should return all task types."""
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity("BUG-1", task_type="bug"),
            _make_task_entity("FEAT-1", task_type="feature"),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(task_type=None)

        assert len(result["items"]) == 2


# ── Filter by priority ──


class TestFilterByPriority:
    def test_list_tasks_accepts_priority_param(self, _reset_stores):
        """list_tasks() must accept priority filter parameter."""
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity("T-1", priority="CRITICAL"),
            _make_task_entity("T-2", priority="LOW"),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(priority="CRITICAL")

        items = result["items"]
        assert all(t.get("priority") == "CRITICAL" for t in items)
        assert len(items) == 1


# ── Filter by created_at date range ──


class TestFilterByCreatedAt:
    def test_created_after_filters_tasks(self, _reset_stores):
        """list_tasks(created_after=...) excludes tasks created before."""
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity("T-OLD", created_at=datetime(2026, 3, 1)),
            _make_task_entity("T-NEW", created_at=datetime(2026, 3, 21)),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(created_after="2026-03-15")

        ids = {t["task_id"] for t in result["items"]}
        assert "T-NEW" in ids
        assert "T-OLD" not in ids

    def test_created_before_filters_tasks(self, _reset_stores):
        """list_tasks(created_before=...) excludes tasks created after."""
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity("T-OLD", created_at=datetime(2026, 3, 1)),
            _make_task_entity("T-NEW", created_at=datetime(2026, 3, 21)),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(created_before="2026-03-15")

        ids = {t["task_id"] for t in result["items"]}
        assert "T-OLD" in ids
        assert "T-NEW" not in ids


# ── Filter by completed_at date range ──


class TestFilterByCompletedAt:
    def test_completed_after_filters_tasks(self, _reset_stores):
        """list_tasks(completed_after=...) excludes tasks completed before."""
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity("T-1", completed_at=datetime(2026, 3, 1)),
            _make_task_entity("T-2", completed_at=datetime(2026, 3, 21)),
            _make_task_entity("T-3", completed_at=None),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(completed_after="2026-03-15")

        ids = {t["task_id"] for t in result["items"]}
        assert "T-2" in ids
        assert "T-1" not in ids
        assert "T-3" not in ids

    def test_completed_before_filters_tasks(self, _reset_stores):
        """list_tasks(completed_before=...) excludes tasks completed after."""
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity("T-1", completed_at=datetime(2026, 3, 1)),
            _make_task_entity("T-2", completed_at=datetime(2026, 3, 21)),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(completed_before="2026-03-15")

        ids = {t["task_id"] for t in result["items"]}
        assert "T-1" in ids
        assert "T-2" not in ids


# ── Combined filters ──


class TestCombinedFilters:
    def test_task_type_and_priority(self, _reset_stores):
        """Combined task_type + priority filters narrow results."""
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity("T-1", task_type="bug", priority="CRITICAL"),
            _make_task_entity("T-2", task_type="bug", priority="LOW"),
            _make_task_entity("T-3", task_type="feature", priority="CRITICAL"),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(task_type="bug", priority="CRITICAL")

        ids = {t["task_id"] for t in result["items"]}
        assert ids == {"T-1"}

    def test_all_filters_together(self, _reset_stores):
        """All 6 filters applied simultaneously."""
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity(
                "MATCH", task_type="bug", priority="HIGH",
                status="DONE", phase="P9",
                created_at=datetime(2026, 3, 20),
                completed_at=datetime(2026, 3, 21),
            ),
            _make_task_entity(
                "MISS", task_type="feature", priority="LOW",
                status="OPEN", phase="P1",
                created_at=datetime(2026, 1, 1),
                completed_at=None,
            ),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(
                task_type="bug", priority="HIGH",
                status="DONE", phase="P9",
                created_after="2026-03-15",
                completed_after="2026-03-15",
            )

        ids = {t["task_id"] for t in result["items"]}
        assert ids == {"MATCH"}


# ── API route accepts new filter query params ──


class TestAPIRouteFilterParams:
    def test_route_has_task_type_param(self):
        """GET /api/tasks must accept task_type query param."""
        import inspect
        from governance.routes.tasks.crud import list_tasks as route_fn
        sig = inspect.signature(route_fn)
        assert "task_type" in sig.parameters

    def test_route_has_priority_param(self):
        """GET /api/tasks must accept priority query param."""
        import inspect
        from governance.routes.tasks.crud import list_tasks as route_fn
        sig = inspect.signature(route_fn)
        assert "priority" in sig.parameters

    def test_route_has_created_after_param(self):
        """GET /api/tasks must accept created_after query param."""
        import inspect
        from governance.routes.tasks.crud import list_tasks as route_fn
        sig = inspect.signature(route_fn)
        assert "created_after" in sig.parameters

    def test_route_has_created_before_param(self):
        """GET /api/tasks must accept created_before query param."""
        import inspect
        from governance.routes.tasks.crud import list_tasks as route_fn
        sig = inspect.signature(route_fn)
        assert "created_before" in sig.parameters

    def test_route_has_completed_after_param(self):
        """GET /api/tasks must accept completed_after query param."""
        import inspect
        from governance.routes.tasks.crud import list_tasks as route_fn
        sig = inspect.signature(route_fn)
        assert "completed_after" in sig.parameters

    def test_route_has_completed_before_param(self):
        """GET /api/tasks must accept completed_before query param."""
        import inspect
        from governance.routes.tasks.crud import list_tasks as route_fn
        sig = inspect.signature(route_fn)
        assert "completed_before" in sig.parameters


# ── Dashboard controller passes new filters ──


class TestDashboardControllerFilters:
    def test_controller_references_task_type_filter(self):
        """load_tasks_page must pass task_type filter to API."""
        import inspect
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        source = inspect.getsource(register_tasks_controllers)
        assert "tasks_type_filter" in source or "task_type" in source

    def test_controller_references_priority_filter(self):
        """load_tasks_page must pass priority filter to API."""
        import inspect
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        source = inspect.getsource(register_tasks_controllers)
        assert "tasks_priority_filter" in source or "priority" in source
