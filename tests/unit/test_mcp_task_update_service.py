"""
Unit tests for MCP task_update routing through service layer.

Phase 2 of EPIC-GOV-TASKS-V2: Auto-Linking + Service Layer Parity.

BDD Scenarios:
  - MCP task_update routes through service layer (not client directly)
  - Service layer auto-linking triggers via MCP path
  - Error handling returns formatted MCP error
  - No-update-fields rejection still works
"""

import json
from unittest.mock import patch, MagicMock

import pytest

_MOD = "governance.mcp_tools.tasks_crud"


def _json_fmt(data):
    return json.dumps(data, indent=2, default=str)


def _register_tools():
    """Register MCP tools and capture them in a dict."""
    from governance.mcp_tools.tasks_crud import register_task_crud_tools

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


# ── Scenario: MCP task_update routes through service layer ──


class TestMCPTaskUpdateServiceRouting:
    """task_update MCP tool uses service update_task, not client directly."""

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_routes_through_service_layer(self, mock_fmt, mock_log):
        """task_update calls service update_task instead of client.update_task."""
        tools = _register_tools()
        task_update = tools["task_update"]

        mock_result = {
            "task_id": "T-1", "description": "Updated", "status": "IN_PROGRESS",
            "phase": "P10", "linked_sessions": ["SESSION-AUTO"],
        }

        with patch(
            f"{_MOD}.svc_update_task",
            return_value=mock_result,
        ) as mock_svc:
            result = task_update(task_id="T-1", status="IN_PROGRESS")

        mock_svc.assert_called_once_with(
            task_id="T-1",
            status="IN_PROGRESS",
            description=None,
            phase=None,
            priority=None,
            task_type=None,
            source="mcp",
        )
        parsed = json.loads(result)
        assert parsed["task_id"] == "T-1"
        assert "updated successfully" in parsed["message"]

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_does_not_call_client_directly(self, mock_fmt, mock_log):
        """Verify typedb_client context manager is NOT used by task_update."""
        tools = _register_tools()
        task_update = tools["task_update"]

        mock_result = {"task_id": "T-2", "status": "DONE"}

        with patch(
            f"{_MOD}.svc_update_task",
            return_value=mock_result,
        ), patch(
            f"{_MOD}.typedb_client",
        ) as mock_ctx:
            task_update(task_id="T-2", status="DONE")

        # typedb_client context manager should NOT be called by task_update
        mock_ctx.assert_not_called()


# ── Scenario: Service auto-linking triggers via MCP ──────


class TestMCPAutoLinkViaService:
    """Auto-linking fires when MCP task_update routes through service."""

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_autolinked_session_in_response(self, mock_fmt, mock_log):
        """Service layer auto-links session, and MCP returns it."""
        tools = _register_tools()
        task_update = tools["task_update"]

        mock_result = {
            "task_id": "T-3", "status": "IN_PROGRESS",
            "linked_sessions": ["SESSION-2026-03-20-AUTO"],
        }

        with patch(
            f"{_MOD}.svc_update_task",
            return_value=mock_result,
        ):
            result = task_update(task_id="T-3", status="IN_PROGRESS")

        parsed = json.loads(result)
        assert "SESSION-2026-03-20-AUTO" in parsed.get("linked_sessions", [])


# ── Scenario: Error handling ─────────────────────────────


class TestMCPTaskUpdateErrors:
    """Error cases for MCP task_update."""

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_no_fields_rejects(self, mock_fmt):
        """No update fields provided → error."""
        tools = _register_tools()
        task_update = tools["task_update"]

        result = task_update(task_id="T-4")
        parsed = json.loads(result)
        assert "error" in parsed
        assert "No update fields" in parsed["error"]

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_service_exception_returns_error(self, mock_fmt, mock_log):
        """Service layer exception → formatted MCP error."""
        tools = _register_tools()
        task_update = tools["task_update"]

        with patch(
            f"{_MOD}.svc_update_task",
            side_effect=RuntimeError("DB gone"),
        ):
            result = task_update(task_id="T-5", status="DONE")

        parsed = json.loads(result)
        assert "error" in parsed
        assert "RuntimeError" in parsed["error"]

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_task_not_found_returns_error(self, mock_fmt, mock_log):
        """Service returns None (not found) → error response."""
        tools = _register_tools()
        task_update = tools["task_update"]

        with patch(
            f"{_MOD}.svc_update_task",
            return_value=None,
        ):
            result = task_update(task_id="T-GHOST", status="DONE")

        parsed = json.loads(result)
        assert "error" in parsed


# ── Scenario: Monitor event fires correctly ──────────────


class TestMCPTaskUpdateMonitoring:
    """MCP task_update fires monitoring events."""

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_monitor_event_on_success(self, mock_fmt, mock_log):
        tools = _register_tools()
        task_update = tools["task_update"]

        mock_result = {"task_id": "T-6", "status": "IN_PROGRESS"}

        with patch(
            f"{_MOD}.svc_update_task",
            return_value=mock_result,
        ):
            task_update(task_id="T-6", status="IN_PROGRESS")

        mock_log.assert_called()
        call_details = mock_log.call_args[1]["details"]
        assert call_details["task_id"] == "T-6"
        assert call_details["action"] == "update"
