"""
Tests for rule ID mappings, normalization, and extraction.

Per META-TAXON-01-v1, GAP-MCP-008: Semantic ID support.
Covers ID normalization, pattern matching, and rule document scanning.

Created: 2026-01-30
"""

import re
import pytest

from governance.rule_linker_ids import (
    LEGACY_RULE_PATTERN,
    SEMANTIC_RULE_PATTERN,
    SEMANTIC_TO_LEGACY,
    LEGACY_TO_SEMANTIC,
    normalize_rule_id,
)
from governance.rule_linker_scan import extract_rule_ids


class TestLegacyRulePattern:
    """Test LEGACY_RULE_PATTERN regex."""

    def test_matches_rule_001(self):
        assert re.fullmatch(LEGACY_RULE_PATTERN, "RULE-001")

    def test_matches_rule_042(self):
        assert re.fullmatch(LEGACY_RULE_PATTERN, "RULE-042")

    def test_rejects_rule_1(self):
        """Must be 3 digits."""
        assert not re.fullmatch(LEGACY_RULE_PATTERN, "RULE-1")

    def test_rejects_lowercase(self):
        assert not re.fullmatch(LEGACY_RULE_PATTERN, "rule-001")

    def test_rejects_no_dash(self):
        assert not re.fullmatch(LEGACY_RULE_PATTERN, "RULE001")


class TestSemanticRulePattern:
    """Test SEMANTIC_RULE_PATTERN regex."""

    def test_two_segments(self):
        """Matches DOMAIN-SUB-NN-vN."""
        assert re.fullmatch(SEMANTIC_RULE_PATTERN, "SESSION-EVID-01-v1")

    def test_three_segments(self):
        """Matches DOMAIN-SUB-SUB-NN-vN."""
        assert re.fullmatch(SEMANTIC_RULE_PATTERN, "CONTAINER-RESTART-01-v1")

    def test_four_segments(self):
        """Matches DOMAIN-SUB-SUB-SUB-NN-vN."""
        assert re.fullmatch(SEMANTIC_RULE_PATTERN, "SESSION-DSP-NOTIFY-01-v1")

    def test_version_2(self):
        """Matches version 2+."""
        assert re.fullmatch(SEMANTIC_RULE_PATTERN, "GOV-RULE-01-v2")

    def test_rejects_single_segment(self):
        """Must have at least 2 segments before version."""
        assert not re.fullmatch(SEMANTIC_RULE_PATTERN, "RULE-01-v1")

    def test_rejects_lowercase(self):
        assert not re.fullmatch(SEMANTIC_RULE_PATTERN, "session-evid-01-v1")


class TestSemanticToLegacyMapping:
    """Test the SEMANTIC_TO_LEGACY mapping table."""

    def test_known_mapping(self):
        assert SEMANTIC_TO_LEGACY["SESSION-EVID-01-v1"] == "RULE-001"
        assert SEMANTIC_TO_LEGACY["DOC-SIZE-01-v1"] == "RULE-032"

    def test_reverse_mapping(self):
        assert LEGACY_TO_SEMANTIC["RULE-001"] == "SESSION-EVID-01-v1"
        assert LEGACY_TO_SEMANTIC["RULE-032"] == "DOC-SIZE-01-v1"

    def test_self_mapped_entries(self):
        """Some rules map to themselves (no legacy ID)."""
        assert SEMANTIC_TO_LEGACY["TASK-LIFE-01-v1"] == "TASK-LIFE-01-v1"

    def test_mapping_count(self):
        """Mapping has entries for all known rules."""
        assert len(SEMANTIC_TO_LEGACY) >= 50


class TestNormalizeRuleId:
    """Test rule ID normalization to legacy format."""

    def test_legacy_unchanged(self):
        """Legacy ID returned as-is."""
        assert normalize_rule_id("RULE-001") == "RULE-001"
        assert normalize_rule_id("RULE-042") == "RULE-042"

    def test_semantic_to_legacy(self):
        """Semantic ID converted to legacy."""
        assert normalize_rule_id("SESSION-EVID-01-v1") == "RULE-001"
        assert normalize_rule_id("DOC-SIZE-01-v1") == "RULE-032"

    def test_unknown_returned_as_is(self):
        """Unknown ID returned unchanged."""
        assert normalize_rule_id("UNKNOWN-RULE-99-v1") == "UNKNOWN-RULE-99-v1"

    def test_self_mapped(self):
        """Self-mapped semantic IDs returned as-is."""
        assert normalize_rule_id("TASK-LIFE-01-v1") == "TASK-LIFE-01-v1"


class TestExtractRuleIds:
    """Test rule ID extraction from markdown content."""

    def test_legacy_ids(self):
        """Extract legacy RULE-NNN IDs."""
        content = "Per RULE-001 and RULE-042: do something."
        ids = extract_rule_ids(content)
        assert "RULE-001" in ids
        assert "RULE-042" in ids

    def test_semantic_ids_converted(self):
        """Semantic IDs converted to legacy in output."""
        content = "Per SESSION-EVID-01-v1: evidence rules."
        ids = extract_rule_ids(content)
        assert "RULE-001" in ids  # Converted from SESSION-EVID-01-v1

    def test_dedup(self):
        """Duplicate IDs deduplicated."""
        content = "RULE-001 and again RULE-001"
        ids = extract_rule_ids(content)
        assert ids.count("RULE-001") == 1

    def test_sorted_by_number(self):
        """Results sorted by rule number."""
        content = "RULE-042 then RULE-001 then RULE-010"
        ids = extract_rule_ids(content)
        assert ids.index("RULE-001") < ids.index("RULE-010")
        assert ids.index("RULE-010") < ids.index("RULE-042")

    def test_empty_content(self):
        """Empty content returns empty list."""
        assert extract_rule_ids("") == []

    def test_no_rules(self):
        """Content without rules returns empty list."""
        assert extract_rule_ids("Just some regular text.") == []

    def test_mixed_formats(self):
        """Both legacy and semantic IDs extracted together."""
        content = "Per RULE-042 and DOC-SIZE-01-v1: file size limit."
        ids = extract_rule_ids(content)
        assert "RULE-042" in ids
        assert "RULE-032" in ids  # DOC-SIZE-01-v1 -> RULE-032

    def test_unknown_semantic_skipped(self):
        """Unknown semantic IDs not added to results."""
        content = "Per FAKE-RULE-99-v1: not real."
        ids = extract_rule_ids(content)
        assert len(ids) == 0
