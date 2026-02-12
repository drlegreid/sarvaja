"""
Unit tests for DSP Phases Enum.

Per DOC-SIZE-01-v1: Tests for dsm/phases.py module.
Tests: DSPPhase enum values, phase_order, next_phase, prev_phase, required_mcps.
"""

import pytest

from governance.dsm.phases import DSPPhase


class TestDSPPhaseValues:
    """Tests for DSPPhase enum values."""

    def test_all_phases_exist(self):
        expected = ["idle", "audit", "hypothesize", "measure", "optimize",
                     "validate", "dream", "report", "complete"]
        for val in expected:
            assert DSPPhase(val).value == val

    def test_phase_count(self):
        assert len(DSPPhase) == 9


class TestPhaseOrder:
    """Tests for DSPPhase.phase_order()."""

    def test_excludes_idle_and_complete(self):
        order = DSPPhase.phase_order()
        assert DSPPhase.IDLE not in order
        assert DSPPhase.COMPLETE not in order

    def test_correct_order(self):
        order = DSPPhase.phase_order()
        assert order == [
            DSPPhase.AUDIT, DSPPhase.HYPOTHESIZE, DSPPhase.MEASURE,
            DSPPhase.OPTIMIZE, DSPPhase.VALIDATE, DSPPhase.DREAM,
            DSPPhase.REPORT,
        ]

    def test_seven_phases(self):
        assert len(DSPPhase.phase_order()) == 7


class TestNextPhase:
    """Tests for DSPPhase.next_phase()."""

    def test_idle_to_audit(self):
        assert DSPPhase.IDLE.next_phase() == DSPPhase.AUDIT

    def test_audit_to_hypothesize(self):
        assert DSPPhase.AUDIT.next_phase() == DSPPhase.HYPOTHESIZE

    def test_report_to_complete(self):
        assert DSPPhase.REPORT.next_phase() == DSPPhase.COMPLETE

    def test_complete_returns_none(self):
        assert DSPPhase.COMPLETE.next_phase() is None

    def test_full_sequence(self):
        phase = DSPPhase.IDLE
        sequence = []
        while phase is not None:
            sequence.append(phase)
            phase = phase.next_phase()
        assert len(sequence) == 9  # IDLE + 7 phases + COMPLETE
        assert sequence[0] == DSPPhase.IDLE
        assert sequence[-1] == DSPPhase.COMPLETE


class TestPrevPhase:
    """Tests for DSPPhase.prev_phase()."""

    def test_idle_returns_idle(self):
        assert DSPPhase.IDLE.prev_phase() == DSPPhase.IDLE

    def test_audit_returns_idle(self):
        assert DSPPhase.AUDIT.prev_phase() == DSPPhase.IDLE

    def test_hypothesize_returns_audit(self):
        assert DSPPhase.HYPOTHESIZE.prev_phase() == DSPPhase.AUDIT

    def test_complete_returns_report(self):
        assert DSPPhase.COMPLETE.prev_phase() == DSPPhase.REPORT


class TestRequiredMcps:
    """Tests for DSPPhase.required_mcps."""

    def test_audit_requires_governance(self):
        mcps = DSPPhase.AUDIT.required_mcps
        assert "governance" in mcps
        assert "claude-mem" in mcps

    def test_idle_empty(self):
        assert DSPPhase.IDLE.required_mcps == []

    def test_complete_empty(self):
        assert DSPPhase.COMPLETE.required_mcps == []

    def test_validate_requires_pytest(self):
        assert "pytest" in DSPPhase.VALIDATE.required_mcps

    def test_all_phases_have_property(self):
        for phase in DSPPhase:
            mcps = phase.required_mcps
            assert isinstance(mcps, list)
