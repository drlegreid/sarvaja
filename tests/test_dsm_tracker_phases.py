"""
Phase Transition Tests for DSMTracker

Tests:
- Phase navigation (next/prev)
- Cycle lifecycle (start, advance, complete)
- Phase transitions
- Checkpoints and findings
- Evidence generation

Per: RULE-004 (Exploratory Testing), RULE-012 (DSP)
"""

import pytest
import json
import tempfile
from pathlib import Path


class TestPhaseNavigation:
    """Tests for phase navigation methods."""

    def test_next_phase_from_idle(self):
        """next_phase from IDLE returns AUDIT."""
        from governance.dsm_tracker import DSPPhase

        phase = DSPPhase.IDLE
        next_phase = phase.next_phase()

        assert next_phase == DSPPhase.AUDIT

    def test_next_phase_through_sequence(self):
        """next_phase follows correct sequence."""
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

        for current, expected_next in sequence:
            assert current.next_phase() == expected_next

    def test_next_phase_from_complete_is_none(self):
        """next_phase from COMPLETE returns None."""
        from governance.dsm_tracker import DSPPhase

        assert DSPPhase.COMPLETE.next_phase() is None

    def test_prev_phase_from_audit(self):
        """prev_phase from AUDIT returns IDLE."""
        from governance.dsm_tracker import DSPPhase

        assert DSPPhase.AUDIT.prev_phase() == DSPPhase.IDLE

    def test_prev_phase_through_sequence(self):
        """prev_phase follows correct sequence."""
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

        for current, expected_prev in sequence:
            assert current.prev_phase() == expected_prev


class TestCycleLifecycle:
    """Tests for cycle start/complete lifecycle."""

    def test_start_cycle_creates_cycle(self):
        """start_cycle creates new DSMCycle."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            cycle = tracker.start_cycle("1001-1100")

            assert cycle is not None
            assert "DSM-" in cycle.cycle_id
            assert cycle.batch_id == "1001-1100"
            assert cycle.current_phase == "idle"

    def test_start_cycle_sets_start_time(self):
        """start_cycle sets start_time."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            cycle = tracker.start_cycle()

            assert cycle.start_time is not None

    def test_start_cycle_while_in_progress_raises(self):
        """start_cycle while cycle in progress raises ValueError."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()

            with pytest.raises(ValueError, match="already in progress"):
                tracker.start_cycle()

    def test_complete_cycle_sets_end_time(self):
        """complete_cycle sets end_time."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.advance_phase()  # AUDIT
            tracker.complete_cycle()

            # Cycle is now archived, check completed_cycles
            assert len(tracker.completed_cycles) == 1
            assert tracker.completed_cycles[0].end_time is not None

    def test_complete_cycle_clears_current(self):
        """complete_cycle clears current_cycle."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.advance_phase()
            tracker.complete_cycle()

            assert tracker.current_cycle is None

    def test_complete_cycle_generates_evidence_file(self):
        """complete_cycle generates markdown evidence file."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle("TEST-BATCH")
            tracker.advance_phase()
            evidence_path = tracker.complete_cycle()

            assert Path(evidence_path).exists()
            assert evidence_path.endswith(".md")


class TestPhaseTransitions:
    """Tests for phase transitions."""

    def test_advance_phase_from_idle_to_audit(self):
        """advance_phase from IDLE goes to AUDIT."""
        from governance.dsm_tracker import DSMTracker, DSPPhase

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            new_phase = tracker.advance_phase()

            assert new_phase == DSPPhase.AUDIT
            assert tracker.current_cycle.current_phase == "audit"

    def test_advance_phase_records_completed(self):
        """advance_phase records completed phases."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.advance_phase()  # AUDIT
            tracker.advance_phase()  # HYPOTHESIZE

            assert "audit" in tracker.current_cycle.phases_completed

    def test_advance_phase_through_full_cycle(self):
        """advance_phase through all phases."""
        from governance.dsm_tracker import DSMTracker, DSPPhase

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()

            expected_phases = [
                DSPPhase.AUDIT,
                DSPPhase.HYPOTHESIZE,
                DSPPhase.MEASURE,
                DSPPhase.OPTIMIZE,
                DSPPhase.VALIDATE,
                DSPPhase.DREAM,
                DSPPhase.REPORT,
                DSPPhase.COMPLETE
            ]

            for expected in expected_phases:
                phase = tracker.advance_phase()
                assert phase == expected

    def test_advance_phase_no_cycle_raises(self):
        """advance_phase without cycle raises ValueError."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            with pytest.raises(ValueError, match="No cycle in progress"):
                tracker.advance_phase()

    def test_go_to_phase_jumps_directly(self):
        """go_to_phase jumps to specific phase."""
        from governance.dsm_tracker import DSMTracker, DSPPhase

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.go_to_phase(DSPPhase.VALIDATE)

            assert tracker.current_cycle.current_phase == "validate"

    def test_go_to_phase_idle_raises(self):
        """go_to_phase with IDLE raises ValueError."""
        from governance.dsm_tracker import DSMTracker, DSPPhase

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()

            with pytest.raises(ValueError, match="Cannot jump to idle"):
                tracker.go_to_phase(DSPPhase.IDLE)


