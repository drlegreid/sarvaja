"""
Unit tests for DSM Data Models.

Per DOC-SIZE-01-v1: Tests for dsm/models.py module.
Tests: PhaseCheckpoint, DSMCycle dataclasses.
"""

import pytest
from dataclasses import asdict

from governance.dsm.models import PhaseCheckpoint, DSMCycle


# ---------------------------------------------------------------------------
# PhaseCheckpoint
# ---------------------------------------------------------------------------
class TestPhaseCheckpoint:
    """Tests for PhaseCheckpoint dataclass."""

    def test_required_fields(self):
        cp = PhaseCheckpoint(phase="audit", timestamp="2026-02-11T10:00:00", description="Started audit")
        assert cp.phase == "audit"
        assert cp.timestamp == "2026-02-11T10:00:00"
        assert cp.description == "Started audit"

    def test_defaults(self):
        cp = PhaseCheckpoint(phase="audit", timestamp="t", description="d")
        assert cp.metrics == {}
        assert cp.evidence == []

    def test_metrics_and_evidence(self):
        cp = PhaseCheckpoint(
            phase="measure",
            timestamp="t",
            description="d",
            metrics={"coverage": 0.85},
            evidence=["evidence/E-001.md"],
        )
        assert cp.metrics["coverage"] == 0.85
        assert len(cp.evidence) == 1

    def test_asdict(self):
        cp = PhaseCheckpoint(phase="audit", timestamp="t", description="d")
        d = asdict(cp)
        assert isinstance(d, dict)
        assert d["phase"] == "audit"
        assert d["metrics"] == {}

    def test_independent_defaults(self):
        cp1 = PhaseCheckpoint(phase="a", timestamp="t", description="d")
        cp2 = PhaseCheckpoint(phase="b", timestamp="t", description="d")
        cp1.metrics["x"] = 1
        assert "x" not in cp2.metrics

    def test_evidence_list_independence(self):
        cp1 = PhaseCheckpoint(phase="a", timestamp="t", description="d")
        cp2 = PhaseCheckpoint(phase="b", timestamp="t", description="d")
        cp1.evidence.append("file.md")
        assert len(cp2.evidence) == 0


# ---------------------------------------------------------------------------
# DSMCycle
# ---------------------------------------------------------------------------
class TestDSMCycle:
    """Tests for DSMCycle dataclass."""

    def test_required_field(self):
        cycle = DSMCycle(cycle_id="DSM-001")
        assert cycle.cycle_id == "DSM-001"

    def test_defaults(self):
        cycle = DSMCycle(cycle_id="DSM-001")
        assert cycle.batch_id is None
        assert cycle.start_time is None
        assert cycle.end_time is None
        assert cycle.current_phase == "idle"
        assert cycle.phases_completed == []
        assert cycle.checkpoints == []
        assert cycle.findings == []
        assert cycle.metrics == {}

    def test_with_all_fields(self):
        cycle = DSMCycle(
            cycle_id="DSM-002",
            batch_id="BATCH-001",
            start_time="2026-02-11T10:00:00Z",
            end_time="2026-02-11T11:00:00Z",
            current_phase="measure",
            phases_completed=["audit", "hypothesize"],
            findings=[{"id": "F-1", "severity": "high"}],
            metrics={"coverage": 0.9},
        )
        assert cycle.batch_id == "BATCH-001"
        assert len(cycle.phases_completed) == 2
        assert cycle.findings[0]["id"] == "F-1"

    def test_to_dict(self):
        cycle = DSMCycle(cycle_id="DSM-001")
        d = cycle.to_dict()
        assert isinstance(d, dict)
        assert d["cycle_id"] == "DSM-001"
        assert d["current_phase"] == "idle"
        assert d["checkpoints"] == []

    def test_to_dict_with_checkpoints(self):
        cp = PhaseCheckpoint(phase="audit", timestamp="t", description="d", metrics={"k": 1})
        cycle = DSMCycle(cycle_id="DSM-001", checkpoints=[cp])
        d = cycle.to_dict()
        assert len(d["checkpoints"]) == 1
        assert d["checkpoints"][0]["phase"] == "audit"
        assert d["checkpoints"][0]["metrics"] == {"k": 1}

    def test_to_dict_contains_all_keys(self):
        cycle = DSMCycle(cycle_id="DSM-001")
        d = cycle.to_dict()
        expected_keys = {"cycle_id", "batch_id", "start_time", "end_time",
                         "current_phase", "phases_completed", "checkpoints",
                         "findings", "metrics"}
        assert set(d.keys()) == expected_keys

    def test_independent_instances(self):
        c1 = DSMCycle(cycle_id="DSM-001")
        c2 = DSMCycle(cycle_id="DSM-002")
        c1.phases_completed.append("audit")
        c1.findings.append({"x": 1})
        assert len(c2.phases_completed) == 0
        assert len(c2.findings) == 0

    def test_to_dict_checkpoints_are_dicts(self):
        """Verify checkpoints serialized via asdict, not raw objects."""
        cp = PhaseCheckpoint(phase="p", timestamp="t", description="d")
        cycle = DSMCycle(cycle_id="DSM-001", checkpoints=[cp])
        d = cycle.to_dict()
        assert isinstance(d["checkpoints"][0], dict)
