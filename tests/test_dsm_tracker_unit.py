"""
Unit Tests for DSMTracker - Core Classes and Data Structures

Tests:
- DSPPhase enum
- PhaseCheckpoint dataclass
- DSMCycle dataclass
- DSMTracker initialization

Per: RULE-004 (Exploratory Testing), RULE-012 (DSP)
"""

import pytest
import json
import tempfile
from pathlib import Path


class TestDSPPhaseEnum:
    """Tests for DSPPhase enumeration."""

    def test_dsp_phase_enum_exists(self):
        """DSPPhase enum exists and is importable."""
        from governance.dsm_tracker import DSPPhase
        assert DSPPhase is not None

    def test_dsp_phase_has_all_phases(self):
        """DSPPhase has all expected phases."""
        from governance.dsm_tracker import DSPPhase

        expected = ["idle", "audit", "hypothesize", "measure",
                    "optimize", "validate", "dream", "report", "complete"]

        for phase_name in expected:
            assert DSPPhase(phase_name) is not None

    def test_dsp_phase_values(self):
        """DSPPhase values are lowercase strings."""
        from governance.dsm_tracker import DSPPhase

        assert DSPPhase.IDLE.value == "idle"
        assert DSPPhase.AUDIT.value == "audit"
        assert DSPPhase.HYPOTHESIZE.value == "hypothesize"
        assert DSPPhase.MEASURE.value == "measure"
        assert DSPPhase.OPTIMIZE.value == "optimize"
        assert DSPPhase.VALIDATE.value == "validate"
        assert DSPPhase.DREAM.value == "dream"
        assert DSPPhase.REPORT.value == "report"
        assert DSPPhase.COMPLETE.value == "complete"

    def test_phase_order_returns_list(self):
        """phase_order returns list of phases."""
        from governance.dsm_tracker import DSPPhase

        order = DSPPhase.phase_order()

        assert isinstance(order, list)
        assert len(order) == 7
        assert DSPPhase.IDLE not in order
        assert DSPPhase.COMPLETE not in order

    def test_phase_order_is_correct_sequence(self):
        """phase_order is in correct sequence."""
        from governance.dsm_tracker import DSPPhase

        order = DSPPhase.phase_order()

        assert order[0] == DSPPhase.AUDIT
        assert order[1] == DSPPhase.HYPOTHESIZE
        assert order[2] == DSPPhase.MEASURE
        assert order[3] == DSPPhase.OPTIMIZE
        assert order[4] == DSPPhase.VALIDATE
        assert order[5] == DSPPhase.DREAM
        assert order[6] == DSPPhase.REPORT


class TestDSPPhaseRequiredMCPs:
    """Tests for phase-specific MCP requirements."""

    def test_audit_requires_claude_mem_and_governance(self):
        """AUDIT phase requires claude-mem and governance MCPs."""
        from governance.dsm_tracker import DSPPhase

        mcps = DSPPhase.AUDIT.required_mcps

        assert "claude-mem" in mcps
        assert "governance" in mcps

    def test_hypothesize_requires_sequential_thinking(self):
        """HYPOTHESIZE phase requires sequential-thinking MCP."""
        from governance.dsm_tracker import DSPPhase

        mcps = DSPPhase.HYPOTHESIZE.required_mcps

        assert "sequential-thinking" in mcps

    def test_measure_requires_powershell_and_sandbox(self):
        """MEASURE phase requires powershell and llm-sandbox MCPs."""
        from governance.dsm_tracker import DSPPhase

        mcps = DSPPhase.MEASURE.required_mcps

        assert "powershell" in mcps
        assert "llm-sandbox" in mcps

    def test_validate_requires_pytest(self):
        """VALIDATE phase requires pytest MCP."""
        from governance.dsm_tracker import DSPPhase

        mcps = DSPPhase.VALIDATE.required_mcps

        assert "pytest" in mcps

    def test_idle_has_no_required_mcps(self):
        """IDLE phase has no required MCPs."""
        from governance.dsm_tracker import DSPPhase

        mcps = DSPPhase.IDLE.required_mcps

        assert mcps == []


