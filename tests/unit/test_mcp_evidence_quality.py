"""
Unit tests for Rule Quality MCP Tools.

Batch 147: Tests for governance/mcp_tools/evidence/quality.py
- governance_analyze_rules: quality analysis delegation
- governance_rule_impact: rule impact analysis delegation
- governance_find_issues: issue finding delegation
"""

import json
import os
from unittest.mock import patch, MagicMock

import pytest

_MOD = "governance.mcp_tools.evidence.quality"


@pytest.fixture(autouse=True)
def force_json_output():
    """Force JSON output format for predictable test results."""
    old = os.environ.get("MCP_OUTPUT_FORMAT")
    os.environ["MCP_OUTPUT_FORMAT"] = "json"
    yield
    if old is None:
        os.environ.pop("MCP_OUTPUT_FORMAT", None)
    else:
        os.environ["MCP_OUTPUT_FORMAT"] = old


def _register_tools():
    """Register and return tools by name."""
    from governance.mcp_tools.evidence.quality import register_quality_tools

    tools = {}

    class MockMCP:
        def tool(self):
            def decorator(fn):
                tools[fn.__name__] = fn
                return fn
            return decorator

    register_quality_tools(MockMCP())
    return tools


class TestRegistration:
    def test_registers_all_tools(self):
        tools = _register_tools()
        assert "governance_analyze_rules" in tools
        assert "governance_rule_impact" in tools
        assert "governance_find_issues" in tools


# ── governance_analyze_rules ─────────────────────────────


class TestGovernanceAnalyzeRules:

    @patch(f"{_MOD}.RULE_QUALITY_AVAILABLE", False)
    def test_unavailable_returns_error(self):
        tools = _register_tools()
        result = json.loads(tools["governance_analyze_rules"]())
        assert "error" in result
        assert "not available" in result["error"]

    @patch(f"{_MOD}.analyze_rule_quality")
    @patch(f"{_MOD}.RULE_QUALITY_AVAILABLE", True)
    def test_delegates_to_analyzer(self, mock_analyze):
        tools = _register_tools()
        mock_analyze.return_value = json.dumps({"issues": [], "score": 95})

        result = tools["governance_analyze_rules"]()
        mock_analyze.assert_called_once()
        # Result is what the analyzer returns (not wrapped by format_mcp_result)
        parsed = json.loads(result)
        assert parsed["score"] == 95


# ── governance_rule_impact ───────────────────────────────


class TestGovernanceRuleImpact:

    @patch(f"{_MOD}.RULE_QUALITY_AVAILABLE", False)
    def test_unavailable_returns_error(self):
        tools = _register_tools()
        result = json.loads(tools["governance_rule_impact"]("R-1"))
        assert "error" in result

    @patch(f"{_MOD}.get_rule_impact")
    @patch(f"{_MOD}.RULE_QUALITY_AVAILABLE", True)
    def test_delegates_with_rule_id(self, mock_impact):
        tools = _register_tools()
        mock_impact.return_value = json.dumps({"impact_score": 0.7})

        tools["governance_rule_impact"]("RULE-001")
        mock_impact.assert_called_once_with("RULE-001")

    @patch(f"{_MOD}.get_rule_impact")
    @patch(f"{_MOD}.RULE_QUALITY_AVAILABLE", True)
    def test_returns_impact_data(self, mock_impact):
        tools = _register_tools()
        mock_impact.return_value = json.dumps({
            "rule_id": "R-1", "impact_score": 0.7, "affected": 3
        })

        result = json.loads(tools["governance_rule_impact"]("R-1"))
        assert result["impact_score"] == 0.7


# ── governance_find_issues ───────────────────────────────


class TestGovernanceFindIssues:

    @patch(f"{_MOD}.RULE_QUALITY_AVAILABLE", False)
    def test_unavailable_returns_error(self):
        tools = _register_tools()
        result = json.loads(tools["governance_find_issues"]())
        assert "error" in result

    @patch(f"{_MOD}.find_rule_issues")
    @patch(f"{_MOD}.RULE_QUALITY_AVAILABLE", True)
    def test_delegates_with_type(self, mock_issues):
        tools = _register_tools()
        mock_issues.return_value = json.dumps({"issues": ["orphaned"]})

        tools["governance_find_issues"](issue_type="orphaned")
        mock_issues.assert_called_once_with("orphaned")

    @patch(f"{_MOD}.find_rule_issues")
    @patch(f"{_MOD}.RULE_QUALITY_AVAILABLE", True)
    def test_delegates_with_none_default(self, mock_issues):
        tools = _register_tools()
        mock_issues.return_value = json.dumps({"issues": []})

        tools["governance_find_issues"]()
        mock_issues.assert_called_once_with(None)

    @patch(f"{_MOD}.find_rule_issues")
    @patch(f"{_MOD}.RULE_QUALITY_AVAILABLE", True)
    def test_returns_issues_data(self, mock_issues):
        tools = _register_tools()
        mock_issues.return_value = json.dumps({
            "issues": [{"type": "orphaned", "rule_id": "R-1"}]
        })

        result = json.loads(tools["governance_find_issues"](issue_type="orphaned"))
        assert len(result["issues"]) == 1
