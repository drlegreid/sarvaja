"""
Unit tests for Executive Reports State.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/state/executive.py.
Tests: with_executive_report, with_executive_loading, with_executive_period,
       get_executive_status_color, get_section_status_color, _get_section_icon,
       format_executive_section, format_executive_report.
"""

from agent.governance_ui.state.executive import (
    with_executive_report, with_executive_loading, with_executive_period,
    get_executive_status_color, get_section_status_color, _get_section_icon,
    format_executive_section, format_executive_report,
)


# ── State Transforms ─────────────────────────────────────


class TestWithExecutiveReport:
    def test_sets_report(self):
        report = {"report_id": "RPT-1"}
        assert with_executive_report({}, report)["executive_report"] == report

    def test_sets_none(self):
        assert with_executive_report({}, None)["executive_report"] is None


class TestWithExecutiveLoading:
    def test_default_true(self):
        assert with_executive_loading({})["executive_loading"] is True

    def test_false(self):
        assert with_executive_loading({}, False)["executive_loading"] is False


class TestWithExecutivePeriod:
    def test_sets_period(self):
        assert with_executive_period({}, "quarter")["executive_period"] == "quarter"


# ── UI Helpers ────────────────────────────────────────────


class TestGetExecutiveStatusColor:
    def test_known_statuses(self):
        assert get_executive_status_color("healthy") == "success"
        assert get_executive_status_color("warning") == "warning"
        assert get_executive_status_color("critical") == "error"

    def test_case_insensitive(self):
        assert get_executive_status_color("HEALTHY") == "success"

    def test_unknown(self):
        assert get_executive_status_color("xyz") == "grey"


class TestGetSectionStatusColor:
    def test_known(self):
        assert get_section_status_color("success") == "success"
        assert get_section_status_color("warning") == "warning"
        assert get_section_status_color("error") == "error"

    def test_unknown(self):
        assert get_section_status_color("xyz") == "grey"


class TestGetSectionIcon:
    def test_summary(self):
        assert _get_section_icon("Executive Summary") == "mdi-clipboard-text"

    def test_compliance(self):
        assert _get_section_icon("Compliance Status") == "mdi-check-decagram"

    def test_risk(self):
        assert _get_section_icon("Risk Assessment") == "mdi-alert-circle"

    def test_alignment(self):
        assert _get_section_icon("Strategic Alignment") == "mdi-compass"

    def test_resource(self):
        assert _get_section_icon("Resource Allocation") == "mdi-account-group"

    def test_recommendation(self):
        assert _get_section_icon("Recommendations") == "mdi-lightbulb"

    def test_objective(self):
        assert _get_section_icon("Key Objectives") == "mdi-target"

    def test_default(self):
        assert _get_section_icon("Something Else") == "mdi-file-document"


# ── Format Functions ──────────────────────────────────────


class TestFormatExecutiveSection:
    def test_full_section(self):
        section = {"title": "Risk Assessment", "content": "All good",
                   "status": "warning", "metrics": {"score": 85}}
        result = format_executive_section(section)
        assert result["title"] == "Risk Assessment"
        assert result["status_color"] == "warning"
        assert result["icon"] == "mdi-alert-circle"
        assert result["metrics"] == {"score": 85}

    def test_defaults(self):
        result = format_executive_section({})
        assert result["title"] == "Section"
        assert result["status"] == "success"
        assert result["status_color"] == "success"


class TestFormatExecutiveReport:
    def test_full_report(self):
        report = {
            "report_id": "RPT-001",
            "generated_at": "2026-01-01T10:00:00",
            "period": "Q1 2026",
            "overall_status": "healthy",
            "sections": [
                {"title": "Summary", "status": "success", "content": "OK"},
            ],
            "metrics_summary": {"total_rules": 50},
        }
        result = format_executive_report(report)
        assert result["report_id"] == "RPT-001"
        assert result["status_color"] == "success"
        assert len(result["sections"]) == 1
        assert result["sections"][0]["icon"] == "mdi-clipboard-text"

    def test_defaults(self):
        result = format_executive_report({})
        assert result["report_id"] == "Unknown"
        assert result["overall_status"] == "healthy"
        assert result["sections"] == []
