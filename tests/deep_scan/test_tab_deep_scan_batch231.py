"""Batch 231 — DSM tracker + models defense tests.

Validates fixes for:
- BUG-231-006: phases_completed dedup to prevent progress_percent > 100%
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-231-006: Phase dedup in DSM tracker ──────────────────────────

class TestDSMPhaseDedup:
    """phases_completed must not contain duplicates."""

    def test_complete_cycle_has_dedup_guard(self):
        src = (SRC / "governance/dsm/tracker.py").read_text()
        idx = src.index("def complete_cycle")
        block = src[idx:idx + 500]
        assert "BUG-231-006" in block

    def test_advance_phase_has_dedup_guard(self):
        """The BUG-231-006 dedup fix must appear in advance_phase."""
        src = (SRC / "governance/dsm/tracker.py").read_text()
        # Find the advance_phase function body (up to next def)
        start = src.index("def advance_phase")
        next_def = src.index("\n    def ", start + 1)
        block = src[start:next_def]
        assert "BUG-231-006" in block

    def test_no_unconditional_append(self):
        """All append sites should check 'not in phases_completed' first."""
        src = (SRC / "governance/dsm/tracker.py").read_text()
        # Count unconditional appends (no dedup check on preceding line)
        lines = src.splitlines()
        bad_appends = 0
        for i, line in enumerate(lines):
            if "phases_completed.append(" in line:
                # Check the line before for dedup guard
                prev = lines[i - 1] if i > 0 else ""
                if "not in self.current_cycle.phases_completed" not in prev:
                    bad_appends += 1
        assert bad_appends == 0, f"Found {bad_appends} unconditional phase appends"


# ── DSM module import defense tests ──────────────────────────────────

class TestDSMImports:
    """Defense tests for governance.dsm modules."""

    def test_tracker_importable(self):
        import governance.dsm.tracker
        assert governance.dsm.tracker is not None

    def test_tracker_persistence_importable(self):
        import governance.dsm.tracker_persistence
        assert governance.dsm.tracker_persistence is not None

    def test_phases_importable(self):
        import governance.dsm.phases
        assert governance.dsm.phases is not None

    def test_models_importable(self):
        import governance.dsm.models
        assert governance.dsm.models is not None

    def test_validation_importable(self):
        import governance.dsm.validation
        assert governance.dsm.validation is not None

    def test_evidence_importable(self):
        import governance.dsm.evidence
        assert governance.dsm.evidence is not None

    def test_memory_importable(self):
        import governance.dsm.memory
        assert governance.dsm.memory is not None
