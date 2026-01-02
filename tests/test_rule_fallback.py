"""
Tests for Rule Fallback Parser
==============================
Per GAP-MCP-004: Rule fallback to markdown files.
"""

import pytest
from pathlib import Path

from governance.mcp_tools.rule_fallback import (
    parse_markdown_rules,
    get_all_markdown_rules,
    get_markdown_rule_by_id,
    filter_markdown_rules,
    markdown_rule_to_dict,
    get_rules_directory,
)


# Sample markdown content for testing
SAMPLE_MARKDOWN = """
# Test Rules

---

## RULE-001: Session Evidence Logging

**Category:** `governance` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive

All agent sessions MUST produce evidence logs that include:

1. **Thought Chain Documentation**
   - Every decision point with rationale

### Validation
- [ ] Session log exists

---

## RULE-007: MCP Usage Protocol

**Category:** `technical` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

Use MCP tools correctly. No manual implementations.

---
"""


class TestMarkdownParser:
    """Test markdown rule parsing."""

    def test_parse_markdown_rules_basic(self):
        """Parse rules from markdown content."""
        rules = parse_markdown_rules(SAMPLE_MARKDOWN, "TEST.md")

        assert len(rules) == 2
        assert rules[0].id == "RULE-001"
        assert rules[0].name == "Session Evidence Logging"
        assert rules[0].category == "governance"
        assert rules[0].priority == "CRITICAL"
        assert rules[0].status == "ACTIVE"
        assert "evidence logs" in rules[0].directive

    def test_parse_markdown_rules_second_rule(self):
        """Verify second rule in sequence."""
        rules = parse_markdown_rules(SAMPLE_MARKDOWN, "TEST.md")

        assert rules[1].id == "RULE-007"
        assert rules[1].name == "MCP Usage Protocol"
        assert rules[1].category == "technical"
        assert rules[1].priority == "HIGH"

    def test_parse_markdown_rules_source_file(self):
        """Source file is tracked."""
        rules = parse_markdown_rules(SAMPLE_MARKDOWN, "RULES-TEST.md")

        for rule in rules:
            assert rule.source_file == "RULES-TEST.md"

    def test_filter_markdown_rules_by_category(self):
        """Filter rules by category."""
        rules = parse_markdown_rules(SAMPLE_MARKDOWN, "TEST.md")
        filtered = filter_markdown_rules(rules, category="governance")

        assert len(filtered) == 1
        assert filtered[0].id == "RULE-001"

    def test_filter_markdown_rules_by_priority(self):
        """Filter rules by priority."""
        rules = parse_markdown_rules(SAMPLE_MARKDOWN, "TEST.md")
        filtered = filter_markdown_rules(rules, priority="HIGH")

        assert len(filtered) == 1
        assert filtered[0].id == "RULE-007"

    def test_filter_markdown_rules_by_status(self):
        """Filter rules by status."""
        rules = parse_markdown_rules(SAMPLE_MARKDOWN, "TEST.md")
        filtered = filter_markdown_rules(rules, status="ACTIVE")

        assert len(filtered) == 2  # Both are ACTIVE

    def test_markdown_rule_to_dict(self):
        """Convert MarkdownRule to dict."""
        rules = parse_markdown_rules(SAMPLE_MARKDOWN, "TEST.md")
        result = markdown_rule_to_dict(rules[0])

        assert result["id"] == "RULE-001"
        assert result["name"] == "Session Evidence Logging"
        assert result["source"] == "markdown"
        assert result["source_file"] == "TEST.md"


class TestRulesDirectory:
    """Test rules directory detection."""

    def test_get_rules_directory_returns_path(self):
        """Rules directory returns a Path object."""
        rules_dir = get_rules_directory()
        assert isinstance(rules_dir, Path)

    def test_rules_directory_exists(self):
        """Rules directory exists in project."""
        rules_dir = get_rules_directory()
        assert rules_dir.exists(), f"Expected rules at {rules_dir}"


class TestRealMarkdownFiles:
    """Test with actual project markdown files."""

    def test_get_all_markdown_rules(self):
        """Load all rules from actual markdown files."""
        rules = get_all_markdown_rules()

        # Should have multiple rules from docs/rules/*.md
        assert len(rules) > 0, "No rules found in docs/rules/"

    def test_get_markdown_rule_by_id_exists(self):
        """Get specific rule by ID."""
        rule = get_markdown_rule_by_id("RULE-001")

        assert rule is not None
        assert rule.id == "RULE-001"
        assert rule.name == "Session Evidence Logging"

    def test_get_markdown_rule_by_id_not_found(self):
        """Get nonexistent rule returns None."""
        rule = get_markdown_rule_by_id("RULE-999")

        assert rule is None

    def test_known_rules_present(self):
        """Verify known rules are parseable."""
        rules = get_all_markdown_rules()
        rule_ids = [r.id for r in rules]

        # These should exist per CLAUDE.md Cross-Reference Index
        expected = ["RULE-001", "RULE-007", "RULE-012"]
        for expected_id in expected:
            assert expected_id in rule_ids, f"{expected_id} not found in parsed rules"

    def test_rules_have_required_fields(self):
        """All parsed rules have required fields."""
        rules = get_all_markdown_rules()

        for rule in rules:
            assert rule.id.startswith("RULE-"), f"Invalid ID format: {rule.id}"
            assert rule.name, f"Missing name for {rule.id}"
            assert rule.category, f"Missing category for {rule.id}"
            assert rule.priority in ["CRITICAL", "HIGH", "MEDIUM", "LOW"], \
                f"Invalid priority for {rule.id}: {rule.priority}"
            assert rule.status in ["ACTIVE", "DRAFT", "DEPRECATED"], \
                f"Invalid status for {rule.id}: {rule.status}"
