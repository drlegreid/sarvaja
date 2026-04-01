"""
Unit tests for MCP task linking structured error responses.

Per SRVJ-BUG-ERROR-OBS-01 / EPIC-TASK-WORKFLOW-HEAL-01 P3:
MCP errors must include entity context (task_id, target entity)
and structured reason — not just "task_link_session failed: KeyError".

Per SRVJ-BUG-LINK-IDEM-01: Write handlers route through service layer;
tests mock service functions, not TypeDB client.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from governance.services.link_result import LinkResult

_MCP_MOD = "governance.mcp_tools.tasks_linking"
_SVC_MOD = "governance.services.tasks_mutations_linking"


def _json_fmt(data):
    """Force JSON output for test parsing (matches existing test pattern)."""
    return json.dumps(data, indent=2, default=str)


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_mcp():
    """Create a mock MCP server that captures tool registrations."""
    tools = {}

    class MockMCP:
        def tool(self):
            def decorator(fn):
                tools[fn.__name__] = fn
                return fn
            return decorator

    return MockMCP(), tools


def _register_linking_tools():
    """Register linking tools and return the captured tool dict."""
    mcp, tools = _make_mcp()
    from governance.mcp_tools.tasks_linking import register_task_linking_tools
    register_task_linking_tools(mcp)
    return tools


def _parse_result(result_str: str) -> dict:
    """Parse MCP JSON result string."""
    return json.loads(result_str)


# ── 1. task_link_session structured errors ───────────────────────────────


class TestMcpTaskLinkSessionStructured:
    """MCP task_link_session must return structured errors with context."""

    @patch(f"{_MCP_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_SVC_MOD}.link_task_to_session")
    def test_success_includes_already_existed(self, mock_svc, _fmt):
        """Successful link response includes already_existed flag."""
        tools = _register_linking_tools()
        mock_svc.return_value = LinkResult(success=True, already_existed=False, reason="linked")
        result = _parse_result(tools["task_link_session"]("T-001", "SESSION-1"))
        assert "already_existed" in result
        assert result["success"] is True
        mock_svc.assert_called_once_with("T-001", "SESSION-1", source="mcp")

    @patch(f"{_MCP_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_SVC_MOD}.link_task_to_session")
    def test_idempotent_returns_already_existed_true(self, mock_svc, _fmt):
        """Duplicate link returns already_existed=True."""
        tools = _register_linking_tools()
        mock_svc.return_value = LinkResult(success=True, already_existed=True, reason="linked")
        result = _parse_result(tools["task_link_session"]("T-001", "SESSION-1"))
        assert result["already_existed"] is True

    @patch(f"{_MCP_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_SVC_MOD}.link_task_to_session")
    def test_not_found_includes_entity_context(self, mock_svc, _fmt):
        """Not-found error includes task_id for debugging."""
        tools = _register_linking_tools()
        mock_svc.return_value = LinkResult(
            success=False, already_existed=False,
            reason="task T-MISSING not found", error_code="ENTITY_NOT_FOUND")
        result = _parse_result(tools["task_link_session"]("T-MISSING", "SESSION-1"))
        assert "error" in result
        assert "T-MISSING" in result.get("error", "")
        assert result.get("error_code") == "ENTITY_NOT_FOUND"

    @patch(f"{_MCP_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_exception_includes_reason(self, _fmt):
        """Exception response includes reason with exception context."""
        tools = _register_linking_tools()
        with patch(f"{_SVC_MOD}.link_task_to_session", side_effect=KeyError("missing")):
            result = _parse_result(tools["task_link_session"]("T-001", "SESSION-1"))
            assert "error" in result
            assert "task_id" in result or "T-001" in result.get("error", "")


# ── 2. task_link_rule structured errors ──────────────────────────────────


class TestMcpTaskLinkRuleStructured:
    """MCP task_link_rule must return structured errors with context."""

    @patch(f"{_MCP_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_SVC_MOD}.link_task_to_rule")
    def test_success_includes_already_existed(self, mock_svc, _fmt):
        tools = _register_linking_tools()
        mock_svc.return_value = LinkResult(success=True, already_existed=False, reason="linked")
        result = _parse_result(tools["task_link_rule"]("T-001", "RULE-001"))
        assert "already_existed" in result
        mock_svc.assert_called_once_with("T-001", "RULE-001", source="mcp")

    @patch(f"{_MCP_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_SVC_MOD}.link_task_to_rule")
    def test_not_found_includes_entity_ids(self, mock_svc, _fmt):
        tools = _register_linking_tools()
        mock_svc.return_value = LinkResult(
            success=False, already_existed=False,
            reason="task T-BAD not found", error_code="ENTITY_NOT_FOUND")
        result = _parse_result(tools["task_link_rule"]("T-BAD", "RULE-001"))
        error = result.get("error", "")
        assert "T-BAD" in error or result.get("task_id") == "T-BAD"
        assert "error_code" in result


# ── 3. task_link_evidence structured errors ──────────────────────────────


class TestMcpTaskLinkEvidenceStructured:
    """MCP task_link_evidence must return structured errors with context."""

    @patch(f"{_MCP_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_SVC_MOD}.link_task_to_evidence")
    def test_success_includes_already_existed(self, mock_svc, _fmt):
        tools = _register_linking_tools()
        mock_svc.return_value = LinkResult(success=True, already_existed=False, reason="linked")
        result = _parse_result(tools["task_link_evidence"]("T-001", "evidence/test.json"))
        assert "already_existed" in result
        mock_svc.assert_called_once_with("T-001", "evidence/test.json", source="mcp")

    @patch(f"{_MCP_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_SVC_MOD}.link_task_to_evidence")
    def test_not_found_structured(self, mock_svc, _fmt):
        tools = _register_linking_tools()
        mock_svc.return_value = LinkResult(
            success=False, already_existed=False,
            reason="task T-001 not found", error_code="ENTITY_NOT_FOUND")
        result = _parse_result(tools["task_link_evidence"]("T-001", "evidence/test.json"))
        assert "error" in result
        assert "error_code" in result


# ── 4. task_link_commit structured errors ────────────────────────────────


class TestMcpTaskLinkCommitStructured:
    """MCP task_link_commit must return structured errors with context."""

    @patch(f"{_MCP_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_SVC_MOD}.link_task_to_commit")
    def test_success_includes_already_existed(self, mock_svc, _fmt):
        tools = _register_linking_tools()
        mock_svc.return_value = LinkResult(success=True, already_existed=False, reason="linked")
        result = _parse_result(tools["task_link_commit"]("T-001", "abc1234"))
        assert "already_existed" in result
        mock_svc.assert_called_once_with("T-001", "abc1234", None, source="mcp")

    @patch(f"{_MCP_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_SVC_MOD}.link_task_to_commit")
    def test_not_found_includes_entity_ids(self, mock_svc, _fmt):
        tools = _register_linking_tools()
        mock_svc.return_value = LinkResult(
            success=False, already_existed=False,
            reason="task T-FAIL not found", error_code="ENTITY_NOT_FOUND")
        result = _parse_result(tools["task_link_commit"]("T-FAIL", "abc1234"))
        error = result.get("error", "")
        assert "T-FAIL" in error or result.get("task_id") == "T-FAIL"

    @patch(f"{_MCP_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_invalid_sha_validation(self, _fmt):
        """Invalid commit_sha rejected at MCP boundary."""
        tools = _register_linking_tools()
        result = _parse_result(tools["task_link_commit"]("T-001", "not-a-hex"))
        assert "error" in result
        assert result.get("error_code") == "VALIDATION"


# ── 5. task_link_document structured errors ──────────────────────────────


class TestMcpTaskLinkDocumentStructured:
    """MCP task_link_document must return structured errors with context."""

    @patch(f"{_MCP_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_SVC_MOD}.link_task_to_document")
    def test_success_includes_already_existed(self, mock_svc, _fmt):
        tools = _register_linking_tools()
        mock_svc.return_value = LinkResult(success=True, already_existed=False, reason="linked")
        result = _parse_result(tools["task_link_document"]("T-001", "docs/README.md"))
        assert "already_existed" in result
        mock_svc.assert_called_once_with("T-001", "docs/README.md", source="mcp")

    @patch(f"{_MCP_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_exception_includes_context(self, _fmt):
        tools = _register_linking_tools()
        with patch(f"{_SVC_MOD}.link_task_to_document",
                   side_effect=TypeError("unexpected None")):
            result = _parse_result(tools["task_link_document"]("T-001", "docs/README.md"))
            assert "error" in result
            assert "task_id" in result or "T-001" in result.get("error", "")
