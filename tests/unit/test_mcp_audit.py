"""
Unit tests for Audit Trail MCP Tools.

Batch 130: Tests for governance/mcp_tools/audit.py
- audit_query: filter by entity_id, entity_type, action_type, correlation_id
- audit_summary: statistics retrieval
- audit_entity_trail: entity-specific trail with timeline summary
- audit_trace: correlation ID tracing with entity grouping
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.audit import register_audit_tools


_MOD = "governance.mcp_tools.audit"


def _json_fmt(data):
    """Simulate format_mcp_result returning JSON."""
    return json.dumps(data, indent=2, default=str)


def _register_tools():
    """Register tools and return them as a dict."""
    mcp = MagicMock()
    tools = {}

    def tool_decorator():
        def wrapper(func):
            tools[func.__name__] = func
            return func
        return wrapper

    mcp.tool = tool_decorator
    register_audit_tools(mcp)
    return tools


# ── audit_query ──────────────────────────────────────────


class TestAuditQuery:

    @patch("governance.stores.query_audit_trail")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_returns_entries(self, mock_fmt, mock_query):
        mock_query.return_value = [
            {"entity_id": "T-1", "action_type": "CREATE", "timestamp": "2026-02-12"}
        ]
        tools = _register_tools()
        result = json.loads(tools["audit_query"](entity_id="T-1"))
        assert result["count"] == 1
        assert result["entries"][0]["entity_id"] == "T-1"

    @patch("governance.stores.query_audit_trail")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_passes_all_filters(self, mock_fmt, mock_query):
        mock_query.return_value = []
        tools = _register_tools()
        tools["audit_query"](
            entity_id="T-1", entity_type="task",
            action_type="UPDATE", correlation_id="CORR-123", limit=5)
        mock_query.assert_called_once_with(
            entity_id="T-1", entity_type="task",
            action_type="UPDATE", correlation_id="CORR-123", limit=5)

    @patch("governance.stores.query_audit_trail", side_effect=Exception("DB error"))
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_handles_exception(self, mock_fmt, mock_query):
        tools = _register_tools()
        result = json.loads(tools["audit_query"]())
        assert "error" in result
        assert "DB error" in result["error"]

    @patch("governance.stores.query_audit_trail", return_value=[])
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_empty_results(self, mock_fmt, mock_query):
        tools = _register_tools()
        result = json.loads(tools["audit_query"]())
        assert result["count"] == 0
        assert result["entries"] == []


# ── audit_summary ────────────────────────────────────────


class TestAuditSummary:

    @patch("governance.stores.get_audit_summary")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_returns_summary(self, mock_fmt, mock_summary):
        mock_summary.return_value = {
            "by_action": {"CREATE": 5, "UPDATE": 3},
            "by_entity": {"task": 6, "session": 2},
            "total": 8,
        }
        tools = _register_tools()
        result = json.loads(tools["audit_summary"]())
        assert result["total"] == 8
        assert result["by_action"]["CREATE"] == 5

    @patch("governance.stores.get_audit_summary", side_effect=Exception("fail"))
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_handles_exception(self, mock_fmt, mock_summary):
        tools = _register_tools()
        result = json.loads(tools["audit_summary"]())
        assert "error" in result


# ── audit_entity_trail ───────────────────────────────────


class TestAuditEntityTrail:

    @patch("governance.stores.query_audit_trail", return_value=[])
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_no_entries(self, mock_fmt, mock_query):
        tools = _register_tools()
        result = json.loads(tools["audit_entity_trail"](entity_id="T-MISSING"))
        assert result["count"] == 0
        assert "No audit entries" in result["message"]

    @patch("governance.stores.query_audit_trail")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_with_entries_and_timeline(self, mock_fmt, mock_query):
        mock_query.return_value = [
            {"action_type": "CREATE", "actor_id": "code-agent", "applied_rules": ["RULE-A"]},
            {"action_type": "UPDATE", "actor_id": "code-agent", "applied_rules": ["RULE-B"]},
            {"action_type": "COMPLETE", "actor_id": "test-agent", "applied_rules": None},
        ]
        tools = _register_tools()
        result = json.loads(tools["audit_entity_trail"](entity_id="T-1"))
        assert result["count"] == 3
        assert result["timeline_summary"]["actions"] == ["CREATE", "UPDATE", "COMPLETE"]
        assert set(result["timeline_summary"]["actors"]) == {"code-agent", "test-agent"}
        assert set(result["timeline_summary"]["rules_applied"]) == {"RULE-A", "RULE-B"}

    @patch("governance.stores.query_audit_trail")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_calls_with_limit_100(self, mock_fmt, mock_query):
        mock_query.return_value = []
        tools = _register_tools()
        tools["audit_entity_trail"](entity_id="T-1")
        mock_query.assert_called_once_with(entity_id="T-1", limit=100)

    @patch("governance.stores.query_audit_trail", side_effect=Exception("fail"))
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_handles_exception(self, mock_fmt, mock_query):
        tools = _register_tools()
        result = json.loads(tools["audit_entity_trail"](entity_id="T-1"))
        assert "error" in result


# ── audit_trace ──────────────────────────────────────────


class TestAuditTrace:

    @patch("governance.stores.query_audit_trail", return_value=[])
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_no_entries(self, mock_fmt, mock_query):
        tools = _register_tools()
        result = json.loads(tools["audit_trace"](correlation_id="CORR-MISSING"))
        assert result["count"] == 0
        assert "No operations found" in result["message"]

    @patch("governance.stores.query_audit_trail")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_groups_by_entity(self, mock_fmt, mock_query):
        mock_query.return_value = [
            {"entity_id": "T-1", "action_type": "CREATE"},
            {"entity_id": "T-1", "action_type": "UPDATE"},
            {"entity_id": "S-1", "action_type": "CREATE"},
        ]
        tools = _register_tools()
        result = json.loads(tools["audit_trace"](correlation_id="CORR-123"))
        assert result["count"] == 3
        assert result["affected_entities"]["T-1"] == ["CREATE", "UPDATE"]
        assert result["affected_entities"]["S-1"] == ["CREATE"]

    @patch("governance.stores.query_audit_trail")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_missing_entity_id_defaults_to_unknown(self, mock_fmt, mock_query):
        mock_query.return_value = [
            {"action_type": "LOG"},  # No entity_id
        ]
        tools = _register_tools()
        result = json.loads(tools["audit_trace"](correlation_id="CORR-123"))
        assert "unknown" in result["affected_entities"]

    @patch("governance.stores.query_audit_trail", side_effect=Exception("fail"))
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_handles_exception(self, mock_fmt, mock_query):
        tools = _register_tools()
        result = json.loads(tools["audit_trace"](correlation_id="CORR-123"))
        assert "error" in result
