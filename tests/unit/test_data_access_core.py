"""
Unit tests for Core Data Access Functions.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/data_access/core.py.
Tests: call_mcp_tool, get_rules, get_rules_by_category, get_decisions,
       get_sessions, get_tasks, search_evidence.
"""

import json
from unittest.mock import patch, MagicMock

from agent.governance_ui.data_access.core import (
    call_mcp_tool, get_rules, get_rules_by_category,
    get_decisions, get_sessions, get_tasks, search_evidence,
    MCP_TOOLS,
)


# ── call_mcp_tool ────────────────────────────────────────


class TestCallMcpTool:
    def test_unknown_tool(self):
        result = call_mcp_tool("nonexistent_tool")
        assert "error" in result
        assert "Unknown tool" in result["error"]

    def test_success(self):
        with patch.dict(MCP_TOOLS, {"test_tool": MagicMock(return_value='{"ok": true}')}):
            result = call_mcp_tool("test_tool", x=1)
        assert result == {"ok": True}

    def test_json_parse_error(self):
        with patch.dict(MCP_TOOLS, {"bad": MagicMock(return_value="not json")}):
            result = call_mcp_tool("bad")
        assert "error" in result

    def test_exception(self):
        with patch.dict(MCP_TOOLS, {"err": MagicMock(side_effect=Exception("boom"))}):
            result = call_mcp_tool("err")
        assert "boom" in result["error"]


# ── get_rules ────────────────────────────────────────────


class TestGetRules:
    def test_returns_list_directly(self):
        rules = [{"rule_id": "R-1"}]
        with patch("agent.governance_ui.data_access.core.call_mcp_tool", return_value=rules):
            result = get_rules()
        assert result == rules

    def test_returns_from_dict_with_rules_key(self):
        with patch("agent.governance_ui.data_access.core.call_mcp_tool",
                    return_value={"rules": [{"rule_id": "R-1"}]}):
            result = get_rules()
        assert result == [{"rule_id": "R-1"}]

    def test_error_returns_empty(self):
        with patch("agent.governance_ui.data_access.core.call_mcp_tool",
                    return_value={"error": "failed"}):
            result = get_rules()
        assert result == []


# ── get_rules_by_category ────────────────────────────────


class TestGetRulesByCategory:
    def test_groups_rules(self):
        rules = [
            {"rule_id": "R-1", "category": "governance"},
            {"rule_id": "R-2", "category": "technical"},
            {"rule_id": "R-3", "category": "governance"},
        ]
        with patch("agent.governance_ui.data_access.core.get_rules", return_value=rules):
            result = get_rules_by_category()
        assert len(result["governance"]) == 2
        assert len(result["technical"]) == 1

    def test_unknown_category(self):
        with patch("agent.governance_ui.data_access.core.get_rules",
                    return_value=[{"rule_id": "R-1"}]):
            result = get_rules_by_category()
        assert "unknown" in result


# ── get_decisions ────────────────────────────────────────


class TestGetDecisions:
    def test_returns_list(self):
        decisions = [{"decision_id": "D-1"}]
        with patch("agent.governance_ui.data_access.core.call_mcp_tool", return_value=decisions):
            result = get_decisions()
        assert result == decisions

    def test_from_dict(self):
        with patch("agent.governance_ui.data_access.core.call_mcp_tool",
                    return_value={"decisions": [{"id": "D-1"}]}):
            result = get_decisions()
        assert len(result) == 1

    def test_error(self):
        with patch("agent.governance_ui.data_access.core.call_mcp_tool",
                    return_value={"error": "fail"}):
            assert get_decisions() == []


# ── get_sessions ─────────────────────────────────────────


class TestGetSessions:
    def test_returns_list(self):
        sessions = [{"session_id": "S-1"}]
        with patch("agent.governance_ui.data_access.core.call_mcp_tool", return_value=sessions):
            result = get_sessions()
        assert result == sessions

    def test_from_dict(self):
        with patch("agent.governance_ui.data_access.core.call_mcp_tool",
                    return_value={"sessions": [{"id": "S-1"}]}):
            result = get_sessions(limit=50)
        assert len(result) == 1

    def test_error(self):
        with patch("agent.governance_ui.data_access.core.call_mcp_tool",
                    return_value={"error": "fail"}):
            assert get_sessions() == []


# ── get_tasks ────────────────────────────────────────────


class TestGetTasks:
    def test_returns_list(self):
        tasks = [{"task_id": "T-1"}]
        with patch("agent.governance_ui.data_access.core.call_mcp_tool", return_value=tasks):
            assert get_tasks() == tasks

    def test_from_dict(self):
        with patch("agent.governance_ui.data_access.core.call_mcp_tool",
                    return_value={"tasks": [{"id": "T-1"}]}):
            assert len(get_tasks()) == 1

    def test_error(self):
        with patch("agent.governance_ui.data_access.core.call_mcp_tool",
                    return_value={"error": "fail"}):
            assert get_tasks() == []


# ── search_evidence ──────────────────────────────────────


class TestSearchEvidence:
    def test_returns_list(self):
        results = [{"file": "evidence/S-1.md"}]
        with patch("agent.governance_ui.data_access.core.call_mcp_tool", return_value=results):
            assert search_evidence("test") == results

    def test_from_dict(self):
        with patch("agent.governance_ui.data_access.core.call_mcp_tool",
                    return_value={"results": [{"file": "e.md"}]}):
            assert len(search_evidence("q")) == 1

    def test_error(self):
        with patch("agent.governance_ui.data_access.core.call_mcp_tool",
                    return_value={"error": "fail"}):
            assert search_evidence("q") == []
