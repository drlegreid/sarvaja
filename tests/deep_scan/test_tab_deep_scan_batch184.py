"""Deep scan batch 184: Evidence + DSM layer.

Batch 184 findings: 21 total, 1 confirmed fix, 20 rejected/deferred.
- BUG-184-007: Rule version regex misses v10+ (v\\d → v\\d+).
"""
import pytest
import re
from pathlib import Path


# ── Rule version pattern defense ──────────────


class TestRuleVersionPatternDefense:
    """Verify extractors.py RULE_PATTERNS handle multi-digit versions."""

    def test_semantic_rule_v1(self):
        """Pattern matches v1 single-digit version."""
        from governance.evidence_scanner.extractors import RULE_PATTERNS
        pattern = RULE_PATTERNS[1]  # Semantic pattern
        match = re.search(pattern, "per SESSION-EVID-01-v1 compliance")
        assert match is not None
        assert match.group(1) == "SESSION-EVID-01-v1"

    def test_semantic_rule_v10(self):
        """Pattern matches v10 two-digit version (BUG-184-007 fix)."""
        from governance.evidence_scanner.extractors import RULE_PATTERNS
        pattern = RULE_PATTERNS[1]
        match = re.search(pattern, "per SESSION-EVID-01-v10 compliance")
        assert match is not None
        assert match.group(1) == "SESSION-EVID-01-v10"

    def test_semantic_rule_v99(self):
        """Pattern matches v99 two-digit version."""
        from governance.evidence_scanner.extractors import RULE_PATTERNS
        pattern = RULE_PATTERNS[1]
        match = re.search(pattern, "GOV-TRUST-01-v99")
        assert match is not None
        assert match.group(1) == "GOV-TRUST-01-v99"

    def test_extract_rule_refs_multi_digit(self):
        """extract_rule_refs captures multi-digit versions."""
        from governance.evidence_scanner.extractors import extract_rule_refs
        text = "Per TEST-GUARD-01-v1 and DOC-SIZE-01-v12"
        refs = extract_rule_refs(text)
        assert "TEST-GUARD-01-v1" in refs
        assert "DOC-SIZE-01-v12" in refs

    def test_legacy_rule_pattern_unchanged(self):
        """Legacy RULE-NNN pattern still works."""
        from governance.evidence_scanner.extractors import extract_rule_refs
        refs = extract_rule_refs("See RULE-001 and RULE-042")
        assert "RULE-001" in refs
        assert "RULE-042" in refs


# ── DSM evidence defense ──────────────


class TestDSMEvidenceDefense:
    """Verify DSM evidence module structure."""

    def test_generate_evidence_signature(self):
        """generate_evidence requires cycle and evidence_dir."""
        import inspect
        from governance.dsm.evidence import generate_evidence
        sig = inspect.signature(generate_evidence)
        params = list(sig.parameters.keys())
        assert "cycle" in params
        assert "evidence_dir" in params

    def test_dsm_cycle_dataclass(self):
        """DSMCycle dataclass is importable."""
        from governance.dsm.models import DSMCycle
        assert DSMCycle is not None

    def test_tracker_persistence_importable(self):
        """TrackerPersistence module is importable."""
        from governance.dsm import tracker_persistence
        assert tracker_persistence is not None


# ── Evidence scanner structure defense ──────────────


class TestEvidenceScannerStructure:
    """Verify evidence scanner module integrity."""

    def test_extract_task_refs_importable(self):
        """extract_task_refs is importable."""
        from governance.evidence_scanner.extractors import extract_task_refs
        assert callable(extract_task_refs)

    def test_extract_gap_refs_importable(self):
        """extract_gap_refs is importable."""
        from governance.evidence_scanner.extractors import extract_gap_refs
        assert callable(extract_gap_refs)

    def test_extract_task_refs_basic(self):
        """extract_task_refs finds task IDs matching TASK_PATTERNS."""
        from governance.evidence_scanner.extractors import extract_task_refs
        # Use actual patterns: FH-001, KAN-001, P4.1
        refs = extract_task_refs("Completed FH-001 and KAN-042")
        assert len(refs) >= 2

    def test_extract_gap_refs_basic(self):
        """extract_gap_refs finds gap IDs."""
        from governance.evidence_scanner.extractors import extract_gap_refs
        refs = extract_gap_refs("Found GAP-UI-001 during review")
        assert "GAP-UI-001" in refs

    def test_evidence_patterns_dict(self):
        """EVIDENCE_PATTERNS maps patterns to types."""
        from governance.evidence_scanner.extractors import EVIDENCE_PATTERNS
        assert isinstance(EVIDENCE_PATTERNS, dict)
        assert "SESSION-*.md" in EVIDENCE_PATTERNS
