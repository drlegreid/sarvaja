"""
Unit tests for Rule Fallback Parser.

Batch 150: Tests for governance/mcp_tools/rule_fallback.py
- MarkdownRule dataclass
- parse_markdown_rules: header/metadata/directive parsing
- get_rules_directory: path resolution
- get_all_markdown_rules: file loading + sorting
- get_markdown_rule_by_id: lookup
- filter_markdown_rules: category/status/priority filtering
- markdown_rule_to_dict: conversion to dict
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.rule_fallback import (
    MarkdownRule,
    parse_markdown_rules,
    get_rules_directory,
    get_all_markdown_rules,
    get_markdown_rule_by_id,
    filter_markdown_rules,
    markdown_rule_to_dict,
    RULE_HEADER_PATTERN,
    METADATA_PATTERN,
)


_SAMPLE_MD = """\
# Rules Governance

## RULE-1: Evidence Requirement
**Category:** `Governance` | **Priority:** HIGH | **Status:** ACTIVE

### Directive
All sessions must produce evidence files.

---

## RULE-3: Trust Protocol
**Category:** `Trust` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive
Agents must maintain trust scores above threshold.
"""

_MINIMAL_MD = """\
## RULE-42: No Metadata Rule

Some content without proper metadata format.
"""


# ── MarkdownRule dataclass ──────────────────────────────

class TestMarkdownRule:
    def test_fields(self):
        r = MarkdownRule(
            id="RULE-001", name="Test", category="Governance",
            priority="HIGH", status="ACTIVE", directive="Do things",
            source_file="RULES-TEST.md",
        )
        assert r.id == "RULE-001"
        assert r.name == "Test"
        assert r.source_file == "RULES-TEST.md"


# ── Regex patterns ──────────────────────────────────────

class TestPatterns:
    def test_header_pattern_matches(self):
        m = RULE_HEADER_PATTERN.search("## RULE-1: Evidence Requirement")
        assert m is not None
        assert m.group(1) == "1"
        assert m.group(2) == "Evidence Requirement"

    def test_header_pattern_no_match(self):
        assert RULE_HEADER_PATTERN.search("### RULE-1: Not H2") is None

    def test_metadata_pattern_matches(self):
        line = "**Category:** `Governance` | **Priority:** HIGH | **Status:** ACTIVE"
        m = METADATA_PATTERN.search(line)
        assert m is not None
        assert m.group(1).strip() == "Governance"
        assert m.group(2) == "HIGH"
        assert m.group(3) == "ACTIVE"


# ── parse_markdown_rules ────────────────────────────────

class TestParseMarkdownRules:
    def test_parses_two_rules(self):
        rules = parse_markdown_rules(_SAMPLE_MD, "RULES-GOV.md")
        assert len(rules) == 2

    def test_first_rule_id_padded(self):
        rules = parse_markdown_rules(_SAMPLE_MD, "RULES-GOV.md")
        assert rules[0].id == "RULE-001"

    def test_first_rule_metadata(self):
        rules = parse_markdown_rules(_SAMPLE_MD, "RULES-GOV.md")
        assert rules[0].category == "Governance"
        assert rules[0].priority == "HIGH"
        assert rules[0].status == "ACTIVE"

    def test_second_rule(self):
        rules = parse_markdown_rules(_SAMPLE_MD, "RULES-GOV.md")
        assert rules[1].id == "RULE-003"
        assert rules[1].name == "Trust Protocol"
        assert rules[1].priority == "CRITICAL"

    def test_directive_extracted(self):
        rules = parse_markdown_rules(_SAMPLE_MD, "RULES-GOV.md")
        assert "evidence files" in rules[0].directive

    def test_source_file_set(self):
        rules = parse_markdown_rules(_SAMPLE_MD, "RULES-GOV.md")
        assert rules[0].source_file == "RULES-GOV.md"

    def test_no_metadata_defaults(self):
        rules = parse_markdown_rules(_MINIMAL_MD, "TEST.md")
        assert len(rules) == 1
        assert rules[0].category == "unknown"
        assert rules[0].priority == "MEDIUM"
        assert rules[0].status == "ACTIVE"

    def test_no_directive_fallback(self):
        rules = parse_markdown_rules(_MINIMAL_MD, "TEST.md")
        assert "TEST.md" in rules[0].directive

    def test_empty_content(self):
        rules = parse_markdown_rules("", "EMPTY.md")
        assert rules == []

    def test_long_directive_truncated(self):
        long = "### Directive\n" + "x" * 600
        md = f"## RULE-99: Long\n{long}"
        rules = parse_markdown_rules(md, "T.md")
        assert len(rules[0].directive) <= 503  # 500 + "..."


# ── get_rules_directory ─────────────────────────────────

class TestGetRulesDirectory:
    def test_returns_path_object(self):
        result = get_rules_directory()
        assert isinstance(result, Path)
        assert str(result).endswith("docs/rules")


# ── get_all_markdown_rules ──────────────────────────────

class TestGetAllMarkdownRules:
    @patch("governance.mcp_tools.rule_fallback.get_rules_directory")
    def test_nonexistent_dir(self, mock_dir):
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_dir.return_value = mock_path
        assert get_all_markdown_rules() == []

    @patch("governance.mcp_tools.rule_fallback.get_rules_directory")
    def test_parses_and_sorts(self, mock_dir, tmp_path):
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "RULES-GOV.md").write_text(_SAMPLE_MD)
        mock_dir.return_value = rules_dir

        result = get_all_markdown_rules()
        assert len(result) == 2
        assert result[0].id == "RULE-001"
        assert result[1].id == "RULE-003"

    @patch("governance.mcp_tools.rule_fallback.get_rules_directory")
    def test_skips_bad_files(self, mock_dir, tmp_path):
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        bad = rules_dir / "RULES-BAD.md"
        bad.write_text("")  # Empty file, no rules
        mock_dir.return_value = rules_dir

        result = get_all_markdown_rules()
        assert result == []

    @patch("governance.mcp_tools.rule_fallback.get_rules_directory")
    def test_ignores_non_rules_files(self, mock_dir, tmp_path):
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "README.md").write_text(_SAMPLE_MD)  # Not RULES-*.md
        mock_dir.return_value = rules_dir

        result = get_all_markdown_rules()
        assert result == []


# ── get_markdown_rule_by_id ─────────────────────────────

class TestGetMarkdownRuleById:
    @patch("governance.mcp_tools.rule_fallback.get_all_markdown_rules")
    def test_found(self, mock_all):
        r = MarkdownRule("RULE-001", "Test", "Gov", "HIGH", "ACTIVE", "d", "f.md")
        mock_all.return_value = [r]
        assert get_markdown_rule_by_id("RULE-001") is r

    @patch("governance.mcp_tools.rule_fallback.get_all_markdown_rules")
    def test_not_found(self, mock_all):
        mock_all.return_value = []
        assert get_markdown_rule_by_id("RULE-999") is None


# ── filter_markdown_rules ───────────────────────────────

class TestFilterMarkdownRules:
    @pytest.fixture
    def rules(self):
        return [
            MarkdownRule("R-1", "A", "Governance", "HIGH", "ACTIVE", "d", "f"),
            MarkdownRule("R-2", "B", "Trust", "LOW", "ACTIVE", "d", "f"),
            MarkdownRule("R-3", "C", "Governance", "HIGH", "DEPRECATED", "d", "f"),
        ]

    def test_no_filter(self, rules):
        assert len(filter_markdown_rules(rules)) == 3

    def test_by_category(self, rules):
        result = filter_markdown_rules(rules, category="governance")
        assert len(result) == 2

    def test_by_status(self, rules):
        result = filter_markdown_rules(rules, status="deprecated")
        assert len(result) == 1
        assert result[0].id == "R-3"

    def test_by_priority(self, rules):
        result = filter_markdown_rules(rules, priority="low")
        assert len(result) == 1
        assert result[0].id == "R-2"

    def test_combined_filters(self, rules):
        result = filter_markdown_rules(rules, category="governance", status="active")
        assert len(result) == 1
        assert result[0].id == "R-1"

    def test_no_match(self, rules):
        result = filter_markdown_rules(rules, category="nonexistent")
        assert result == []


# ── markdown_rule_to_dict ───────────────────────────────

class TestMarkdownRuleToDict:
    def test_conversion(self):
        r = MarkdownRule("RULE-001", "Test", "Gov", "HIGH", "ACTIVE", "dir", "f.md")
        d = markdown_rule_to_dict(r)
        assert d["id"] == "RULE-001"
        assert d["name"] == "Test"
        assert d["source"] == "markdown"
        assert d["source_file"] == "f.md"
        assert d["directive"] == "dir"

    def test_all_keys_present(self):
        r = MarkdownRule("R-1", "N", "C", "P", "S", "D", "F")
        d = markdown_rule_to_dict(r)
        expected_keys = {"id", "name", "category", "priority", "status",
                         "directive", "source", "source_file"}
        assert set(d.keys()) == expected_keys