class TestPhaseCheckpointDataclass:
    """Tests for PhaseCheckpoint dataclass."""

    def test_checkpoint_creation(self):
        """PhaseCheckpoint creates with required fields."""
        from governance.dsm_tracker import PhaseCheckpoint

        cp = PhaseCheckpoint(
            phase="audit",
            timestamp="2024-12-24T12:00:00",
            description="Audited 5 modules"
        )

        assert cp.phase == "audit"
        assert cp.timestamp == "2024-12-24T12:00:00"
        assert cp.description == "Audited 5 modules"

    def test_checkpoint_has_default_metrics(self):
        """PhaseCheckpoint has default empty metrics."""
        from governance.dsm_tracker import PhaseCheckpoint

        cp = PhaseCheckpoint(
            phase="audit",
            timestamp="2024-12-24T12:00:00",
            description="Test"
        )

        assert cp.metrics == {}

    def test_checkpoint_has_default_evidence(self):
        """PhaseCheckpoint has default empty evidence list."""
        from governance.dsm_tracker import PhaseCheckpoint

        cp = PhaseCheckpoint(
            phase="audit",
            timestamp="2024-12-24T12:00:00",
            description="Test"
        )

        assert cp.evidence == []

    def test_checkpoint_with_metrics_and_evidence(self):
        """PhaseCheckpoint accepts metrics and evidence."""
        from governance.dsm_tracker import PhaseCheckpoint

        cp = PhaseCheckpoint(
            phase="measure",
            timestamp="2024-12-24T12:00:00",
            description="Measured performance",
            metrics={"latency_ms": 15, "throughput": 100},
            evidence=["benchmark.log", "perf_report.md"]
        )

        assert cp.metrics["latency_ms"] == 15
        assert len(cp.evidence) == 2


class TestDSMCycleDataclass:
    """Tests for DSMCycle dataclass."""

    def test_cycle_creation(self):
        """DSMCycle creates with cycle_id."""
        from governance.dsm_tracker import DSMCycle

        cycle = DSMCycle(cycle_id="DSM-2024-12-24-120000")

        assert cycle.cycle_id == "DSM-2024-12-24-120000"
        assert cycle.current_phase == "idle"

    def test_cycle_has_default_empty_lists(self):
        """DSMCycle has default empty lists."""
        from governance.dsm_tracker import DSMCycle

        cycle = DSMCycle(cycle_id="TEST-001")

        assert cycle.phases_completed == []
        assert cycle.checkpoints == []
        assert cycle.findings == []

    def test_cycle_to_dict(self):
        """DSMCycle converts to dictionary."""
        from governance.dsm_tracker import DSMCycle

        cycle = DSMCycle(
            cycle_id="TEST-001",
            batch_id="1001-1100",
            current_phase="audit"
        )

        d = cycle.to_dict()

        assert d["cycle_id"] == "TEST-001"
        assert d["batch_id"] == "1001-1100"
        assert d["current_phase"] == "audit"
        assert isinstance(d["checkpoints"], list)


class TestDSMTrackerInitialization:
    """Tests for DSMTracker initialization."""

    def test_tracker_class_exists(self):
        """DSMTracker class exists and is importable."""
        from governance.dsm_tracker import DSMTracker
        assert DSMTracker is not None

    def test_tracker_creates_with_defaults(self):
        """DSMTracker creates with default paths."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            assert tracker.current_cycle is None
            assert tracker.completed_cycles == []

    def test_tracker_uses_custom_evidence_dir(self):
        """DSMTracker uses custom evidence directory."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "custom_evidence"
            tracker = DSMTracker(evidence_dir=str(custom_dir))

            assert tracker.evidence_dir == custom_dir

    def test_tracker_starts_with_no_active_cycle(self):
        """DSMTracker starts with no active cycle."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            assert tracker.current_cycle is None
            status = tracker.get_status()
            assert status["active"] is False


class TestDSMTrackerSerialization:
    """Tests for DSMTracker serialization."""

    def test_to_dict_returns_dict(self):
        """to_dict returns dictionary."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            d = tracker.to_dict()

            assert isinstance(d, dict)
            assert "current_cycle" in d
            assert "completed_cycles_count" in d

    def test_to_json_returns_valid_json(self):
        """to_json returns valid JSON string."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            json_str = tracker.to_json()
            parsed = json.loads(json_str)

            assert parsed["current_cycle"] is None


class TestGlobalTrackerFunctions:
    """Tests for global tracker functions."""

    def test_get_tracker_returns_tracker(self):
        """get_tracker returns DSMTracker instance."""
        from governance.dsm_tracker import get_tracker, reset_tracker, DSMTracker

        reset_tracker()  # Ensure clean state

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = get_tracker(evidence_dir=tmpdir)
            assert isinstance(tracker, DSMTracker)

        reset_tracker()

    def test_get_tracker_returns_same_instance(self):
        """get_tracker returns same instance on multiple calls."""
        from governance.dsm_tracker import get_tracker, reset_tracker

        reset_tracker()

        tracker1 = get_tracker()
        tracker2 = get_tracker()

        assert tracker1 is tracker2

        reset_tracker()

    def test_reset_tracker_clears_instance(self):
        """reset_tracker clears global instance."""
        from governance.dsm_tracker import get_tracker, reset_tracker

        reset_tracker()
        tracker1 = get_tracker()

        reset_tracker()
        tracker2 = get_tracker()

        assert tracker1 is not tracker2

        reset_tracker()
