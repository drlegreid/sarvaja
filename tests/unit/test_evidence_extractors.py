"""
Tests for evidence_scanner extractors module.

Per BACKFILL-OPS-01-v1: Validates entity reference extraction from evidence files.
Per DOC-SIZE-01-v1: Tests the extracted extractors.py module.

Created: 2026-01-30
"""

import pytest
from pathlib import Path

from governance.evidence_scanner.extractors import (
    extract_task_refs,
    extract_rule_refs,
    extract_gap_refs,
    extract_session_id,
    TASK_PATTERNS,
    RULE_PATTERNS,
    GAP_PATTERNS,
    EVIDENCE_PATTERNS,
)


class TestExtractTaskRefs:
    """Test task ID extraction from content."""

    def test_frankel_hash_pattern(self):
        """Extract FH-NNN task IDs."""
        refs = extract_task_refs("Completed FH-001 and FH-042 today")
        assert "FH-001" in refs
        assert "FH-042" in refs

    def test_kanren_pattern(self):
        """Extract KAN-NNN task IDs."""
        refs = extract_task_refs("Working on KAN-005")
        assert "KAN-005" in refs

    def test_docview_pattern(self):
        """Extract DOCVIEW-NNN task IDs."""
        refs = extract_task_refs("DOCVIEW-003 is ready for review")
        assert "DOCVIEW-003" in refs

    def test_atest_pattern(self):
        """Extract ATEST-NNN task IDs."""
        refs = extract_task_refs("ATEST-001 passed")
        assert "ATEST-001" in refs

    def test_rd_pattern(self):
        """Extract RD-NNN task IDs."""
        refs = extract_task_refs("Researching RD-012")
        assert "RD-012" in refs

    def test_phase_task_pattern(self):
        """Extract P-format task IDs (P4.1, P10.2b)."""
        refs = extract_task_refs("Implemented P4.1 and P10.2b features")
        assert "P4.1" in refs
        assert "P10.2B" in refs

    def test_fix_pattern(self):
        """Extract FIX-XXX-NNN task IDs."""
        refs = extract_task_refs("Applied FIX-INFRA-001")
        assert "FIX-INFRA-001" in refs

    def test_ui_audit_pattern(self):
        """Extract UI-AUDIT-NNN task IDs."""
        refs = extract_task_refs("Per UI-AUDIT-010: Dashboard tests")
        assert "UI-AUDIT-010" in refs

    def test_multi_pattern(self):
        """Extract MULTI-NNN task IDs."""
        refs = extract_task_refs("MULTI-007 delegation complete")
        assert "MULTI-007" in refs

    def test_case_insensitive(self):
        """Extract task IDs regardless of case."""
        refs = extract_task_refs("fh-001 and kan-005")
        assert "FH-001" in refs
        assert "KAN-005" in refs

    def test_no_matches(self):
        """Return empty set when no task IDs found."""
        refs = extract_task_refs("Just some text with no task references")
        assert len(refs) == 0

    def test_empty_content(self):
        """Return empty set for empty content."""
        refs = extract_task_refs("")
        assert len(refs) == 0

    def test_dedup(self):
        """Deduplicate repeated task IDs."""
        refs = extract_task_refs("FH-001 mentioned twice: FH-001")
        assert len(refs) == 1
        assert "FH-001" in refs


class TestExtractRuleRefs:
    """Test rule ID extraction from content."""

    def test_legacy_rule_pattern(self):
        """Extract RULE-NNN legacy IDs."""
        refs = extract_rule_refs("Per RULE-001 and RULE-012")
        assert "RULE-001" in refs
        assert "RULE-012" in refs

    def test_semantic_rule_pattern(self):
        """Extract semantic rule IDs (DOMAIN-SUB-NN-vN)."""
        refs = extract_rule_refs("Per SESSION-EVID-01-v1: Evidence required")
        assert "SESSION-EVID-01-v1" in refs

    def test_multiple_semantic_rules(self):
        """Extract multiple semantic rule IDs."""
        refs = extract_rule_refs(
            "Per TEST-GUARD-01-v1 and CONTAINER-DEV-01-v1"
        )
        assert "TEST-GUARD-01-v1" in refs
        assert "CONTAINER-DEV-01-v1" in refs

    def test_no_matches(self):
        """Return empty set when no rule IDs found."""
        refs = extract_rule_refs("No rules here")
        assert len(refs) == 0

    def test_mixed_legacy_and_semantic(self):
        """Extract both legacy and semantic rule IDs."""
        refs = extract_rule_refs("RULE-004 and DOC-SIZE-01-v1 apply")
        assert "RULE-004" in refs
        assert "DOC-SIZE-01-v1" in refs


class TestExtractGapRefs:
    """Test gap ID extraction from content."""

    def test_gap_pattern(self):
        """Extract GAP-XXX-NNN IDs."""
        refs = extract_gap_refs("Per GAP-UI-001 and GAP-MCP-008")
        assert "GAP-UI-001" in refs
        assert "GAP-MCP-008" in refs

    def test_no_matches(self):
        """Return empty set when no gap IDs found."""
        refs = extract_gap_refs("No gaps mentioned")
        assert len(refs) == 0

    def test_case_insensitive(self):
        """Extract gap IDs regardless of case."""
        refs = extract_gap_refs("gap-ui-001 is open")
        assert "GAP-UI-001" in refs


class TestExtractSessionId:
    """Test session ID extraction from filepath."""

    def test_session_file(self):
        """Extract session ID from SESSION-*.md filename."""
        path = Path("/evidence/SESSION-2026-01-30-TOPIC.md")
        assert extract_session_id(path) == "SESSION-2026-01-30-TOPIC"

    def test_dsm_file(self):
        """Extract session ID from DSM-*.md filename."""
        path = Path("/evidence/DSM-2026-01-25-015206.md")
        assert extract_session_id(path) == "DSM-2026-01-25-015206"

    def test_test_run_file(self):
        """Extract session ID from TEST-RUN-*.md filename."""
        path = Path("/evidence/TEST-RUN-2026-01-30-unit.md")
        assert extract_session_id(path) == "TEST-RUN-2026-01-30-unit"


class TestPatternConstants:
    """Verify pattern constants are properly defined."""

    def test_task_patterns_nonempty(self):
        """TASK_PATTERNS contains patterns."""
        assert len(TASK_PATTERNS) >= 9

    def test_rule_patterns_nonempty(self):
        """RULE_PATTERNS contains patterns."""
        assert len(RULE_PATTERNS) >= 2

    def test_gap_patterns_nonempty(self):
        """GAP_PATTERNS contains patterns."""
        assert len(GAP_PATTERNS) >= 1

    def test_evidence_patterns_keys(self):
        """EVIDENCE_PATTERNS maps glob patterns to types."""
        assert "SESSION-*.md" in EVIDENCE_PATTERNS
        assert "DSM-*.md" in EVIDENCE_PATTERNS
        assert "TEST-RUN-*.md" in EVIDENCE_PATTERNS
        assert EVIDENCE_PATTERNS["SESSION-*.md"] == "session"
