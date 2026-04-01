"""
Unit tests for Task Service Layer.

Per DOC-SIZE-01-v1: Tests for governance/services/tasks.py module.
Tests: _monitor, list_tasks, create_task, get_task.
P9: _get_active_session_id removed (BUG-SESSION-POISON-01).
"""

from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

_P = "governance.services.tasks"
_PQ = "governance.services.tasks_queries"


@pytest.fixture(autouse=True)
def _reset_stores():
    tasks = {}
    with patch(f"{_P}._tasks_store", tasks), \
         patch(f"{_PQ}._tasks_store", tasks), \
         patch(f"{_P}.record_audit"), \
         patch(f"{_P}.log_event"):
        yield tasks, {}


# ── _get_active_session_id (REMOVED — P9 BUG-SESSION-POISON-01) ──


class TestGetActiveSessionIdRemoved:
    """P9: _get_active_session_id removed (BUG-SESSION-POISON-01)."""
    def test_function_removed(self):
        from governance.services import tasks
        assert not hasattr(tasks, '_get_active_session_id')


# ── _monitor ─────────────────────────────────────────────────────


class TestMonitor:
    def test_success(self):
        from governance.services.tasks import _monitor
        with patch("governance.mcp_tools.common.log_monitor_event") as mock:
            _monitor("create", "T-1", source="test")
        mock.assert_called_once()

    def test_exception_silenced(self):
        from governance.services.tasks import _monitor
        with patch("governance.mcp_tools.common.log_monitor_event", side_effect=Exception("fail")):
            _monitor("create", "T-1")  # should not raise


# ── list_tasks ───────────────────────────────────────────────────


class TestListTasks:
    def test_returns_paginated(self, _reset_stores):
        from governance.services.tasks import list_tasks
        tasks_data = [
            {"task_id": "T-1", "status": "OPEN", "phase": "P10"},
            {"task_id": "T-2", "status": "DONE", "phase": "P11"},
        ]
        with patch(f"{_PQ}.get_all_tasks_from_typedb", return_value=tasks_data):
            result = list_tasks()
        assert result["total"] == 2
        assert result["has_more"] is False

    def test_pagination(self, _reset_stores):
        from governance.services.tasks import list_tasks
        tasks_data = [{"task_id": f"T-{i}", "status": "OPEN"} for i in range(5)]
        with patch(f"{_PQ}.get_all_tasks_from_typedb", return_value=tasks_data):
            result = list_tasks(offset=0, limit=2)
        assert len(result["items"]) == 2
        assert result["has_more"] is True

    def test_sorting_desc(self, _reset_stores):
        from governance.services.tasks import list_tasks
        tasks_data = [
            {"task_id": "T-A", "status": "OPEN"},
            {"task_id": "T-B", "status": "OPEN"},
        ]
        with patch(f"{_PQ}.get_all_tasks_from_typedb", return_value=tasks_data):
            result = list_tasks(sort_by="task_id", order="desc")
        assert result["items"][0]["task_id"] == "T-B"

    def test_invalid_sort_field(self, _reset_stores):
        from governance.services.tasks import list_tasks
        tasks_data = [{"task_id": "T-1", "status": "OPEN"}]
        with patch(f"{_PQ}.get_all_tasks_from_typedb", return_value=tasks_data):
            result = list_tasks(sort_by="invalid_field")
        assert result["total"] == 1


# ── create_task ──────────────────────────────────────────────────


