"""
Unit tests for Rule Quality MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/evidence/quality.py module.
Tests: register_quality_tools (governance_analyze_rules,
       governance_rule_impact, governance_find_issues).
"""

import pytest
from unittest.mock import patch, MagicMock


class _CaptureMCP:
    """Captures tools registered via @mcp.tool()."""

    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


class TestRegisterQualityTools:
    """Tests for register_quality_tools()."""

    def test_registers_three_tools(self):
        from governance.mcp_tools.evidence.quality import register_quality_tools
        mcp = _CaptureMCP()
        register_quality_tools(mcp)
        assert len(mcp.tools) == 3

    def test_tool_names(self):
        from governance.mcp_tools.evidence.quality import register_quality_tools
        mcp = _CaptureMCP()
        register_quality_tools(mcp)
        assert "governance_analyze_rules" in mcp.tools
        assert "governance_rule_impact" in mcp.tools
        assert "governance_find_issues" in mcp.tools


class TestAnalyzeRulesUnavailable:
    """Tests for governance_analyze_rules when quality module not available."""

    @patch("governance.mcp_tools.evidence.quality.RULE_QUALITY_AVAILABLE", False)
    def test_returns_error_when_unavailable(self):
        from governance.mcp_tools.evidence.quality import register_quality_tools
        mcp = _CaptureMCP()
        register_quality_tools(mcp)
        result = mcp.tools["governance_analyze_rules"]()
        assert "error" in result or "not available" in result


class TestRuleImpactUnavailable:
    """Tests for governance_rule_impact when quality module not available."""

    @patch("governance.mcp_tools.evidence.quality.RULE_QUALITY_AVAILABLE", False)
    def test_returns_error_when_unavailable(self):
        from governance.mcp_tools.evidence.quality import register_quality_tools
        mcp = _CaptureMCP()
        register_quality_tools(mcp)
        result = mcp.tools["governance_rule_impact"]("RULE-001")
        assert "error" in result or "not available" in result


class TestFindIssuesUnavailable:
    """Tests for governance_find_issues when quality module not available."""

    @patch("governance.mcp_tools.evidence.quality.RULE_QUALITY_AVAILABLE", False)
    def test_returns_error_when_unavailable(self):
        from governance.mcp_tools.evidence.quality import register_quality_tools
        mcp = _CaptureMCP()
        register_quality_tools(mcp)
        result = mcp.tools["governance_find_issues"]()
        assert "error" in result or "not available" in result

    @patch("governance.mcp_tools.evidence.quality.RULE_QUALITY_AVAILABLE", False)
    def test_accepts_issue_type_param(self):
        from governance.mcp_tools.evidence.quality import register_quality_tools
        mcp = _CaptureMCP()
        register_quality_tools(mcp)
        result = mcp.tools["governance_find_issues"](issue_type="orphaned")
        assert "error" in result or "not available" in result


class TestAnalyzeRulesAvailable:
    """Tests for governance_analyze_rules when quality module IS available."""

    @patch("governance.mcp_tools.evidence.quality.RULE_QUALITY_AVAILABLE", True)
    @patch("governance.mcp_tools.evidence.quality.analyze_rule_quality")
    def test_delegates_to_analyzer(self, mock_analyze):
        mock_analyze.return_value = '{"issues": []}'
        from governance.mcp_tools.evidence.quality import register_quality_tools
        mcp = _CaptureMCP()
        register_quality_tools(mcp)
        result = mcp.tools["governance_analyze_rules"]()
        mock_analyze.assert_called_once()
        assert result == '{"issues": []}'

    @patch("governance.mcp_tools.evidence.quality.RULE_QUALITY_AVAILABLE", True)
    @patch("governance.mcp_tools.evidence.quality.get_rule_impact")
    def test_rule_impact_delegates(self, mock_impact):
        mock_impact.return_value = '{"impact": "low"}'
        from governance.mcp_tools.evidence.quality import register_quality_tools
        mcp = _CaptureMCP()
        register_quality_tools(mcp)
        result = mcp.tools["governance_rule_impact"]("RULE-001")
        mock_impact.assert_called_once_with("RULE-001")

    @patch("governance.mcp_tools.evidence.quality.RULE_QUALITY_AVAILABLE", True)
    @patch("governance.mcp_tools.evidence.quality.find_rule_issues")
    def test_find_issues_delegates(self, mock_find):
        mock_find.return_value = '[]'
        from governance.mcp_tools.evidence.quality import register_quality_tools
        mcp = _CaptureMCP()
        register_quality_tools(mcp)
        result = mcp.tools["governance_find_issues"](issue_type="orphaned")
        mock_find.assert_called_once_with("orphaned")
