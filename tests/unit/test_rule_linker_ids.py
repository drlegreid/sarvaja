"""
Unit tests for Rule ID Mappings and Patterns.

Per DOC-SIZE-01-v1: Tests for rule_linker_ids.py module.
Tests: SEMANTIC_TO_LEGACY, LEGACY_TO_SEMANTIC, normalize_rule_id(), patterns.
"""

import re
from governance.rule_linker_ids import (
    LEGACY_RULE_PATTERN,
    SEMANTIC_RULE_PATTERN,
    SEMANTIC_TO_LEGACY,
    LEGACY_TO_SEMANTIC,
    RULE_DOCUMENT_MAP,
    normalize_rule_id,
)


class TestPatterns:
    def test_legacy_matches(self):
        assert re.match(LEGACY_RULE_PATTERN, "RULE-001")
        assert re.match(LEGACY_RULE_PATTERN, "RULE-042")
        assert not re.match(LEGACY_RULE_PATTERN, "RULE-1")

    def test_semantic_matches(self):
        assert re.match(SEMANTIC_RULE_PATTERN, "SESSION-EVID-01-v1")
        assert re.match(SEMANTIC_RULE_PATTERN, "GOV-BICAM-01-v1")
        assert re.match(SEMANTIC_RULE_PATTERN, "DOC-SIZE-01-v1")
        assert not re.match(SEMANTIC_RULE_PATTERN, "RULE-001")


class TestMappings:
    def test_semantic_to_legacy_populated(self):
        assert len(SEMANTIC_TO_LEGACY) > 50
        assert SEMANTIC_TO_LEGACY["SESSION-EVID-01-v1"] == "RULE-001"
        assert SEMANTIC_TO_LEGACY["DOC-SIZE-01-v1"] == "RULE-032"

    def test_reverse_mapping(self):
        assert LEGACY_TO_SEMANTIC["RULE-001"] == "SESSION-EVID-01-v1"
        assert LEGACY_TO_SEMANTIC["RULE-032"] == "DOC-SIZE-01-v1"

    def test_no_identity_mappings_in_semantic_to_legacy(self):
        # Per P7: Self-mapped entries extracted to SEMANTIC_ONLY_RULES
        for k, v in SEMANTIC_TO_LEGACY.items():
            assert k != v, f"Self-mapped entry {k} should be in SEMANTIC_ONLY_RULES"

    def test_document_map(self):
        assert len(RULE_DOCUMENT_MAP) > 0
        for doc_path, rules in RULE_DOCUMENT_MAP.items():
            assert doc_path.endswith(".md")
            for r in rules:
                assert r.startswith("RULE-")


class TestNormalizeRuleId:
    def test_legacy_passthrough(self):
        assert normalize_rule_id("RULE-001") == "RULE-001"
        assert normalize_rule_id("RULE-042") == "RULE-042"

    def test_semantic_to_legacy(self):
        assert normalize_rule_id("SESSION-EVID-01-v1") == "RULE-001"
        assert normalize_rule_id("DOC-SIZE-01-v1") == "RULE-032"

    def test_unknown_passthrough(self):
        assert normalize_rule_id("UNKNOWN-THING") == "UNKNOWN-THING"

    def test_semantic_only_returns_same_id(self):
        # Per P7: Semantic-only IDs return as-is via SEMANTIC_ONLY_RULES
        result = normalize_rule_id("CONTAINER-TYPEDB-01-v1")
        assert result == "CONTAINER-TYPEDB-01-v1"
