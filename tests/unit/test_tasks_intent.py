"""
Unit tests for Task Intent/Outcome Capture MCP Tools.

Per EPIC-H: Tests for task_capture_intent, task_capture_outcome,
and _store_task_section helper.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from governance.mcp_tools.tasks_intent import (
    _store_task_section,
    register_tasks_intent_tools,
)


def _json_format(data, **kw):
    return json.dumps(data, default=str)


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@pytest.fixture(autouse=True)
def _force_json():
    with patch("governance.mcp_tools.tasks_intent.format_mcp_result", side_effect=_json_format):
        yield


@pytest.fixture
def mcp_tools():
    mcp = _CaptureMCP()
    register_tasks_intent_tools(mcp)
    return mcp.tools


# ---------------------------------------------------------------------------
# _store_task_section
# ---------------------------------------------------------------------------
class TestStoreTaskSection:
    """Tests for _store_task_section() helper."""

    def test_stores_to_memory_fallback(self):
        """When TypeDB unavailable, stores to in-memory _tasks_store."""
        mock_store = {"T-1": {"status": "OPEN"}}
        with patch("governance.mcp_tools.tasks_intent._store_task_section.__module__"):
            pass  # just ensure importable

        # Direct test via _tasks_store manipulation
        from governance import stores
        original = getattr(stores, "_tasks_store", {})
        try:
            stores._tasks_store = {"T-1": {"status": "OPEN"}}
            _store_task_section("T-1", "intent", {"goal": "test"})
            assert "details" in stores._tasks_store["T-1"]
            assert stores._tasks_store["T-1"]["details"]["intent"]["goal"] == "test"
        finally:
            stores._tasks_store = original

    def test_nonexistent_task_silent(self):
        """When task not in memory store, silently does nothing."""
        from governance import stores
        original = getattr(stores, "_tasks_store", {})
        try:
            stores._tasks_store = {}
            _store_task_section("NONEXIST", "intent", {"goal": "test"})
            # No error raised
        finally:
            stores._tasks_store = original


# ---------------------------------------------------------------------------
# task_capture_intent
# ---------------------------------------------------------------------------
class TestTaskCaptureIntent:
    """Tests for task_capture_intent() tool."""

    @patch("governance.services.tasks.get_task")
    def test_task_not_found(self, mock_get, mcp_tools):
        mock_get.return_value = None
        result = json.loads(mcp_tools["task_capture_intent"](
            task_id="T-999", goal="test",
        ))
        assert "error" in result
        assert "not found" in result["error"]

    @patch("governance.services.tasks.get_task")
    def test_captures_intent(self, mock_get, mcp_tools):
        mock_get.return_value = {"task_id": "T-1", "status": "OPEN"}
        result = json.loads(mcp_tools["task_capture_intent"](
            task_id="T-1", goal="Fix login bug",
            planned_steps="analyze,fix,test", context="GAP-AUTH-001",
        ))
        assert result["task_id"] == "T-1"
        assert result["action"] == "intent_captured"
        assert result["goal"] == "Fix login bug"
        assert result["steps_count"] == 3

    @patch("governance.services.tasks.get_task")
    def test_no_planned_steps(self, mock_get, mcp_tools):
        mock_get.return_value = {"task_id": "T-1"}
        result = json.loads(mcp_tools["task_capture_intent"](
            task_id="T-1", goal="Quick fix",
        ))
        assert result["steps_count"] == 0

    @patch("governance.services.tasks.get_task")
    def test_empty_planned_steps(self, mock_get, mcp_tools):
        mock_get.return_value = {"task_id": "T-1"}
        result = json.loads(mcp_tools["task_capture_intent"](
            task_id="T-1", goal="Quick fix", planned_steps="",
        ))
        assert result["steps_count"] == 0


# ---------------------------------------------------------------------------
# task_capture_outcome
# ---------------------------------------------------------------------------
class TestTaskCaptureOutcome:
    """Tests for task_capture_outcome() tool."""

    @patch("governance.services.tasks.get_task")
    def test_task_not_found(self, mock_get, mcp_tools):
        mock_get.return_value = None
        result = json.loads(mcp_tools["task_capture_outcome"](
            task_id="T-999", status="DONE", achieved="nothing",
        ))
        assert "error" in result

    @patch("governance.services.tasks.get_task")
    def test_captures_outcome(self, mock_get, mcp_tools):
        mock_get.return_value = {"task_id": "T-1"}
        result = json.loads(mcp_tools["task_capture_outcome"](
            task_id="T-1", status="DONE",
            achieved="Fixed login flow",
            deferred="refactor auth module",
            discoveries="GAP-SESSION-LEAK",
            files_modified="auth.py,login.py",
        ))
        assert result["task_id"] == "T-1"
        assert result["action"] == "outcome_captured"
        assert result["status"] == "DONE"
        assert result["deferred_count"] == 1
        assert result["discoveries_count"] == 1

    @patch("governance.services.tasks.get_task")
    def test_no_optional_fields(self, mock_get, mcp_tools):
        mock_get.return_value = {"task_id": "T-1"}
        result = json.loads(mcp_tools["task_capture_outcome"](
            task_id="T-1", status="PARTIAL", achieved="Half done",
        ))
        assert result["deferred_count"] == 0
        assert result["discoveries_count"] == 0

    @patch("governance.services.tasks.get_task")
    def test_multiple_deferred(self, mock_get, mcp_tools):
        mock_get.return_value = {"task_id": "T-1"}
        result = json.loads(mcp_tools["task_capture_outcome"](
            task_id="T-1", status="PARTIAL", achieved="Some",
            deferred="item1, item2, item3",
        ))
        assert result["deferred_count"] == 3
