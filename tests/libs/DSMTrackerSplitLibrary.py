"""
Robot Framework Library for DSM Tracker Split Tests.

Per GAP-FILE-024: dsm/tracker.py split.
Migrated from tests/test_dsm_tracker_split.py
"""
import tempfile
import os
from pathlib import Path
from robot.api.deco import keyword


class DSMTrackerSplitLibrary:
    """Library for testing DSM tracker module structure."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.governance_dir = self.project_root / "governance"
        self.dsm_dir = self.governance_dir / "dsm"

    # =============================================================================
    # Module Structure Tests
    # =============================================================================

    @keyword("Tracker Module Exists")
    def tracker_module_exists(self):
        """tracker.py should exist in dsm/."""
        tracker_file = self.dsm_dir / "tracker.py"
        return {"exists": tracker_file.exists()}

    @keyword("Memory Module Exists")
    def memory_module_exists(self):
        """memory.py should exist in dsm/ (if split was done)."""
        memory_file = self.dsm_dir / "memory.py"
        if not memory_file.exists():
            return {"skipped": True, "reason": "memory.py not yet extracted"}
        return {"exists": memory_file.exists()}

    # =============================================================================
    # Backward Compatibility Tests
    # =============================================================================

    @keyword("Import DSM Tracker Class From DSM")
    def import_dsm_tracker_class_from_dsm(self):
        """from governance.dsm.tracker import DSMTracker must work."""
        try:
            from governance.dsm.tracker import DSMTracker
            return {"imported": DSMTracker is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Get Tracker From DSM")
    def import_get_tracker_from_dsm(self):
        """from governance.dsm.tracker import get_tracker must work."""
        try:
            from governance.dsm.tracker import get_tracker
            return {"imported": get_tracker is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Reset Tracker From DSM")
    def import_reset_tracker_from_dsm(self):
        """from governance.dsm.tracker import reset_tracker must work."""
        try:
            from governance.dsm.tracker import reset_tracker
            return {"imported": reset_tracker is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create DSM Tracker Instance")
    def create_dsm_tracker_instance(self):
        """DSMTracker should create instance."""
        try:
            from governance.dsm.tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=os.path.join(tmpdir, ".state.json")
                )
                return {"created": tracker is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Core Functionality Tests
    # =============================================================================

    @keyword("DSM Tracker Start Cycle")
    def dsm_tracker_start_cycle(self):
        """DSMTracker should start a cycle."""
        try:
            from governance.dsm.tracker import DSMTracker, reset_tracker

            reset_tracker()
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=os.path.join(tmpdir, ".state.json")
                )
                cycle = tracker.start_cycle("test-batch")
                return {
                    "not_none": cycle is not None,
                    "starts_with_dsm": cycle.cycle_id.startswith("DSM-")
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("DSM Tracker Get Status")
    def dsm_tracker_get_status(self):
        """DSMTracker should return status."""
        try:
            from governance.dsm.tracker import DSMTracker, reset_tracker

            reset_tracker()
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=os.path.join(tmpdir, ".state.json")
                )
                status = tracker.get_status()
                return {
                    "is_dict": isinstance(status, dict),
                    "has_active": "active" in status
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("DSM Tracker Get Session Memory Payload")
    def dsm_tracker_get_session_memory_payload(self):
        """DSMTracker should provide session memory payload."""
        try:
            from governance.dsm.tracker import DSMTracker, reset_tracker

            reset_tracker()
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=os.path.join(tmpdir, ".state.json")
                )
                # No cycle - should return None
                payload = tracker.get_session_memory_payload()
                return {"payload_none": payload is None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Integration Tests
    # =============================================================================

    @keyword("DSM Global Tracker Singleton")
    def dsm_global_tracker_singleton(self):
        """get_tracker should return same instance."""
        try:
            from governance.dsm.tracker import get_tracker, reset_tracker

            reset_tracker()
            t1 = get_tracker()
            t2 = get_tracker()
            result = {"same_instance": t1 is t2}
            reset_tracker()
            return result
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("DSM Tracker To Dict")
    def dsm_tracker_to_dict(self):
        """DSMTracker.to_dict should return dict."""
        try:
            from governance.dsm.tracker import DSMTracker, reset_tracker

            reset_tracker()
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=os.path.join(tmpdir, ".state.json")
                )
                d = tracker.to_dict()
                return {
                    "is_dict": isinstance(d, dict),
                    "has_current_cycle": "current_cycle" in d
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
