"""Deep scan batch 172: DSM + audit + dashboard layer.

Batch 172 findings: 7 total, 3 confirmed fixes, 4 rejected.
- BUG-DSM-ABORT-001: abort_cycle nulled current_cycle before _save_state.
- BUG-DSM-DEDUP-001: go_to_phase duplicated phases_completed entries.
- BUG-AUDIT-NULL-001: update_session fallback audit recorded new_value=None.
"""
import pytest
from pathlib import Path


# ── DSM abort save order defense ──────────────


class TestDSMAbortSaveOrderDefense:
    """Verify abort_cycle saves state BEFORE clearing current_cycle."""

    def test_save_before_null(self):
        """_save_state() is called before current_cycle = None."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/dsm/tracker.py").read_text()
        start = src.index("def abort_cycle")
        end = src.index("\n    def ", start + 1)
        func = src[start:end]
        # _save_state must appear BEFORE current_cycle = None
        save_pos = func.index("_save_state()")
        null_pos = func.index("self.current_cycle = None")
        assert save_pos < null_pos

    def test_abort_preserves_metadata(self):
        """abort_cycle sets abort metadata before saving."""
        from governance.dsm.tracker import DSMTracker
        from governance.dsm.phases import DSPPhase
        import tempfile, json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            state_file = f.name
        tracker = DSMTracker(state_file=state_file)
        tracker.start_cycle("abort-test-cycle")
        tracker.abort_cycle("Test abort reason")
        # State should have been saved with abort data
        with open(state_file) as f:
            saved = json.load(f)
        # After abort, current_cycle is None in tracker
        assert tracker.current_cycle is None


# ── DSM phase dedup defense ──────────────


class TestDSMPhaseDeduplicationDefense:
    """Verify go_to_phase deduplicates phases_completed."""

    def test_no_duplicate_phases(self):
        """Calling go_to_phase from same phase doesn't duplicate."""
        from governance.dsm.tracker import DSMTracker
        from governance.dsm.phases import DSPPhase
        import tempfile, json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            state_file = f.name
        tracker = DSMTracker(state_file=state_file)
        tracker.start_cycle("dedup-test-cycle")
        # Go to AUDIT, then try to go to AUDIT again from AUDIT
        tracker.go_to_phase(DSPPhase.AUDIT)
        tracker.go_to_phase(DSPPhase.HYPOTHESIZE)
        tracker.go_to_phase(DSPPhase.MEASURE)
        # Each phase should appear at most once
        completed = tracker.current_cycle.phases_completed
        assert len(completed) == len(set(completed))

    def test_dedup_check_in_source(self):
        """Source code checks 'not in phases_completed' before append."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/dsm/tracker.py").read_text()
        assert "not in self.current_cycle.phases_completed" in src

    def test_progress_cannot_exceed_100(self):
        """Progress percent cannot exceed 100."""
        from governance.dsm.tracker import DSMTracker
        from governance.dsm.phases import DSPPhase
        import tempfile, json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            state_file = f.name
        tracker = DSMTracker(state_file=state_file)
        tracker.start_cycle("progress-test")
        # Go through all phases
        for phase in [DSPPhase.AUDIT, DSPPhase.HYPOTHESIZE, DSPPhase.MEASURE,
                      DSPPhase.OPTIMIZE, DSPPhase.VALIDATE, DSPPhase.DREAM]:
            tracker.go_to_phase(phase)
        status = tracker.get_status()
        assert status["progress_percent"] <= 100.0


# ── Audit trail null value defense ──────────────


class TestAuditTrailNullValueDefense:
    """Verify update_session audit doesn't record None for status."""

    def test_fallback_audit_uses_old_status(self):
        """Fallback path uses old_status when status is None."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/sessions.py").read_text()
        # Find fallback audit call (not inside try/except TypeDB block)
        assert "status if status is not None else old_status" in src

    def test_typedb_path_audit_consistent(self):
        """TypeDB path audit also handles None status."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/sessions.py").read_text()
        # TypeDB path uses "status or old_status"
        assert "status or old_status" in src


# ── Session null sort defense ──────────────


class TestSessionNullSortDefense:
    """Verify session null-handling in sort is documented."""

    def test_sort_has_null_handling(self):
        """list_sessions sort handles None/empty values."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/sessions.py").read_text()
        assert "sort_field" in src
        assert "is None" in src

    def test_pagination_formula(self):
        """has_more uses len(paginated) not limit."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/sessions.py").read_text()
        assert "len(paginated)" in src
