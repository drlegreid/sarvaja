"""
Unit tests for DSM Evidence Generation.

Per RULE-012: Tests for generate_evidence() DSM cycle evidence file generation.
"""

import pytest
from pathlib import Path

from governance.dsm.evidence import generate_evidence
from governance.dsm.models import DSMCycle, PhaseCheckpoint


def _make_cycle(**overrides):
    """Create a DSMCycle with reasonable defaults."""
    defaults = {
        "cycle_id": "DSM-2026-02-11-001",
        "batch_id": "BATCH-001",
        "start_time": "2026-02-11T09:00:00",
        "end_time": "2026-02-11T13:00:00",
        "phases_completed": ["audit", "hypothesize", "measure"],
        "checkpoints": [],
        "findings": [],
        "metrics": {},
    }
    defaults.update(overrides)
    return DSMCycle(**defaults)


def _make_checkpoint(phase="audit", description="Valid checkpoint", metrics=None, evidence=None):
    return PhaseCheckpoint(
        phase=phase,
        timestamp="2026-02-11T10:00:00",
        description=description,
        metrics=metrics or {},
        evidence=evidence or [],
    )


# ---------------------------------------------------------------------------
# generate_evidence — basic structure
# ---------------------------------------------------------------------------
class TestGenerateEvidenceBasic:
    """Tests for generate_evidence() basic output structure."""

    def test_creates_file(self, tmp_path):
        cycle = _make_cycle()
        result = generate_evidence(cycle, tmp_path)
        assert Path(result).exists()

    def test_filename_from_cycle_id(self, tmp_path):
        cycle = _make_cycle(cycle_id="DSM-TEST-001")
        result = generate_evidence(cycle, tmp_path)
        assert Path(result).name == "DSM-TEST-001.md"

    def test_creates_directory(self, tmp_path):
        sub = tmp_path / "nested" / "evidence"
        cycle = _make_cycle()
        generate_evidence(cycle, sub)
        assert sub.exists()

    def test_returns_string_path(self, tmp_path):
        cycle = _make_cycle()
        result = generate_evidence(cycle, tmp_path)
        assert isinstance(result, str)

    def test_title_includes_cycle_id(self, tmp_path):
        cycle = _make_cycle(cycle_id="DSM-XYZ")
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "# DSM Cycle Evidence: DSM-XYZ" in content


# ---------------------------------------------------------------------------
# generate_evidence — summary section
# ---------------------------------------------------------------------------
class TestGenerateEvidenceSummary:
    """Tests for summary section output."""

    def test_batch_id(self, tmp_path):
        cycle = _make_cycle(batch_id="BATCH-42")
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "BATCH-42" in content

    def test_no_batch_id(self, tmp_path):
        cycle = _make_cycle(batch_id=None)
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "N/A" in content

    def test_timestamps(self, tmp_path):
        cycle = _make_cycle(start_time="2026-02-11T09:00", end_time="2026-02-11T13:00")
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "2026-02-11T09:00" in content
        assert "2026-02-11T13:00" in content

    def test_phases_count(self, tmp_path):
        cycle = _make_cycle(phases_completed=["a", "b", "c"])
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "**Phases Completed:** 3" in content

    def test_findings_count(self, tmp_path):
        findings = [
            {"id": "F-1", "type": "gap", "severity": "HIGH", "description": "Found gap"},
            {"id": "F-2", "type": "issue", "severity": "LOW", "description": "Minor issue"},
        ]
        cycle = _make_cycle(findings=findings)
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "**Findings:** 2" in content


# ---------------------------------------------------------------------------
# generate_evidence — metrics section
# ---------------------------------------------------------------------------
class TestGenerateEvidenceMetrics:
    """Tests for metrics section output."""

    def test_metrics_table(self, tmp_path):
        cycle = _make_cycle(metrics={"test_count": 100, "coverage": "85%"})
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "## Metrics" in content
        assert "| test_count | 100 |" in content
        assert "| coverage | 85% |" in content

    def test_no_metrics_skips_section(self, tmp_path):
        cycle = _make_cycle(metrics={})
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "## Metrics" not in content


# ---------------------------------------------------------------------------
# generate_evidence — findings section
# ---------------------------------------------------------------------------
class TestGenerateEvidenceFindings:
    """Tests for findings section output."""

    def test_findings_table(self, tmp_path):
        findings = [
            {"id": "F-1", "type": "gap", "severity": "HIGH", "description": "Found a gap in coverage"},
        ]
        cycle = _make_cycle(findings=findings)
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "## Findings" in content
        assert "| F-1 | gap | HIGH |" in content

    def test_long_description_truncated(self, tmp_path):
        long_desc = "x" * 100
        findings = [{"id": "F-1", "type": "gap", "severity": "HIGH", "description": long_desc}]
        cycle = _make_cycle(findings=findings)
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "..." in content  # truncated

    def test_short_description_not_truncated(self, tmp_path):
        findings = [{"id": "F-1", "type": "gap", "severity": "HIGH", "description": "Short desc"}]
        cycle = _make_cycle(findings=findings)
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "Short desc" in content
        # "..." should not appear for short descriptions in the findings table
        lines = [l for l in content.split("\n") if "F-1" in l]
        assert "..." not in lines[0]

    def test_no_findings_skips_section(self, tmp_path):
        cycle = _make_cycle(findings=[])
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "## Findings" not in content


# ---------------------------------------------------------------------------
# generate_evidence — checkpoints section
# ---------------------------------------------------------------------------
class TestGenerateEvidenceCheckpoints:
    """Tests for checkpoints section output."""

    def test_checkpoint_header(self, tmp_path):
        cp = _make_checkpoint(phase="audit", description="Found orphan rules in TypeDB")
        cycle = _make_cycle(checkpoints=[cp])
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "## Checkpoints" in content
        assert "### AUDIT" in content

    def test_checkpoint_description(self, tmp_path):
        cp = _make_checkpoint(description="Detailed audit findings here")
        cycle = _make_cycle(checkpoints=[cp])
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "Detailed audit findings here" in content

    def test_checkpoint_evidence_list(self, tmp_path):
        cp = _make_checkpoint(evidence=["ev1.md", "ev2.md"])
        cycle = _make_cycle(checkpoints=[cp])
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "**Evidence:**" in content
        assert "- ev1.md" in content
        assert "- ev2.md" in content

    def test_no_evidence_skips_list(self, tmp_path):
        cp = _make_checkpoint(evidence=[])
        cycle = _make_cycle(checkpoints=[cp])
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "**Evidence:**" not in content

    def test_multiple_checkpoints(self, tmp_path):
        cps = [
            _make_checkpoint(phase="audit", description="Audit phase findings"),
            _make_checkpoint(phase="measure", description="Measurement results"),
        ]
        cycle = _make_cycle(checkpoints=cps)
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "### AUDIT" in content
        assert "### MEASURE" in content

    def test_no_checkpoints_skips_section(self, tmp_path):
        cycle = _make_cycle(checkpoints=[])
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "## Checkpoints" not in content


# ---------------------------------------------------------------------------
# generate_evidence — footer
# ---------------------------------------------------------------------------
class TestGenerateEvidenceFooter:
    """Tests for footer section."""

    def test_footer_present(self, tmp_path):
        cycle = _make_cycle()
        path = generate_evidence(cycle, tmp_path)
        content = Path(path).read_text()
        assert "RULE-012" in content
        assert "Deep Sleep Protocol" in content
