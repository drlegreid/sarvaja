"""
Unit tests for Rule Fallback Parser.

Per GAP-MCP-004: Tests for rule_fallback.py markdown parser.
Tests: MarkdownRule, parse_markdown_rules, filter_markdown_rules,
       markdown_rule_to_dict, get_rules_directory.
"""

import pytest

from governance.mcp_tools.rule_fallback import (
    MarkdownRule,
    parse_markdown_rules,
    filter_markdown_rules,
    markdown_rule_to_dict,
    get_rules_directory,
    RULE_HEADER_PATTERN,
    METADATA_PATTERN,
)


SAMPLE_MD = """\
# Rules Governance

## RULE-1: Evidence Tracking
**Category:** `governance` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive
All sessions must produce evidence files.

---

## RULE-3: Decision Recording
**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE

### Directive
Record all decisions with rationale and evidence links.

---

## RULE-11: Multi-Agent Trust
**Category:** `governance` | **Priority:** HIGH | **Status:** DEPRECATED

### Directive
Trust scores determine agent capabilities.
"""


class TestMarkdownRule:
    """Tests for MarkdownRule dataclass."""

    def test_creation(self):
        rule = MarkdownRule(
            id="RULE-001", name="Evidence Tracking",
            category="governance", priority="CRITICAL",
            status="ACTIVE", directive="All sessions must produce evidence",
            source_file="RULES-GOVERNANCE.md",
        )
        assert rule.id == "RULE-001"
        assert rule.name == "Evidence Tracking"
        assert rule.category == "governance"
        assert rule.priority == "CRITICAL"
        assert rule.status == "ACTIVE"
        assert rule.source_file == "RULES-GOVERNANCE.md"


class TestParseMarkdownRules:
    """Tests for parse_markdown_rules()."""

    def test_parses_three_rules(self):
        rules = parse_markdown_rules(SAMPLE_MD, "RULES-GOVERNANCE.md")
        assert len(rules) == 3

    def test_first_rule_id(self):
        rules = parse_markdown_rules(SAMPLE_MD, "test.md")
        assert rules[0].id == "RULE-001"

    def test_first_rule_name(self):
        rules = parse_markdown_rules(SAMPLE_MD, "test.md")
        assert rules[0].name == "Evidence Tracking"

    def test_first_rule_metadata(self):
        rules = parse_markdown_rules(SAMPLE_MD, "test.md")
        assert rules[0].category == "governance"
        assert rules[0].priority == "CRITICAL"
        assert rules[0].status == "ACTIVE"

    def test_parses_directive(self):
        rules = parse_markdown_rules(SAMPLE_MD, "test.md")
        assert "evidence" in rules[0].directive.lower()

    def test_deprecated_rule(self):
        rules = parse_markdown_rules(SAMPLE_MD, "test.md")
        deprecated = [r for r in rules if r.status == "DEPRECATED"]
        assert len(deprecated) == 1
        assert deprecated[0].id == "RULE-011"

    def test_source_file_tracked(self):
        rules = parse_markdown_rules(SAMPLE_MD, "RULES-GOVERNANCE.md")
        for r in rules:
            assert r.source_file == "RULES-GOVERNANCE.md"

    def test_empty_content(self):
        rules = parse_markdown_rules("", "empty.md")
        assert rules == []

    def test_no_rules_content(self):
        rules = parse_markdown_rules("# No rules here\nJust text.", "none.md")
        assert rules == []

    def test_missing_metadata_defaults(self):
        md = "## RULE-99: Test Rule\nNo metadata here.\n"
        rules = parse_markdown_rules(md, "test.md")
        assert len(rules) == 1
        assert rules[0].category == "unknown"
        assert rules[0].priority == "MEDIUM"
        assert rules[0].status == "ACTIVE"

    def test_missing_directive_fallback(self):
        md = "## RULE-50: No Directive\n**Category:** `tech` | **Priority:** LOW | **Status:** ACTIVE\n"
        rules = parse_markdown_rules(md, "test.md")
        assert len(rules) == 1
        assert "test.md" in rules[0].directive

    def test_long_directive_truncated(self):
        long_directive = "A" * 600
        md = f"## RULE-88: Long Rule\n### Directive\n{long_directive}\n"
        rules = parse_markdown_rules(md, "test.md")
        assert len(rules[0].directive) <= 503  # 500 + "..."

    def test_rule_id_zero_padded(self):
        md = "## RULE-1: Test\n"
        rules = parse_markdown_rules(md, "test.md")
        assert rules[0].id == "RULE-001"

    def test_multi_digit_rule_id(self):
        md = "## RULE-14: Multi Digit\n"
        rules = parse_markdown_rules(md, "test.md")
        assert rules[0].id == "RULE-014"