class TestCreateTask:
    def test_typedb_success(self, _reset_stores):
        from governance.services.tasks import create_task
        client = MagicMock()
        client.get_task.return_value = None
        client.insert_task.return_value = {"task_id": "T-NEW", "description": "d", "status": "OPEN", "phase": "P10"}
        with patch(f"{_P}.get_typedb_client", return_value=client), \
             patch(f"{_P}.task_to_response", side_effect=lambda x: x), \
             patch(f"{_P}._monitor"):
            result = create_task(task_id="T-NEW", description="d")
        assert result["task_id"] == "T-NEW"

    def test_typedb_duplicate(self, _reset_stores):
        from governance.services.tasks import create_task
        client = MagicMock()
        client.get_task.return_value = {"task_id": "T-DUP"}
        with patch(f"{_P}.get_typedb_client", return_value=client):
            with pytest.raises(ValueError, match="already exists"):
                create_task(task_id="T-DUP", description="d")

    def test_fallback_success(self, _reset_stores):
        from governance.services.tasks import create_task
        tasks, _ = _reset_stores
        with patch(f"{_P}.get_typedb_client", return_value=None), \
             patch(f"{_P}._monitor"):
            result = create_task(task_id="T-FB", description="d")
        assert result["task_id"] == "T-FB"
        assert "T-FB" in tasks

    def test_fallback_duplicate(self, _reset_stores):
        from governance.services.tasks import create_task
        tasks, _ = _reset_stores
        tasks["T-DUP"] = {"task_id": "T-DUP"}
        with patch(f"{_P}.get_typedb_client", return_value=None):
            with pytest.raises(ValueError, match="already exists"):
                create_task(task_id="T-DUP", description="d")

    def test_no_auto_link_without_explicit_sessions(self, _reset_stores):
        """P9: No auto-linking; linked_sessions empty without explicit param."""
        from governance.services.tasks import create_task
        with patch(f"{_P}.get_typedb_client", return_value=None), \
             patch(f"{_P}._monitor"):
            result = create_task(task_id="T-LINK", description="d")
        assert result["linked_sessions"] == []

    def test_typedb_insert_failure_falls_back(self, _reset_stores):
        from governance.services.tasks import create_task
        tasks, _ = _reset_stores
        client = MagicMock()
        client.get_task.return_value = None
        client.insert_task.side_effect = Exception("db error")
        with patch(f"{_P}.get_typedb_client", return_value=client), \
             patch(f"{_P}._monitor"):
            result = create_task(task_id="T-ERR", description="d")
        assert "T-ERR" in tasks

    def test_typedb_insert_returns_none_falls_back(self, _reset_stores):
        from governance.services.tasks import create_task
        tasks, _ = _reset_stores
        client = MagicMock()
        client.get_task.return_value = None
        client.insert_task.return_value = None
        with patch(f"{_P}.get_typedb_client", return_value=client), \
             patch(f"{_P}._monitor"):
            result = create_task(task_id="T-NULL", description="d")
        assert "T-NULL" in tasks


# ── get_task ─────────────────────────────────────────────────────


class TestGetTask:
    def test_typedb_found(self, _reset_stores):
        from governance.services.tasks import get_task
        client = MagicMock()
        client.get_task.return_value = {"task_id": "T-1"}
        with patch(f"{_PQ}.get_typedb_client", return_value=client), \
             patch(f"{_PQ}.task_to_response", side_effect=lambda x: x):
            result = get_task("T-1")
        assert result["task_id"] == "T-1"

    def test_typedb_not_found(self, _reset_stores):
        from governance.services.tasks import get_task
        client = MagicMock()
        client.get_task.return_value = None
        with patch(f"{_PQ}.get_typedb_client", return_value=client):
            result = get_task("T-MISS")
        assert result is None

    def test_fallback_found(self, _reset_stores):
        from governance.services.tasks import get_task
        tasks, _ = _reset_stores
        tasks["T-MEM"] = {"task_id": "T-MEM", "description": "memory"}
        with patch(f"{_PQ}.get_typedb_client", return_value=None):
            result = get_task("T-MEM")
        assert result["task_id"] == "T-MEM"

    def test_typedb_error_fallback(self, _reset_stores):
        from governance.services.tasks import get_task
        tasks, _ = _reset_stores
        tasks["T-FB"] = {"task_id": "T-FB"}
        client = MagicMock()
        client.get_task.side_effect = Exception("db error")
        with patch(f"{_PQ}.get_typedb_client", return_value=client):
            result = get_task("T-FB")
        assert result["task_id"] == "T-FB"

    def test_not_found_anywhere(self, _reset_stores):
        from governance.services.tasks import get_task
        with patch(f"{_PQ}.get_typedb_client", return_value=None):
            result = get_task("T-NOWHERE")
        assert result is None
