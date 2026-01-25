"""
Robot Framework Library for DSMTracker - Cycle & Checkpoint Tests.

Per RULE-012: Deep Sleep Protocol.
Split from DSMTrackerPhasesLibrary.py per DOC-SIZE-01-v1.

Covers: Cycle lifecycle, checkpoints, abort cycle.
"""
import tempfile
from pathlib import Path
from robot.api.deco import keyword


class DSMTrackerCycleLibrary:
    """Library for testing DSMTracker cycle and checkpoint operations."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Cycle Lifecycle Tests
    # =========================================================================

    @keyword("Start Cycle Creates Cycle")
    def start_cycle_creates_cycle(self):
        """start_cycle creates new DSMCycle."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                cycle = tracker.start_cycle("1001-1100")
                return {
                    "not_none": cycle is not None,
                    "has_dsm_prefix": "DSM-" in cycle.cycle_id,
                    "batch_correct": cycle.batch_id == "1001-1100",
                    "phase_idle": cycle.current_phase == "idle"
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Start Cycle Sets Start Time")
    def start_cycle_sets_start_time(self):
        """start_cycle sets start_time."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                cycle = tracker.start_cycle()
                return {"has_start_time": cycle.start_time is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Start Cycle While In Progress Raises")
    def start_cycle_while_in_progress_raises(self):
        """start_cycle while cycle in progress raises ValueError."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                try:
                    tracker.start_cycle()
                    return {"raises": False}
                except ValueError as e:
                    return {"raises": True, "message_correct": "already in progress" in str(e)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Complete Cycle Sets End Time")
    def complete_cycle_sets_end_time(self):
        """complete_cycle sets end_time."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.advance_phase()  # AUDIT
                tracker.complete_cycle()
                return {
                    "has_completed": len(tracker.completed_cycles) == 1,
                    "has_end_time": tracker.completed_cycles[0].end_time is not None
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Complete Cycle Clears Current")
    def complete_cycle_clears_current(self):
        """complete_cycle clears current_cycle."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.advance_phase()
                tracker.complete_cycle()
                return {"cleared": tracker.current_cycle is None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Complete Cycle Generates Evidence File")
    def complete_cycle_generates_evidence_file(self):
        """complete_cycle generates markdown evidence file."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle("TEST-BATCH")
                tracker.advance_phase()
                evidence_path = tracker.complete_cycle()
                return {
                    "exists": Path(evidence_path).exists(),
                    "is_md": evidence_path.endswith(".md")
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Checkpoint Tests
    # =========================================================================

    @keyword("Checkpoint Creates Checkpoint")
    def checkpoint_creates_checkpoint(self):
        """checkpoint creates PhaseCheckpoint."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.advance_phase()  # AUDIT
                cp = tracker.checkpoint("Audited 5 modules")
                return {
                    "phase_audit": cp.phase == "audit",
                    "description_correct": cp.description == "Audited 5 modules",
                    "added_to_list": len(tracker.current_cycle.checkpoints) == 1
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Checkpoint With Metrics")
    def checkpoint_with_metrics(self):
        """checkpoint accepts metrics."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.advance_phase()
                cp = tracker.checkpoint("Measured performance", metrics={"latency_ms": 15})
                return {"has_metrics": cp.metrics.get("latency_ms") == 15}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Checkpoint With Evidence")
    def checkpoint_with_evidence(self):
        """checkpoint accepts evidence references."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.advance_phase()
                cp = tracker.checkpoint("Generated report", evidence=["report.md", "metrics.json"])
                return {"evidence_count": len(cp.evidence) == 2}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Checkpoint No Cycle Raises")
    def checkpoint_no_cycle_raises(self):
        """checkpoint without cycle raises ValueError."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                try:
                    tracker.checkpoint("Test")
                    return {"raises": False}
                except ValueError as e:
                    return {"raises": True, "message_correct": "No cycle in progress" in str(e)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Abort Cycle Tests
    # =========================================================================

    @keyword("Abort Cycle Clears Current")
    def abort_cycle_clears_current(self):
        """abort_cycle clears current_cycle."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.abort_cycle("Test abort")
                return {"cleared": tracker.current_cycle is None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Abort Cycle Without Cycle Is Safe")
    def abort_cycle_without_cycle_is_safe(self):
        """abort_cycle without cycle does nothing."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.abort_cycle()  # Should not raise
                return {"no_error": True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
