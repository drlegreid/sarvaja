"""
Unit tests for Data Access Filter Functions.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/data_access/filters.py.
Tests: filter_rules_by_status, filter_rules_by_category,
       filter_rules_by_search, sort_rules.
"""

from agent.governance_ui.data_access.filters import (
    filter_rules_by_status,
    filter_rules_by_category,
    filter_rules_by_search,
    sort_rules,
)

_RULES = [
    {"rule_id": "R-1", "title": "First Rule", "status": "active",
     "category": "security", "directive": "Do X"},
    {"rule_id": "R-2", "title": "Second Rule", "status": "deprecated",
     "category": "ops", "directive": "Do Y"},
    {"rule_id": "R-3", "title": "Third Rule", "status": "active",
     "category": "security", "directive": "Do Z"},
]


# ── filter_rules_by_status ────────────────────────────


class TestFilterByStatus:
    def test_filters_active(self):
        result = filter_rules_by_status(_RULES, "active")
        assert len(result) == 2
        assert all(r["status"] == "active" for r in result)

    def test_filters_deprecated(self):
        result = filter_rules_by_status(_RULES, "deprecated")
        assert len(result) == 1
        assert result[0]["rule_id"] == "R-2"

    def test_none_returns_all(self):
        assert filter_rules_by_status(_RULES, None) == _RULES

    def test_empty_string_returns_all(self):
        assert filter_rules_by_status(_RULES, "") == _RULES

    def test_no_match(self):
        assert filter_rules_by_status(_RULES, "draft") == []

    def test_empty_list(self):
        assert filter_rules_by_status([], "active") == []


# ── filter_rules_by_category ─────────────────────────


class TestFilterByCategory:
    def test_filters_security(self):
        result = filter_rules_by_category(_RULES, "security")
        assert len(result) == 2

    def test_filters_ops(self):
        result = filter_rules_by_category(_RULES, "ops")
        assert len(result) == 1

    def test_none_returns_all(self):
        assert filter_rules_by_category(_RULES, None) == _RULES

    def test_empty_string_returns_all(self):
        assert filter_rules_by_category(_RULES, "") == _RULES

    def test_no_match(self):
        assert filter_rules_by_category(_RULES, "compliance") == []


# ── filter_rules_by_search ───────────────────────────


class TestFilterBySearch:
    def test_search_by_title(self):
        result = filter_rules_by_search(_RULES, "First")
        assert len(result) == 1
        assert result[0]["rule_id"] == "R-1"

    def test_search_case_insensitive(self):
        result = filter_rules_by_search(_RULES, "first rule")
        assert len(result) == 1

    def test_search_by_rule_id(self):
        result = filter_rules_by_search(_RULES, "R-2")
        assert len(result) == 1
        assert result[0]["title"] == "Second Rule"

    def test_search_by_directive(self):
        result = filter_rules_by_search(_RULES, "Do Z")
        assert len(result) == 1
        assert result[0]["rule_id"] == "R-3"

    def test_empty_query_returns_all(self):
        assert filter_rules_by_search(_RULES, "") == _RULES

    def test_no_match(self):
        assert filter_rules_by_search(_RULES, "nonexistent") == []

    def test_partial_match(self):
        result = filter_rules_by_search(_RULES, "Rule")
        assert len(result) == 3  # All have "Rule" in title

    def test_none_fields_handled(self):
        rules = [{"rule_id": "R-1", "title": None, "directive": None}]
        result = filter_rules_by_search(rules, "test")
        assert result == []


# ── sort_rules ────────────────────────────────────────


class TestSortRules:
    def test_sort_by_title_ascending(self):
        result = sort_rules(_RULES, "title", ascending=True)
        assert result[0]["title"] == "First Rule"
        assert result[-1]["title"] == "Third Rule"

    def test_sort_by_title_descending(self):
        result = sort_rules(_RULES, "title", ascending=False)
        assert result[0]["title"] == "Third Rule"
        assert result[-1]["title"] == "First Rule"

    def test_returns_new_list(self):
        result = sort_rules(_RULES, "title")
        assert result is not _RULES

    def test_sort_by_status(self):
        result = sort_rules(_RULES, "status")
        assert result[0]["status"] == "active"

    def test_empty_list(self):
        assert sort_rules([], "title") == []

    def test_missing_column(self):
        result = sort_rules(_RULES, "nonexistent")
        assert len(result) == 3  # Still returns all items
