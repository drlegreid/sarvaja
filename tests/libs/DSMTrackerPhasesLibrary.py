"""
Robot Framework Library for DSMTracker Phase Transition Tests.

Per RULE-012: Deep Sleep Protocol.
Migrated from tests/test_dsm_tracker_phases.py
"""
import tempfile
from pathlib import Path
from robot.api.deco import keyword


class DSMTrackerPhasesLibrary:
    """Library for testing DSMTracker phase transitions."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # Phase Navigation Tests
    # =============================================================================

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

    # =============================================================================
    # Cycle Lifecycle Tests
    # =============================================================================

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

    # =============================================================================
    # Phase Transition Tests
    # =============================================================================

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

    # =============================================================================
    # Checkpoint Tests
    # =============================================================================

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

    # =============================================================================
    # Finding Tests
    # =============================================================================

    @keyword("Add Finding Creates Finding")
    def add_finding_creates_finding(self):
        """add_finding creates finding dict."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.advance_phase()
                finding = tracker.add_finding(finding_type="gap", description="Missing test coverage")
                return {
                    "type_gap": finding["type"] == "gap",
                    "description_correct": finding["description"] == "Missing test coverage",
                    "added_to_list": len(tracker.current_cycle.findings) == 1
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Add Finding Assigns Sequential Id")
    def add_finding_assigns_sequential_id(self):
        """add_finding assigns sequential ID."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.advance_phase()
                f1 = tracker.add_finding("gap", "Finding 1")
                f2 = tracker.add_finding("orphan", "Finding 2")
                return {
                    "first_id": f1["id"] == "FINDING-001",
                    "second_id": f2["id"] == "FINDING-002"
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Add Finding With Severity")
    def add_finding_with_severity(self):
        """add_finding accepts severity."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.advance_phase()
                finding = tracker.add_finding("conflict", "Critical conflict", severity="CRITICAL")
                return {"severity_correct": finding["severity"] == "CRITICAL"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Add Finding With Related Rules")
    def add_finding_with_related_rules(self):
        """add_finding accepts related rules."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.advance_phase()
                finding = tracker.add_finding("improvement", "Enhance RULE-001", related_rules=["RULE-001", "RULE-012"])
                return {
                    "has_rule_001": "RULE-001" in finding["related_rules"],
                    "has_rule_012": "RULE-012" in finding["related_rules"]
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Abort Cycle Tests
    # =============================================================================

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

    # =============================================================================
    # Status Tests
    # =============================================================================

    @keyword("Get Status When Idle")
    def get_status_when_idle(self):
        """get_status when no cycle."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                status = tracker.get_status()
                return {
                    "not_active": status["active"] is False,
                    "has_message": "No cycle in progress" in status.get("message", "")
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Status When Active")
    def get_status_when_active(self):
        """get_status when cycle active."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle("TEST")
                tracker.checkpoint("Audit checkpoint")
                tracker.advance_phase()  # AUDIT
                tracker.checkpoint("Hypothesize checkpoint")
                tracker.advance_phase()  # HYPOTHESIZE
                status = tracker.get_status()
                return {
                    "is_active": status["active"] is True,
                    "batch_correct": status.get("batch_id") == "TEST",
                    "phase_correct": status.get("current_phase") == "hypothesize",
                    "has_progress": "1/7" in status.get("progress", "")
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Status Includes Required MCPs")
    def get_status_includes_required_mcps(self):
        """get_status includes required MCPs for current phase."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.advance_phase()  # AUDIT
                status = tracker.get_status()
                mcps = status.get("required_mcps", [])
                return {
                    "has_claude_mem": "claude-mem" in mcps,
                    "has_governance": "governance" in mcps
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