class TestCheckpoints:
    """Tests for checkpoint creation."""

    def test_checkpoint_creates_checkpoint(self):
        """checkpoint creates PhaseCheckpoint."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.advance_phase()  # AUDIT

            cp = tracker.checkpoint("Audited 5 modules")

            assert cp.phase == "audit"
            assert cp.description == "Audited 5 modules"
            assert len(tracker.current_cycle.checkpoints) == 1

    def test_checkpoint_with_metrics(self):
        """checkpoint accepts metrics."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.advance_phase()

            cp = tracker.checkpoint(
                "Measured performance",
                metrics={"latency_ms": 15}
            )

            assert cp.metrics["latency_ms"] == 15

    def test_checkpoint_with_evidence(self):
        """checkpoint accepts evidence references."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.advance_phase()

            cp = tracker.checkpoint(
                "Generated report",
                evidence=["report.md", "metrics.json"]
            )

            assert len(cp.evidence) == 2

    def test_checkpoint_no_cycle_raises(self):
        """checkpoint without cycle raises ValueError."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            with pytest.raises(ValueError, match="No cycle in progress"):
                tracker.checkpoint("Test")


class TestFindings:
    """Tests for finding creation."""

    def test_add_finding_creates_finding(self):
        """add_finding creates finding dict."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.advance_phase()

            finding = tracker.add_finding(
                finding_type="gap",
                description="Missing test coverage"
            )

            assert finding["type"] == "gap"
            assert finding["description"] == "Missing test coverage"
            assert len(tracker.current_cycle.findings) == 1

    def test_add_finding_assigns_id(self):
        """add_finding assigns sequential ID."""
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

            assert f1["id"] == "FINDING-001"
            assert f2["id"] == "FINDING-002"

    def test_add_finding_with_severity(self):
        """add_finding accepts severity."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.advance_phase()

            finding = tracker.add_finding(
                "conflict",
                "Critical conflict",
                severity="CRITICAL"
            )

            assert finding["severity"] == "CRITICAL"

    def test_add_finding_with_related_rules(self):
        """add_finding accepts related rules."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.advance_phase()

            finding = tracker.add_finding(
                "improvement",
                "Enhance RULE-001",
                related_rules=["RULE-001", "RULE-012"]
            )

            assert "RULE-001" in finding["related_rules"]
            assert "RULE-012" in finding["related_rules"]


class TestAbortCycle:
    """Tests for cycle abort."""

    def test_abort_cycle_clears_current(self):
        """abort_cycle clears current_cycle."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.abort_cycle("Test abort")

            assert tracker.current_cycle is None

    def test_abort_cycle_without_cycle_is_safe(self):
        """abort_cycle without cycle does nothing."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            # Should not raise
            tracker.abort_cycle()


class TestStatus:
    """Tests for status reporting."""

    def test_get_status_when_idle(self):
        """get_status when no cycle."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            status = tracker.get_status()

            assert status["active"] is False
            assert "No cycle in progress" in status["message"]

    def test_get_status_when_active(self):
        """get_status when cycle active."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle("TEST")
            tracker.advance_phase()
            tracker.advance_phase()

            status = tracker.get_status()

            assert status["active"] is True
            assert status["batch_id"] == "TEST"
            assert status["current_phase"] == "hypothesize"
            assert "1/7" in status["progress"]

    def test_get_status_includes_required_mcps(self):
        """get_status includes required MCPs for current phase."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.advance_phase()  # AUDIT

            status = tracker.get_status()

            assert "claude-mem" in status["required_mcps"]
            assert "governance" in status["required_mcps"]
