"""
Robot Framework Library for DSM Tracker State Persistence Tests.

Per: RULE-012 (DSP), DOC-SIZE-01-v1.
Split from tests/test_dsm_tracker_integration.py
"""
import json
import tempfile
from pathlib import Path
from robot.api.deco import keyword


class DSMTrackerIntegrationStateLibrary:
    """Library for DSM Tracker state persistence tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # State Persistence Tests
    # =========================================================================

    @keyword("State Saved On Start Cycle")
    def state_saved_on_start_cycle(self):
        """State file created on start_cycle."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                state_file = Path(tmpdir) / ".dsm_state.json"
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(state_file)
                )

                tracker.start_cycle("TEST")

                if not state_file.exists():
                    return {"state_created": False}

                with open(state_file) as f:
                    state = json.load(f)

                return {
                    "state_created": True,
                    "batch_id_correct": state["current_cycle"]["batch_id"] == "TEST"
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("State Saved On Advance Phase")
    def state_saved_on_advance_phase(self):
        """State updated on advance_phase."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                state_file = Path(tmpdir) / ".dsm_state.json"
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(state_file)
                )

                tracker.start_cycle()
                tracker.advance_phase()

                with open(state_file) as f:
                    state = json.load(f)

                return {
                    "phase_updated": state["current_cycle"]["current_phase"] == "audit"
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("State Saved On Checkpoint")
    def state_saved_on_checkpoint(self):
        """State updated on checkpoint."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                state_file = Path(tmpdir) / ".dsm_state.json"
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(state_file)
                )

                tracker.start_cycle()
                tracker.advance_phase()
                tracker.checkpoint("Test checkpoint")

                with open(state_file) as f:
                    state = json.load(f)

                return {
                    "checkpoint_saved": len(state["current_cycle"]["checkpoints"]) == 1
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("State Loaded On Init")
    def state_loaded_on_init(self):
        """State loaded from file on init."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                state_file = Path(tmpdir) / ".dsm_state.json"

                # Create first tracker and start cycle
                tracker1 = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(state_file)
                )
                tracker1.start_cycle("PERSIST-TEST")
                tracker1.advance_phase()
                cycle_id = tracker1.current_cycle.cycle_id

                # Create second tracker - should load state
                tracker2 = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(state_file)
                )

                return {
                    "cycle_loaded": tracker2.current_cycle is not None,
                    "cycle_id_matches": tracker2.current_cycle.cycle_id == cycle_id if tracker2.current_cycle else False,
                    "batch_id_matches": tracker2.current_cycle.batch_id == "PERSIST-TEST" if tracker2.current_cycle else False
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("State Cleared On Complete")
    def state_cleared_on_complete(self):
        """State cleared on complete_cycle."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                state_file = Path(tmpdir) / ".dsm_state.json"
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(state_file)
                )

                tracker.start_cycle()
                tracker.advance_phase()
                tracker.complete_cycle()

                with open(state_file) as f:
                    state = json.load(f)

                return {
                    "state_cleared": state["current_cycle"] is None
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
