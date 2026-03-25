"""
Unit tests for SEMANTIC_ONLY_RULES frozenset and normalize_rule_id() semantic-only handling.

Per EPIC-GOV-RULES-V3 P7: Legacy ID Debt + Semantic-Only Rule CRUD.
TDD RED: These tests fail until SEMANTIC_ONLY_RULES is extracted from SEMANTIC_TO_LEGACY.
"""

from governance.rule_linker_ids import (
    SEMANTIC_ONLY_RULES,
    SEMANTIC_TO_LEGACY,
    LEGACY_TO_SEMANTIC,
    normalize_rule_id,
)

# The 10 semantic-only rule IDs (self-mapped before extraction)
EXPECTED_SEMANTIC_ONLY = frozenset({
    "CONTAINER-TYPEDB-01-v1",
    "PKG-LATEST-01-v1",
    "DOC-GAP-ARCHIVE-01-v1",
    "TASK-TECH-01-v1",
    "TASK-LIFE-01-v1",
    "UI-LOADER-01-v1",
    "UI-TRACE-01-v1",
    "TEST-BDD-01-v1",
    "GAP-DOC-01-v1",
    "TASK-VALID-01-v1",
})


class TestSemanticOnlyFrozenset:
    def test_semantic_only_rules_frozenset_has_10_entries(self):
        assert isinstance(SEMANTIC_ONLY_RULES, frozenset)
        assert len(SEMANTIC_ONLY_RULES) == 10

    def test_semantic_only_rules_contains_expected_ids(self):
        assert SEMANTIC_ONLY_RULES == EXPECTED_SEMANTIC_ONLY

    def test_self_mapped_entries_removed_from_semantic_to_legacy(self):
        """Self-mapped entries must NOT appear in SEMANTIC_TO_LEGACY."""
        for rule_id in EXPECTED_SEMANTIC_ONLY:
            assert rule_id not in SEMANTIC_TO_LEGACY, (
                f"{rule_id} should not be in SEMANTIC_TO_LEGACY"
            )

    def test_no_overlap_between_semantic_only_and_legacy_map(self):
        """No rule ID should appear in both SEMANTIC_ONLY_RULES and SEMANTIC_TO_LEGACY."""
        overlap = SEMANTIC_ONLY_RULES & set(SEMANTIC_TO_LEGACY.keys())
        assert overlap == set(), f"Overlap found: {overlap}"

    def test_semantic_only_not_in_reverse_map(self):
        """Semantic-only IDs should not pollute LEGACY_TO_SEMANTIC reverse map."""
        for rule_id in EXPECTED_SEMANTIC_ONLY:
            assert rule_id not in LEGACY_TO_SEMANTIC, (
                f"{rule_id} should not be a value in LEGACY_TO_SEMANTIC"
            )


class TestNormalizeSemanticOnly:
    def test_normalize_rule_id_semantic_only_returns_same_id(self):
        """Semantic-only IDs should be returned as-is."""
        for rule_id in EXPECTED_SEMANTIC_ONLY:
            assert normalize_rule_id(rule_id) == rule_id

    def test_normalize_rule_id_semantic_only_no_warning(self, caplog):
        """Semantic-only IDs should NOT produce an 'Unknown rule ID' warning."""
        import logging
        with caplog.at_level(logging.WARNING, logger="governance.rule_linker_ids"):
            normalize_rule_id("CONTAINER-TYPEDB-01-v1")
        assert "Unknown rule ID format" not in caplog.text

    def test_normalize_rule_id_legacy_still_maps_correctly(self):
        """Legacy mappings must still work after extraction."""
        assert normalize_rule_id("SESSION-EVID-01-v1") == "RULE-001"
        assert normalize_rule_id("DOC-SIZE-01-v1") == "RULE-032"
        assert normalize_rule_id("SAFETY-DESTR-01-v1") == "RULE-042"

    def test_normalize_rule_id_unknown_still_warns(self, caplog):
        """Unknown IDs should still produce a warning."""
        import logging
        with caplog.at_level(logging.WARNING, logger="governance.rule_linker_ids"):
            result = normalize_rule_id("TOTALLY-FAKE-01-v1")
        assert result == "TOTALLY-FAKE-01-v1"
        assert "Unknown rule ID format" in caplog.text
