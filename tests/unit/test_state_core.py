"""
Unit tests for Core State Transforms and Helpers.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/state/core.py.
Tests: with_loading, with_error, clear_error, with_status, with_active_view,
       with_selected_rule, with_rule_form, with_filters, with_sort,
       with_impact_analysis, with_graph_view, get_status_color, get_priority_color,
       get_category_icon, get_risk_color, format_rule_card, format_impact_summary.
"""

from agent.governance_ui.state.core import (
    with_loading, with_error, clear_error, with_status,
    with_active_view, with_selected_rule, with_rule_form,
    with_filters, with_sort, with_impact_analysis, with_graph_view,
    get_status_color, get_priority_color, get_category_icon,
    get_risk_color, format_rule_card, format_impact_summary,
)


# ── State Transforms ─────────────────────────────────────


class TestWithLoading:
    def test_sets_loading_true(self):
        result = with_loading({}, True)
        assert result["is_loading"] is True

    def test_sets_loading_false(self):
        result = with_loading({"is_loading": True}, False)
        assert result["is_loading"] is False

    def test_preserves_other_keys(self):
        result = with_loading({"foo": "bar"}, True)
        assert result["foo"] == "bar"

    def test_default_is_true(self):
        result = with_loading({})
        assert result["is_loading"] is True


class TestWithError:
    def test_sets_error(self):
        result = with_error({}, "something broke")
        assert result["has_error"] is True
        assert result["error_message"] == "something broke"

    def test_preserves_other_keys(self):
        result = with_error({"x": 1}, "err")
        assert result["x"] == 1


class TestClearError:
    def test_clears_error(self):
        result = clear_error({"has_error": True, "error_message": "old"})
        assert result["has_error"] is False
        assert result["error_message"] == ""


class TestWithStatus:
    def test_sets_status(self):
        result = with_status({}, "All good")
        assert result["status_message"] == "All good"


class TestWithActiveView:
    def test_sets_view(self):
        result = with_active_view({}, "rules")
        assert result["active_view"] == "rules"


class TestWithSelectedRule:
    def test_selects_rule(self):
        rule = {"rule_id": "R-1"}
        result = with_selected_rule({}, rule)
        assert result["selected_rule"] == rule
        assert result["show_rule_detail"] is True

    def test_deselects_rule(self):
        result = with_selected_rule({}, None)
        assert result["selected_rule"] is None
        assert result["show_rule_detail"] is False


class TestWithRuleForm:
    def test_create_mode(self):
        result = with_rule_form({})
        assert result["show_rule_form"] is True
        assert result["rule_form_mode"] == "create"

    def test_edit_mode(self):
        result = with_rule_form({}, mode="edit")
        assert result["rule_form_mode"] == "edit"

    def test_hide_form(self):
        result = with_rule_form({}, show=False)
        assert result["show_rule_form"] is False


class TestWithFilters:
    def test_sets_all_filters(self):
        result = with_filters({}, status="ACTIVE", category="governance", search="test")
        assert result["rules_status_filter"] == "ACTIVE"
        assert result["rules_category_filter"] == "governance"
        assert result["rules_search_query"] == "test"

    def test_defaults_none(self):
        result = with_filters({})
        assert result["rules_status_filter"] is None
        assert result["rules_category_filter"] is None
        assert result["rules_search_query"] == ""


class TestWithSort:
    def test_sets_sort(self):
        result = with_sort({}, "name")
        assert result["rules_sort_column"] == "name"
        assert result["rules_sort_asc"] is True

    def test_descending(self):
        result = with_sort({}, "priority", ascending=False)
        assert result["rules_sort_asc"] is False


class TestWithImpactAnalysis:
    def test_sets_all_fields(self):
        result = with_impact_analysis({}, rule_id="R-1", analysis={"x": 1},
                                       graph={"nodes": []}, mermaid="graph LR")
        assert result["impact_selected_rule"] == "R-1"
        assert result["impact_analysis"] == {"x": 1}
        assert result["dependency_graph"] == {"nodes": []}
        assert result["mermaid_diagram"] == "graph LR"

    def test_defaults_none(self):
        result = with_impact_analysis({})
        assert result["impact_selected_rule"] is None
        assert result["mermaid_diagram"] == ""


class TestWithGraphView:
    def test_show(self):
        assert with_graph_view({})["show_graph_view"] is True

    def test_hide(self):
        assert with_graph_view({}, False)["show_graph_view"] is False


# ── UI Helpers ────────────────────────────────────────────


class TestGetStatusColor:
    def test_known_status(self):
        assert get_status_color("ACTIVE") == "success"
        assert get_status_color("DEPRECATED") == "warning"

    def test_unknown_fallback(self):
        assert get_status_color("NONEXISTENT") == "grey"


class TestGetPriorityColor:
    def test_known_priority(self):
        assert get_priority_color("CRITICAL") == "error"
        assert get_priority_color("HIGH") == "warning"

    def test_unknown_fallback(self):
        assert get_priority_color("NONE") == "grey"


class TestGetCategoryIcon:
    def test_known_category(self):
        assert get_category_icon("governance") == "mdi-gavel"

    def test_unknown_fallback(self):
        assert get_category_icon("random") == "mdi-file"


class TestGetRiskColor:
    def test_known_risk(self):
        assert get_risk_color("CRITICAL") == "error"
        assert get_risk_color("LOW") == "success"

    def test_unknown_fallback(self):
        assert get_risk_color("UNKNOWN") == "grey"


# ── Format Functions ──────────────────────────────────────


class TestFormatRuleCard:
    def test_full_rule(self):
        rule = {"rule_id": "R-1", "title": "Test Rule", "status": "ACTIVE", "category": "governance"}
        result = format_rule_card(rule)
        assert result["title"] == "R-1"
        assert result["subtitle"] == "Test Rule"
        assert result["color"] == "success"
        assert result["icon"] == "mdi-gavel"

    def test_uses_id_fallback(self):
        rule = {"id": "R-2", "name": "Fallback"}
        result = format_rule_card(rule)
        assert result["title"] == "R-2"
        assert result["subtitle"] == "Fallback"

    def test_missing_fields(self):
        result = format_rule_card({})
        assert result["title"] == "Unknown"
        assert result["subtitle"] == ""
        assert result["color"] == "grey"  # unknown status


class TestFormatImpactSummary:
    def test_full_impact(self):
        impact = {
            "rule_id": "R-1", "risk_level": "HIGH",
            "total_affected": 5,
            "direct_dependents": ["R-2", "R-3"],
            "dependencies": ["R-0"],
            "recommendation": "Review before change",
            "critical_rules_affected": ["R-2"],
        }
        result = format_impact_summary(impact)
        assert result["rule_id"] == "R-1"
        assert result["risk_level"] == "HIGH"
        assert result["risk_color"] == "warning"
        assert result["total_affected"] == 5
        assert result["direct_dependents"] == 2
        assert result["dependencies"] == 1
        assert result["recommendation"] == "Review before change"
        assert result["critical_affected"] == ["R-2"]

    def test_defaults(self):
        result = format_impact_summary({})
        assert result["rule_id"] == "Unknown"
        assert result["risk_level"] == "LOW"
        assert result["risk_color"] == "success"
        assert result["total_affected"] == 0
        assert result["direct_dependents"] == 0
        assert result["dependencies"] == 0
