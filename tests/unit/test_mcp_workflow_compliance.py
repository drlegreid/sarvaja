"""
Unit tests for workflow_compliance.py MCP tools.

Tests workflow_compliance_check and workflow_compliance_summary.
Covers success path, error handling, and tool registration.
"""

import json
import os
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, field

import pytest


_MOD = "governance.mcp_tools.workflow_compliance"
_SRC = "governance.workflow_compliance"


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
    from governance.mcp_tools.workflow_compliance import register_workflow_compliance_tools

    tools = {}

    class MockMCP:
        def tool(self):
            def decorator(fn):
                tools[fn.__name__] = fn
                return fn
            return decorator

    register_workflow_compliance_tools(MockMCP())
    return tools


@dataclass
class FakeReport:
    overall_status: str = "COMPLIANT"
    checks: list = field(default_factory=list)
    score: float = 0.85

    def to_dict(self):
        return {
            "overall_status": self.overall_status,
            "checks": self.checks,
            "score": self.score,
        }


# ── workflow_compliance_check ─────────────────────────────


class TestWorkflowComplianceCheck:

    def test_registration(self):
        tools = _register_tools()
        assert "workflow_compliance_check" in tools

    @patch(f"{_SRC}.run_compliance_checks")
    def test_success_returns_report(self, mock_run):
        tools = _register_tools()
        report = FakeReport()
        mock_run.return_value = report

        result = json.loads(tools["workflow_compliance_check"]())
        assert result["overall_status"] == "COMPLIANT"
        assert result["score"] == 0.85

    @patch(f"{_SRC}.run_compliance_checks", side_effect=RuntimeError("TypeDB down"))
    def test_exception_returns_error(self, mock_run):
        tools = _register_tools()
        result = json.loads(tools["workflow_compliance_check"]())
        assert "error" in result
        assert "RuntimeError" in result["error"]

    @patch(f"{_SRC}.run_compliance_checks")
    def test_non_compliant_report(self, mock_run):
        tools = _register_tools()
        report = FakeReport(overall_status="NON_COMPLIANT", score=0.3)
        mock_run.return_value = report

        result = json.loads(tools["workflow_compliance_check"]())
        assert result["overall_status"] == "NON_COMPLIANT"
        assert result["score"] == 0.3


# ── workflow_compliance_summary ───────────────────────────


class TestWorkflowComplianceSummary:

    def test_registration(self):
        tools = _register_tools()
        assert "workflow_compliance_summary" in tools

    @patch(f"{_SRC}.format_compliance_for_ui")
    @patch(f"{_SRC}.run_compliance_checks")
    def test_success_returns_summary(self, mock_run, mock_format):
        tools = _register_tools()
        report = FakeReport()
        mock_run.return_value = report
        mock_format.return_value = {
            "status": "COMPLIANT",
            "recommendations": ["Add tests", "Update docs", "Fix lint"],
        }

        result = json.loads(tools["workflow_compliance_summary"]())
        assert result["status"] == "COMPLIANT"
        assert result["recommendation_count"] == 3
        assert len(result["recommendations"]) == 3

    @patch(f"{_SRC}.format_compliance_for_ui")
    @patch(f"{_SRC}.run_compliance_checks")
    def test_truncates_to_3_recommendations(self, mock_run, mock_format):
        tools = _register_tools()
        report = FakeReport()
        mock_run.return_value = report
        mock_format.return_value = {
            "status": "WARNING",
            "recommendations": [f"Rec {i}" for i in range(10)],
        }

        result = json.loads(tools["workflow_compliance_summary"]())
        assert result["recommendation_count"] == 10
        assert len(result["recommendations"]) == 3

    @patch(f"{_SRC}.run_compliance_checks", side_effect=ImportError("No module"))
    def test_import_error_returns_error(self, mock_run):
        tools = _register_tools()
        result = json.loads(tools["workflow_compliance_summary"]())
        assert "error" in result

    @patch(f"{_SRC}.format_compliance_for_ui", side_effect=ValueError("Bad data"))
    @patch(f"{_SRC}.run_compliance_checks")
    def test_format_error_returns_error(self, mock_run, mock_format):
        tools = _register_tools()
        mock_run.return_value = FakeReport()

        result = json.loads(tools["workflow_compliance_summary"]())
        assert "error" in result
        assert "ValueError" in result["error"]
