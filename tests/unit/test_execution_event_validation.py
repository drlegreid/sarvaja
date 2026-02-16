"""TDD Tests: Task execution event_type validation.

Gap: event_type in POST /tasks/{id}/execution accepts arbitrary strings.
Fix: Validate against allowed event types, return 422 for invalid.
"""
from unittest.mock import patch, MagicMock

import pytest


VALID_EVENT_TYPES = {"claimed", "started", "progress", "delegated", "completed", "failed", "evidence"}


class TestEventTypeValidation:
    """POST /tasks/{id}/execution rejects invalid event_type."""

    @patch("governance.routes.tasks.execution.get_typedb_client")
    @patch("governance.routes.tasks.execution.record_audit")
    def test_valid_event_type_accepted(self, mock_audit, mock_client_fn):
        """Valid event types are accepted (201)."""
        mock_client_fn.return_value = None
        from governance.stores import _tasks_store
        from governance.routes.tasks.execution import add_task_execution_event
        import asyncio

        task_id = "T-EVT-VALID-001"
        _tasks_store[task_id] = {"task_id": task_id, "status": "IN_PROGRESS"}

        try:
            for evt in VALID_EVENT_TYPES:
                result = asyncio.get_event_loop().run_until_complete(
                    add_task_execution_event(task_id, event_type=evt, message="test", agent_id=None)
                )
                assert result.event_type == evt
        finally:
            _tasks_store.pop(task_id, None)

    @patch("governance.routes.tasks.execution.get_typedb_client")
    def test_invalid_event_type_rejected(self, mock_client_fn):
        """Invalid event_type returns 422."""
        mock_client_fn.return_value = None
        from governance.stores import _tasks_store
        from governance.routes.tasks.execution import add_task_execution_event
        from fastapi import HTTPException
        import asyncio

        task_id = "T-EVT-INVALID-001"
        _tasks_store[task_id] = {"task_id": task_id, "status": "IN_PROGRESS"}

        try:
            with pytest.raises(HTTPException) as exc_info:
                asyncio.get_event_loop().run_until_complete(
                    add_task_execution_event(task_id, event_type="invalid_xyz", message="test", agent_id=None)
                )
            assert exc_info.value.status_code == 422
            assert "event_type" in str(exc_info.value.detail).lower()
        finally:
            _tasks_store.pop(task_id, None)

    @patch("governance.routes.tasks.execution.get_typedb_client")
    def test_empty_event_type_rejected(self, mock_client_fn):
        """Empty string event_type returns 422."""
        mock_client_fn.return_value = None
        from governance.stores import _tasks_store
        from governance.routes.tasks.execution import add_task_execution_event
        from fastapi import HTTPException
        import asyncio

        task_id = "T-EVT-EMPTY-001"
        _tasks_store[task_id] = {"task_id": task_id, "status": "IN_PROGRESS"}

        try:
            with pytest.raises(HTTPException) as exc_info:
                asyncio.get_event_loop().run_until_complete(
                    add_task_execution_event(task_id, event_type="", message="test", agent_id=None)
                )
            assert exc_info.value.status_code == 422
        finally:
            _tasks_store.pop(task_id, None)
