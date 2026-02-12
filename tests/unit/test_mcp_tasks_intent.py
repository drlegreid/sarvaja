"""
Unit tests for Task Intent/Outcome MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/tasks_intent.py module.
Tests: task_capture_intent(), task_capture_outcome().
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from governance.mcp_tools.tasks_intent import register_tasks_intent_tools


def _json_format(data, **kwargs):
    return json.dumps(data, indent=2, default=str)


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, name=None):
        if callable(name):
            self.tools[name.__name__] = name
            return name

        def decorator(fn):
            key = name if name else fn.__name__
            self.tools[key] = fn
            return fn
        return decorator


def _register():
    mcp = _CaptureMCP()
    register_tasks_intent_tools(mcp)
    return mcp


@pytest.fixture(autouse=True)
def _force_json():
    with patch(
        "governance.mcp_tools.tasks_intent.format_mcp_result",
        side_effect=_json_format,
    ):
        yield


class TestRegistration:
    def test_registers_two_tools(self):
        mcp = _register()
        assert "task_capture_intent" in mcp.tools
        assert "task_capture_outcome" in mcp.tools


class TestTaskCaptureIntent:
    """Tests for task_capture_intent()."""

    @patch("governance.services.tasks.get_task", return_value=None)
    def test_task_not_found(self, mock_get):
        mcp = _register()
        result = json.loads(mcp.tools["task_capture_intent"](
            task_id="MISSING", goal="test"
        ))
        assert "error" in result

    @patch("governance.mcp_tools.tasks_intent._store_task_section")
    @patch("governance.services.tasks.get_task", return_value={"task_id": "T-1"})
    def test_success(self, mock_get, mock_store):
        mcp = _register()
        result = json.loads(mcp.tools["task_capture_intent"](
            task_id="T-1", goal="Fix bug"
        ))
        assert result["task_id"] == "T-1"
        assert result["action"] == "intent_captured"
        assert result["goal"] == "Fix bug"
        mock_store.assert_called_once()

    @patch("governance.mcp_tools.tasks_intent._store_task_section")
    @patch("governance.services.tasks.get_task", return_value={"task_id": "T-1"})
    def test_with_steps(self, mock_get, mock_store):
        mcp = _register()
        result = json.loads(mcp.tools["task_capture_intent"](
            task_id="T-1", goal="Fix", planned_steps="Read code, Find bug, Fix"
        ))
        assert result["steps_count"] == 3

    @patch("governance.mcp_tools.tasks_intent._store_task_section")
    @patch("governance.services.tasks.get_task", return_value={"task_id": "T-1"})
    def test_with_context(self, mock_get, mock_store):
        mcp = _register()
        result = json.loads(mcp.tools["task_capture_intent"](
            task_id="T-1", goal="Test", context="GAP-001"
        ))
        assert result["action"] == "intent_captured"


class TestTaskCaptureOutcome:
    """Tests for task_capture_outcome()."""

    @patch("governance.services.tasks.get_task", return_value=None)
    def test_task_not_found(self, mock_get):
        mcp = _register()
        result = json.loads(mcp.tools["task_capture_outcome"](
            task_id="MISSING", status="DONE", achieved="nothing"
        ))
        assert "error" in result

    @patch("governance.mcp_tools.tasks_intent._store_task_section")
    @patch("governance.services.tasks.get_task", return_value={"task_id": "T-1"})
    def test_success(self, mock_get, mock_store):
        mcp = _register()
        result = json.loads(mcp.tools["task_capture_outcome"](
            task_id="T-1", status="DONE", achieved="Fixed the bug"
        ))
        assert result["task_id"] == "T-1"
        assert result["action"] == "outcome_captured"
        assert result["status"] == "DONE"

    @patch("governance.mcp_tools.tasks_intent._store_task_section")
    @patch("governance.services.tasks.get_task", return_value={"task_id": "T-1"})
    def test_with_deferred(self, mock_get, mock_store):
        mcp = _register()
        result = json.loads(mcp.tools["task_capture_outcome"](
            task_id="T-1", status="PARTIAL", achieved="Half done",
            deferred="Item A, Item B"
        ))
        assert result["deferred_count"] == 2

    @patch("governance.mcp_tools.tasks_intent._store_task_section")
    @patch("governance.services.tasks.get_task", return_value={"task_id": "T-1"})
    def test_with_discoveries(self, mock_get, mock_store):
        mcp = _register()
        result = json.loads(mcp.tools["task_capture_outcome"](
            task_id="T-1", status="DONE", achieved="OK",
            discoveries="GAP-NEW-001, Pattern found"
        ))
        assert result["discoveries_count"] == 2
