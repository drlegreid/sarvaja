"""
Robot Framework Library for DSMTracker - Phase Navigation Tests.

Per RULE-012: Deep Sleep Protocol.
Split from DSMTrackerPhasesLibrary.py per DOC-SIZE-01-v1.

Covers: Phase navigation, sequence traversal, phase transitions.
"""
import tempfile
from pathlib import Path
from robot.api.deco import keyword


class DSMTrackerPhaseNavLibrary:
    """Library for testing DSMTracker phase navigation."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Phase Navigation Tests
    # =========================================================================

    @keyword("Next Phase From Idle Returns Audit")
    def next_phase_from_idle_returns_audit(self):
        """next_phase from IDLE returns AUDIT."""
        try:
            from governance.dsm_tracker import DSPPhase
            phase = DSPPhase.IDLE
            next_phase = phase.next_phase()
            return {"is_audit": next_phase == DSPPhase.AUDIT}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Next Phase Through Sequence")
    def next_phase_through_sequence(self):
        """next_phase follows correct sequence."""
        try:
            from governance.dsm_tracker import DSPPhase
            sequence = [
                (DSPPhase.AUDIT, DSPPhase.HYPOTHESIZE),
                (DSPPhase.HYPOTHESIZE, DSPPhase.MEASURE),
                (DSPPhase.MEASURE, DSPPhase.OPTIMIZE),
                (DSPPhase.OPTIMIZE, DSPPhase.VALIDATE),
                (DSPPhase.VALIDATE, DSPPhase.DREAM),
                (DSPPhase.DREAM, DSPPhase.REPORT),
                (DSPPhase.REPORT, DSPPhase.COMPLETE),
            ]
            all_correct = all(current.next_phase() == expected_next
                             for current, expected_next in sequence)
            return {"all_correct": all_correct}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Next Phase From Complete Is None")
    def next_phase_from_complete_is_none(self):
        """next_phase from COMPLETE returns None."""
        try:
            from governance.dsm_tracker import DSPPhase
            return {"is_none": DSPPhase.COMPLETE.next_phase() is None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Prev Phase From Audit Returns Idle")
    def prev_phase_from_audit_returns_idle(self):
        """prev_phase from AUDIT returns IDLE."""
        try:
            from governance.dsm_tracker import DSPPhase
            return {"is_idle": DSPPhase.AUDIT.prev_phase() == DSPPhase.IDLE}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Prev Phase Through Sequence")
    def prev_phase_through_sequence(self):
        """prev_phase follows correct sequence."""
        try:
            from governance.dsm_tracker import DSPPhase
            sequence = [
                (DSPPhase.HYPOTHESIZE, DSPPhase.AUDIT),
                (DSPPhase.MEASURE, DSPPhase.HYPOTHESIZE),
                (DSPPhase.OPTIMIZE, DSPPhase.MEASURE),
                (DSPPhase.VALIDATE, DSPPhase.OPTIMIZE),
                (DSPPhase.DREAM, DSPPhase.VALIDATE),
                (DSPPhase.REPORT, DSPPhase.DREAM),
                (DSPPhase.COMPLETE, DSPPhase.REPORT),
            ]
            all_correct = all(current.prev_phase() == expected_prev
                             for current, expected_prev in sequence)
            return {"all_correct": all_correct}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Phase Transition Tests
    # =========================================================================

    @keyword("Advance Phase From Idle To Audit")
    def advance_phase_from_idle_to_audit(self):
        """advance_phase from IDLE goes to AUDIT."""
        try:
            from governance.dsm_tracker import DSMTracker, DSPPhase
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                new_phase = tracker.advance_phase()
                return {
                    "is_audit": new_phase == DSPPhase.AUDIT,
                    "current_audit": tracker.current_cycle.current_phase == "audit"
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Advance Phase Records Completed")
    def advance_phase_records_completed(self):
        """advance_phase records completed phases."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.checkpoint("Audit checkpoint")
                tracker.advance_phase()  # AUDIT
                tracker.checkpoint("Hypothesize checkpoint")
                tracker.advance_phase()  # HYPOTHESIZE
                return {"audit_completed": "audit" in tracker.current_cycle.phases_completed}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Advance Phase No Cycle Raises")
    def advance_phase_no_cycle_raises(self):
        """advance_phase without cycle raises ValueError."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                try:
                    tracker.advance_phase()
                    return {"raises": False}
                except ValueError as e:
                    return {"raises": True, "message_correct": "No cycle in progress" in str(e)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Go To Phase Jumps Directly")
    def go_to_phase_jumps_directly(self):
        """go_to_phase jumps to specific phase."""
        try:
            from governance.dsm_tracker import DSMTracker, DSPPhase
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.go_to_phase(DSPPhase.VALIDATE)
                return {"is_validate": tracker.current_cycle.current_phase == "validate"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Go To Phase Idle Raises")
    def go_to_phase_idle_raises(self):
        """go_to_phase with IDLE raises ValueError."""
        try:
            from governance.dsm_tracker import DSMTracker, DSPPhase
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                try:
                    tracker.go_to_phase(DSPPhase.IDLE)
                    return {"raises": False}
                except ValueError as e:
                    return {"raises": True, "message_correct": "Cannot jump to idle" in str(e)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
