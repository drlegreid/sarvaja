"""
Robot Framework Library for DSM Tracker Workflow Tests.

Per: RULE-012 (DSP), DOC-SIZE-01-v1.
Split from tests/test_dsm_tracker_integration.py
"""
import tempfile
from pathlib import Path
from robot.api.deco import keyword


class DSMTrackerIntegrationWorkflowLibrary:
    """Library for DSM Tracker full cycle workflow tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # Full Cycle Workflow Tests
    # =========================================================================

    @keyword("Full Cycle Workflow")
    def full_cycle_workflow(self):
        """Full DSP cycle from start to complete."""
        try:
            from governance.dsm_tracker import DSMTracker, DSPPhase

            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )

                results = {}

                # Start
                tracker.start_cycle("FULL-CYCLE-TEST")
                results["start_idle"] = tracker.get_current_phase() == DSPPhase.IDLE

                # AUDIT
                tracker.advance_phase()
                results["advance_audit"] = tracker.get_current_phase() == DSPPhase.AUDIT
                tracker.add_finding("gap", "Missing tests for integration coverage")
                tracker.checkpoint("Audit complete with gaps identified for resolution")

                # HYPOTHESIZE
                tracker.advance_phase()
                results["advance_hypothesize"] = tracker.get_current_phase() == DSPPhase.HYPOTHESIZE
                tracker.checkpoint("Hypothesis formed and documented for testing purposes")

                # MEASURE
                tracker.advance_phase()
                results["advance_measure"] = tracker.get_current_phase() == DSPPhase.MEASURE
                tracker.update_metrics({"baseline_coverage": 75})
                tracker.checkpoint("Baseline metrics collected for coverage analysis", metrics={"baseline_coverage": 75})

                # OPTIMIZE
                tracker.advance_phase()
                results["advance_optimize"] = tracker.get_current_phase() == DSPPhase.OPTIMIZE
                tracker.checkpoint("Optimizations applied for improved test coverage")

                # VALIDATE
                tracker.advance_phase()
                results["advance_validate"] = tracker.get_current_phase() == DSPPhase.VALIDATE
                tracker.update_metrics({"new_coverage": 85})
                tracker.checkpoint("Validation completed with improved coverage metrics")

                # DREAM
                tracker.advance_phase()
                results["advance_dream"] = tracker.get_current_phase() == DSPPhase.DREAM
                tracker.add_finding("improvement", "Consider new pattern for better test isolation")

                # REPORT
                tracker.advance_phase()
                results["advance_report"] = tracker.get_current_phase() == DSPPhase.REPORT

                # COMPLETE
                evidence_path = tracker.complete_cycle()

                # Verify
                results["evidence_exists"] = Path(evidence_path).exists()
                results["completed_count"] = len(tracker.completed_cycles) == 1
                results["cycle_cleared"] = tracker.current_cycle is None

                return results
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Resume Interrupted Cycle")
    def resume_interrupted_cycle(self):
        """Resume cycle after interruption."""
        try:
            from governance.dsm_tracker import DSMTracker, DSPPhase

            with tempfile.TemporaryDirectory() as tmpdir:
                state_file = Path(tmpdir) / ".dsm_state.json"

                # Start cycle and advance
                tracker1 = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(state_file)
                )
                tracker1.start_cycle("RESUME-TEST")
                tracker1.advance_phase()  # AUDIT
                tracker1.checkpoint("Audit checkpoint for testing")  # Required before advancing
                tracker1.advance_phase()  # HYPOTHESIZE
                tracker1.checkpoint("Hypothesis checkpoint before simulated interruption")

                # Simulate interruption - create new tracker
                tracker2 = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(state_file)
                )

                results = {
                    "cycle_resumed": tracker2.current_cycle is not None,
                    "phase_correct": tracker2.get_current_phase() == DSPPhase.HYPOTHESIZE if tracker2.current_cycle else False,
                    "checkpoints_preserved": len(tracker2.current_cycle.checkpoints) == 2 if tracker2.current_cycle else False
                }

                # Can continue
                if tracker2.current_cycle:
                    tracker2.advance_phase()  # MEASURE
                    results["can_continue"] = tracker2.get_current_phase() == DSPPhase.MEASURE

                return results
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Metrics Update Tests
    # =========================================================================

    @keyword("Update Metrics Adds To Cycle")
    def update_metrics_adds_to_cycle(self):
        """update_metrics adds metrics to cycle."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )

                tracker.start_cycle()
                tracker.advance_phase()
                tracker.update_metrics({"tests": 100, "coverage": 80})

                return {
                    "tests_added": tracker.current_cycle.metrics["tests"] == 100,
                    "coverage_added": tracker.current_cycle.metrics["coverage"] == 80
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Update Metrics Merges With Existing")
    def update_metrics_merges_with_existing(self):
        """update_metrics merges with existing metrics."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )

                tracker.start_cycle()
                tracker.advance_phase()
                tracker.update_metrics({"tests": 100})
                tracker.update_metrics({"coverage": 80})

                return {
                    "tests_preserved": tracker.current_cycle.metrics["tests"] == 100,
                    "coverage_merged": tracker.current_cycle.metrics["coverage"] == 80
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Update Metrics No Cycle Raises")
    def update_metrics_no_cycle_raises(self):
        """update_metrics without cycle raises ValueError."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )

                try:
                    tracker.update_metrics({"key": "value"})
                    return {"raises_error": False}
                except ValueError as e:
                    return {"raises_error": True, "error_message_correct": "No cycle in progress" in str(e)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
