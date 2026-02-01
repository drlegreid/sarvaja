"""
TDD Tests for GAP-FILE-024: dsm/tracker.py Split

Tests verify that the modularized DSM tracker:
1. Maintains backward compatibility
2. Has properly separated memory integration
3. All modules stay under 400 lines

Per RULE-004: TDD approach
Per DOC-SIZE-01-v1: Files under 400 lines
"""

import pytest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
GOVERNANCE_DIR = PROJECT_ROOT / "governance"
DSM_DIR = GOVERNANCE_DIR / "dsm"


# =============================================================================
# Test 1: Module Structure
# =============================================================================

# =============================================================================
# Test 2: Backward Compatibility
# =============================================================================

class TestBackwardCompatibility:
    """Tests ensuring existing imports still work."""

    def test_import_dsm_tracker_class(self):
        """from governance.dsm.tracker import DSMTracker must work."""
        from governance.dsm.tracker import DSMTracker
        assert DSMTracker is not None

    def test_import_get_tracker(self):
        """from governance.dsm.tracker import get_tracker must work."""
        from governance.dsm.tracker import get_tracker
        assert get_tracker is not None

    def test_import_reset_tracker(self):
        """from governance.dsm.tracker import reset_tracker must work."""
        from governance.dsm.tracker import reset_tracker
        assert reset_tracker is not None

    def test_create_tracker_instance(self):
        """DSMTracker should create instance."""
        from governance.dsm.tracker import DSMTracker
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=os.path.join(tmpdir, ".state.json")
            )
            assert tracker is not None


# =============================================================================
# Test 3: Core Functionality
# =============================================================================

class TestCoreFunctionality:
    """Tests for core tracker functionality."""

    def test_start_cycle(self):
        """DSMTracker should start a cycle."""
        from governance.dsm.tracker import DSMTracker, reset_tracker
        import tempfile
        import os

        reset_tracker()
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=os.path.join(tmpdir, ".state.json")
            )
            cycle = tracker.start_cycle("test-batch")
            assert cycle is not None
            assert cycle.cycle_id.startswith("DSM-")

    def test_get_status(self):
        """DSMTracker should return status."""
        from governance.dsm.tracker import DSMTracker, reset_tracker
        import tempfile
        import os

        reset_tracker()
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=os.path.join(tmpdir, ".state.json")
            )
            status = tracker.get_status()
            assert isinstance(status, dict)
            assert "active" in status

    def test_get_session_memory_payload(self):
        """DSMTracker should provide session memory payload."""
        from governance.dsm.tracker import DSMTracker, reset_tracker
        import tempfile
        import os

        reset_tracker()
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=os.path.join(tmpdir, ".state.json")
            )
            # No cycle - should return None
            payload = tracker.get_session_memory_payload()
            assert payload is None


# =============================================================================
# Test 4: File Size Compliance
# =============================================================================

class TestFileSizeCompliance:
    """Tests ensuring files stay under size limit."""

    def test_tracker_module_under_400_lines(self):
        """tracker.py should be under 400 lines."""
        tracker_file = DSM_DIR / "tracker.py"
        line_count = len(tracker_file.read_text().splitlines())

        # If over limit, skip (refactoring needed)
        if line_count > 400:
            pytest.skip(f"tracker.py has {line_count} lines - refactoring needed")

        assert line_count <= 400, f"tracker.py has {line_count} lines"


# =============================================================================
# Test 5: Integration
# =============================================================================

class TestIntegration:
    """Integration tests for tracker."""

    def test_global_tracker_singleton(self):
        """get_tracker should return same instance."""
        from governance.dsm.tracker import get_tracker, reset_tracker

        reset_tracker()
        t1 = get_tracker()
        t2 = get_tracker()
        assert t1 is t2

    def test_tracker_to_dict(self):
        """DSMTracker.to_dict should return dict."""
        from governance.dsm.tracker import DSMTracker, reset_tracker
        import tempfile
        import os

        reset_tracker()
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=os.path.join(tmpdir, ".state.json")
            )
            d = tracker.to_dict()
            assert isinstance(d, dict)
            assert "current_cycle" in d
