"""DSP-13: MCP Taxonomy V2 Flow Tests.

Tests taxonomy V2 features through the MCP tools layer:
1. task_create with deprecated type aliases (gap→bug) via service layer
2. task_create with orthogonal tag dimensions (layer, concern, method)
3. task_update with CLOSED→DONE normalization
4. task_update passes taxonomy fields to service layer

Pattern: MCP tools accept strings directly (no Pydantic Literal).
Alias normalization happens at the service layer, not MCP layer.
"""
import json
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.tasks_crud import register_task_crud_tools

_MOD = "governance.mcp_tools.tasks_crud"


def _json_fmt(data):
    return json.dumps(data, indent=2, default=str)


def _register_tools():
    mcp = MagicMock()
    tools = {}

    def tool_decorator():
        def wrapper(func):
            tools[func.__name__] = func
            return func
        return wrapper

    mcp.tool = tool_decorator
    with patch(f"{_MOD}.register_task_verify_tools"):
        register_task_crud_tools(mcp)
    return tools


# =============================================================================
# 1. MCP task_create with Alias Normalization
# =============================================================================


class TestMCPTaskCreateAliases:
    """MCP task_create routes through service layer which normalizes aliases."""

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch("governance.services.tasks.create_task")
    def test_gap_type_passed_to_service(self, mock_svc, mock_fmt, mock_log):
        """MCP passes task_type='gap' to service; service normalizes to 'bug'."""
        tools = _register_tools()
        mock_svc.return_value = {"task_id": "BUG-901", "task_type": "bug"}

        result = json.loads(tools["task_create"](
            name="Fix the gap",
            task_id="BUG-901",
            task_type="gap",
        ))
        # Service layer was called with gap (MCP passes through)
        call_kwargs = mock_svc.call_args[1]
        assert call_kwargs["task_type"] == "gap"
        # Service normalizes it — response shows "bug"
        assert result["task_type"] == "bug"

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch("governance.services.tasks.create_task")
    def test_story_type_passed_to_service(self, mock_svc, mock_fmt, mock_log):
        tools = _register_tools()
        mock_svc.return_value = {"task_id": "FEAT-901", "task_type": "feature"}

        result = json.loads(tools["task_create"](
            name="New story",
            task_id="FEAT-901",
            task_type="story",
        ))
        call_kwargs = mock_svc.call_args[1]
        assert call_kwargs["task_type"] == "story"
        assert result["task_type"] == "feature"

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch("governance.services.tasks.create_task")
    def test_canonical_type_passthrough(self, mock_svc, mock_fmt, mock_log):
        tools = _register_tools()
        mock_svc.return_value = {"task_id": "BUG-902", "task_type": "bug"}

        result = json.loads(tools["task_create"](
            name="A bug",
            task_id="BUG-902",
            task_type="bug",
        ))
        call_kwargs = mock_svc.call_args[1]
        assert call_kwargs["task_type"] == "bug"
        assert result["task_type"] == "bug"


# =============================================================================
# 2. MCP task_create with Tag Dimensions
# =============================================================================


class TestMCPTaskCreateTags:
    """MCP task_create passes tag dimensions to service layer."""

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch("governance.services.tasks.create_task")
    def test_tags_passed_to_service(self, mock_svc, mock_fmt, mock_log):
        tools = _register_tools()
        mock_svc.return_value = {
            "task_id": "BUG-903",
            "layer": "api", "concern": "security", "method": "automated",
        }

        result = json.loads(tools["task_create"](
            name="API security fix",
            task_id="BUG-903",
            task_type="bug",
            layer="api",
            concern="security",
            method="automated",
        ))
        call_kwargs = mock_svc.call_args[1]
        assert call_kwargs["layer"] == "api"
        assert call_kwargs["concern"] == "security"
        assert call_kwargs["method"] == "automated"
        assert result["layer"] == "api"

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch("governance.services.tasks.create_task")
    def test_none_tags_passed_as_none(self, mock_svc, mock_fmt, mock_log):
        tools = _register_tools()
        mock_svc.return_value = {"task_id": "CHORE-903"}

        tools["task_create"](
            name="Simple task",
            task_id="CHORE-903",
            task_type="chore",
        )
        call_kwargs = mock_svc.call_args[1]
        assert call_kwargs["layer"] is None
        assert call_kwargs["concern"] is None
        assert call_kwargs["method"] is None


# =============================================================================
# 3. MCP task_update with CLOSED→DONE
# =============================================================================


class TestMCPTaskUpdateNormalization:
    """MCP task_update routes to service which normalizes CLOSED→DONE."""

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.svc_update_task")
    def test_closed_status_sent_to_service(self, mock_svc, mock_fmt, mock_log):
        """Service layer normalizes CLOSED→DONE."""
        tools = _register_tools()
        mock_svc.return_value = {"task_id": "CHORE-904", "status": "DONE"}

        result = json.loads(tools["task_update"](
            task_id="CHORE-904",
            status="CLOSED",
        ))
        call_kwargs = mock_svc.call_args[1]
        assert call_kwargs["status"] == "CLOSED"
        assert result["status"] == "DONE"


# =============================================================================
# 4. MCP task_update passes taxonomy V2 fields
# =============================================================================


class TestMCPTaskUpdateTaxonomy:
    """MCP task_update passes taxonomy V2 fields to service."""

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.svc_update_task")
    def test_tags_passed_to_update(self, mock_svc, mock_fmt, mock_log):
        tools = _register_tools()
        mock_svc.return_value = {
            "task_id": "BUG-905",
            "layer": "data", "concern": "performance",
        }

        result = json.loads(tools["task_update"](
            task_id="BUG-905",
            layer="data",
            concern="performance",
        ))
        call_kwargs = mock_svc.call_args[1]
        assert call_kwargs["layer"] == "data"
        assert call_kwargs["concern"] == "performance"

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.svc_update_task")
    def test_resolution_notes_passed(self, mock_svc, mock_fmt, mock_log):
        tools = _register_tools()
        mock_svc.return_value = {
            "task_id": "BUG-906",
            "resolution_notes": "Fixed via hotpatch",
        }

        result = json.loads(tools["task_update"](
            task_id="BUG-906",
            resolution_notes="Fixed via hotpatch",
        ))
        call_kwargs = mock_svc.call_args[1]
        assert call_kwargs["resolution_notes"] == "Fixed via hotpatch"


# =============================================================================
# 5. MCP task_create Validation Error Handling
# =============================================================================


class TestMCPTaskCreateValidation:
    """MCP returns structured errors on validation failure."""

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch("governance.services.tasks.create_task")
    def test_validation_error_returned_as_json(self, mock_svc, mock_fmt):
        tools = _register_tools()
        mock_svc.side_effect = ValueError("Invalid agent_id 'bad-agent'")

        result = json.loads(tools["task_create"](
            name="Bad test",
            task_id="BUG-999",
        ))
        assert "error" in result
        assert result["type"] == "validation"

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch("governance.services.tasks.create_task")
    def test_generic_error_returned(self, mock_svc, mock_fmt):
        tools = _register_tools()
        mock_svc.side_effect = RuntimeError("TypeDB down")

        result = json.loads(tools["task_create"](
            name="Fail test",
            task_id="BUG-998",
        ))
        assert "error" in result