class TestFilterMarkdownRules:
    """Tests for filter_markdown_rules()."""

    @pytest.fixture
    def rules(self):
        return parse_markdown_rules(SAMPLE_MD, "test.md")

    def test_no_filter(self, rules):
        result = filter_markdown_rules(rules)
        assert len(result) == 3

    def test_filter_by_category(self, rules):
        result = filter_markdown_rules(rules, category="governance")
        assert len(result) == 3

    def test_filter_by_status(self, rules):
        result = filter_markdown_rules(rules, status="ACTIVE")
        assert len(result) == 2

    def test_filter_by_priority(self, rules):
        result = filter_markdown_rules(rules, priority="CRITICAL")
        assert len(result) == 1
        assert result[0].id == "RULE-001"

    def test_filter_case_insensitive(self, rules):
        result = filter_markdown_rules(rules, category="GOVERNANCE")
        assert len(result) == 3

    def test_filter_multiple_criteria(self, rules):
        result = filter_markdown_rules(rules, category="governance", priority="HIGH")
        assert len(result) == 2

    def test_filter_no_match(self, rules):
        result = filter_markdown_rules(rules, category="nonexistent")
        assert len(result) == 0

    def test_filter_empty_list(self):
        result = filter_markdown_rules([])
        assert result == []


class TestMarkdownRuleToDict:
    """Tests for markdown_rule_to_dict()."""

    def test_converts_to_dict(self):
        rule = MarkdownRule(
            id="RULE-007", name="MCP Protocol",
            category="technical", priority="CRITICAL",
            status="ACTIVE", directive="Use MCP for all comms",
            source_file="RULES-TECHNICAL.md",
        )
        d = markdown_rule_to_dict(rule)
        assert d["id"] == "RULE-007"
        assert d["name"] == "MCP Protocol"
        assert d["category"] == "technical"
        assert d["source"] == "markdown"
        assert d["source_file"] == "RULES-TECHNICAL.md"

    def test_source_always_markdown(self):
        rule = MarkdownRule("R-1", "N", "C", "P", "S", "D", "F")
        d = markdown_rule_to_dict(rule)
        assert d["source"] == "markdown"


class TestGetRulesDirectory:
    """Tests for get_rules_directory()."""

    def test_returns_path(self):
        path = get_rules_directory()
        assert path is not None
        assert "docs" in str(path)
        assert "rules" in str(path)


class TestRegexPatterns:
    """Tests for regex patterns."""

    def test_header_pattern_matches(self):
        match = RULE_HEADER_PATTERN.search("## RULE-1: Evidence Tracking")
        assert match is not None
        assert match.group(1) == "1"
        assert match.group(2) == "Evidence Tracking"

    def test_header_pattern_multi_digit(self):
        match = RULE_HEADER_PATTERN.search("## RULE-14: Task Sequencing")
        assert match is not None
        assert match.group(1) == "14"

    def test_metadata_pattern_matches(self):
        line = "**Category:** `governance` | **Priority:** CRITICAL | **Status:** ACTIVE"
        match = METADATA_PATTERN.search(line)
        assert match is not None
        assert match.group(1).strip() == "governance"
        assert match.group(2) == "CRITICAL"
        assert match.group(3) == "ACTIVE"
