"""
Unit tests for DSM Phase Validation.

Per TASK 3.1: Tests for validate_phase_evidence() and PHASE_REQUIREMENTS.
"""

import pytest

from governance.dsm.validation import (
    validate_phase_evidence,
    PHASE_REQUIREMENTS,
)
from governance.dsm.phases import DSPPhase
from governance.dsm.models import DSMCycle, PhaseCheckpoint


def _make_cycle(checkpoints=None, findings=None):
    """Create a DSMCycle with specified checkpoints and findings."""
    return DSMCycle(
        cycle_id="TEST-001",
        checkpoints=checkpoints or [],
        findings=findings or [],
    )


def _make_checkpoint(phase, description="Valid checkpoint text", metrics=None):
    """Create a PhaseCheckpoint."""
    return PhaseCheckpoint(
        phase=phase,
        timestamp="2026-02-11T10:00:00",
        description=description,
        metrics=metrics or {},
    )


# ---------------------------------------------------------------------------
# PHASE_REQUIREMENTS
# ---------------------------------------------------------------------------
class TestPhaseRequirements:
    """Tests for PHASE_REQUIREMENTS constants."""

    def test_all_phases_have_requirements(self):
        for phase in DSPPhase.phase_order():
            assert phase in PHASE_REQUIREMENTS, f"Missing requirements for {phase}"

    def test_audit_needs_checkpoint_or_finding(self):
        assert PHASE_REQUIREMENTS[DSPPhase.AUDIT]["need_checkpoint_or_finding"] is True

    def test_hypothesize_needs_checkpoint(self):
        assert PHASE_REQUIREMENTS[DSPPhase.HYPOTHESIZE]["need_checkpoint"] is True

    def test_measure_needs_metrics(self):
        assert PHASE_REQUIREMENTS[DSPPhase.MEASURE]["need_checkpoint_with_metrics"] is True

    def test_optimize_needs_checkpoint(self):
        assert PHASE_REQUIREMENTS[DSPPhase.OPTIMIZE]["need_checkpoint"] is True

    def test_report_no_strict_requirements(self):
        assert PHASE_REQUIREMENTS[DSPPhase.REPORT]["need_checkpoint_or_finding"] is False

    def test_all_have_descriptions(self):
        for phase, req in PHASE_REQUIREMENTS.items():
            assert "description" in req


# ---------------------------------------------------------------------------
# validate_phase_evidence — AUDIT phase
# ---------------------------------------------------------------------------
class TestValidateAudit:
    """Tests for AUDIT phase validation."""

    def test_valid_with_checkpoint(self):
        cp = _make_checkpoint("audit", "Found a significant gap in coverage")
        cycle = _make_cycle(checkpoints=[cp])
        assert validate_phase_evidence(cycle, DSPPhase.AUDIT) is None

    def test_valid_with_finding(self):
        finding = {"phase": "audit", "type": "gap", "description": "Missing tests"}
        cycle = _make_cycle(findings=[finding])
        assert validate_phase_evidence(cycle, DSPPhase.AUDIT) is None

    def test_fails_without_evidence(self):
        cycle = _make_cycle()
        result = validate_phase_evidence(cycle, DSPPhase.AUDIT)
        assert result is not None
        assert "AUDIT" in result

    def test_fails_with_short_checkpoint(self):
        cp = _make_checkpoint("audit", "Too short")  # < 20 chars
        cycle = _make_cycle(checkpoints=[cp])
        # "Too short" is 9 chars, min is 20 for AUDIT
        result = validate_phase_evidence(cycle, DSPPhase.AUDIT)
        # With a finding it would pass, without one it depends on checkpoint length
        # AUDIT uses need_checkpoint_or_finding, so needs valid checkpoint OR finding
        assert result is not None


# ---------------------------------------------------------------------------
# validate_phase_evidence — HYPOTHESIZE phase
# ---------------------------------------------------------------------------
class TestValidateHypothesize:
    """Tests for HYPOTHESIZE phase validation."""

    def test_valid_with_sufficient_checkpoint(self):
        cp = _make_checkpoint("hypothesize", "Hypothesis: improving test coverage will reduce defects significantly")
        cycle = _make_cycle(checkpoints=[cp])
        assert validate_phase_evidence(cycle, DSPPhase.HYPOTHESIZE) is None

    def test_fails_with_short_checkpoint(self):
        cp = _make_checkpoint("hypothesize", "Too short for hypothesis")  # < 30 chars
        cycle = _make_cycle(checkpoints=[cp])
        result = validate_phase_evidence(cycle, DSPPhase.HYPOTHESIZE)
        assert result is not None
        assert "HYPOTHESIZE" in result

    def test_fails_without_checkpoint(self):
        cycle = _make_cycle()
        result = validate_phase_evidence(cycle, DSPPhase.HYPOTHESIZE)
        assert result is not None


# ---------------------------------------------------------------------------
# validate_phase_evidence — MEASURE phase
# ---------------------------------------------------------------------------
class TestValidateMeasure:
    """Tests for MEASURE phase validation (requires metrics)."""

    def test_valid_with_metrics(self):
        cp = _make_checkpoint("measure", "Metrics collected", metrics={"test_count": 100})
        cycle = _make_cycle(checkpoints=[cp])
        assert validate_phase_evidence(cycle, DSPPhase.MEASURE) is None

    def test_fails_without_metrics(self):
        cp = _make_checkpoint("measure", "No metrics here")
        cycle = _make_cycle(checkpoints=[cp])
        result = validate_phase_evidence(cycle, DSPPhase.MEASURE)
        assert result is not None
        assert "metrics" in result.lower()

    def test_fails_with_empty_metrics(self):
        cp = _make_checkpoint("measure", "Empty metrics", metrics={})
        cycle = _make_cycle(checkpoints=[cp])
        result = validate_phase_evidence(cycle, DSPPhase.MEASURE)
        assert result is not None

    def test_fails_without_checkpoint(self):
        cycle = _make_cycle()
        result = validate_phase_evidence(cycle, DSPPhase.MEASURE)
        assert result is not None


# ---------------------------------------------------------------------------
# validate_phase_evidence — OPTIMIZE phase
# ---------------------------------------------------------------------------
class TestValidateOptimize:
    """Tests for OPTIMIZE phase validation."""

    def test_valid_with_checkpoint(self):
        cp = _make_checkpoint("optimize", "Applied optimization to reduce query time")
        cycle = _make_cycle(checkpoints=[cp])
        assert validate_phase_evidence(cycle, DSPPhase.OPTIMIZE) is None

    def test_fails_with_short_checkpoint(self):
        cp = _make_checkpoint("optimize", "Too short")  # < 20 chars
        cycle = _make_cycle(checkpoints=[cp])
        result = validate_phase_evidence(cycle, DSPPhase.OPTIMIZE)
        assert result is not None


# ---------------------------------------------------------------------------
# validate_phase_evidence — VALIDATE phase
# ---------------------------------------------------------------------------
class TestValidateValidate:
    """Tests for VALIDATE phase validation."""

    def test_valid_with_checkpoint(self):
        cp = _make_checkpoint("validate", "All tests pass")  # >= 10 chars
        cycle = _make_cycle(checkpoints=[cp])
        assert validate_phase_evidence(cycle, DSPPhase.VALIDATE) is None

    def test_fails_with_very_short(self):
        cp = _make_checkpoint("validate", "OK")  # < 10 chars
        cycle = _make_cycle(checkpoints=[cp])
        result = validate_phase_evidence(cycle, DSPPhase.VALIDATE)
        assert result is not None


# ---------------------------------------------------------------------------
# validate_phase_evidence — DREAM phase
# ---------------------------------------------------------------------------
class TestValidateDream:
    """Tests for DREAM phase validation."""

    def test_valid_with_finding(self):
        finding = {"phase": "dream", "type": "discovery", "description": "Found pattern"}
        cycle = _make_cycle(findings=[finding])
        assert validate_phase_evidence(cycle, DSPPhase.DREAM) is None

    def test_valid_with_checkpoint(self):
        cp = _make_checkpoint("dream", "Discovered new pattern in codebase")
        cycle = _make_cycle(checkpoints=[cp])
        assert validate_phase_evidence(cycle, DSPPhase.DREAM) is None

    def test_fails_without_evidence(self):
        cycle = _make_cycle()
        result = validate_phase_evidence(cycle, DSPPhase.DREAM)
        assert result is not None


# ---------------------------------------------------------------------------
# validate_phase_evidence — REPORT phase
# ---------------------------------------------------------------------------
class TestValidateReport:
    """Tests for REPORT phase validation (auto-generates evidence)."""

    def test_always_passes(self):
        cycle = _make_cycle()
        assert validate_phase_evidence(cycle, DSPPhase.REPORT) is None


# ---------------------------------------------------------------------------
# validate_phase_evidence — edge cases
# ---------------------------------------------------------------------------
class TestValidateEdgeCases:
    """Tests for edge cases in validate_phase_evidence()."""

    def test_unknown_phase(self):
        """Unknown phase should return None (allow)."""
        cycle = _make_cycle()
        assert validate_phase_evidence(cycle, DSPPhase.IDLE) is None

    def test_wrong_phase_checkpoints_ignored(self):
        """Checkpoints from other phases should not count."""
        cp = _make_checkpoint("optimize", "Valid checkpoint for optimize phase")
        cycle = _make_cycle(checkpoints=[cp])
        result = validate_phase_evidence(cycle, DSPPhase.HYPOTHESIZE)
        assert result is not None

    def test_wrong_phase_findings_ignored(self):
        """Findings from other phases should not count."""
        finding = {"phase": "dream", "type": "discovery"}
        cycle = _make_cycle(findings=[finding])
        result = validate_phase_evidence(cycle, DSPPhase.AUDIT)
        assert result is not None

    def test_multiple_checkpoints_one_valid(self):
        """If at least one checkpoint is valid, should pass."""
        cp1 = _make_checkpoint("hypothesize", "Short")
        cp2 = _make_checkpoint("hypothesize", "This is a long enough hypothesis description for validation")
        cycle = _make_cycle(checkpoints=[cp1, cp2])
        assert validate_phase_evidence(cycle, DSPPhase.HYPOTHESIZE) is None
