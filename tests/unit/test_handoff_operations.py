"""
Unit tests for Handoff Operations.

Per DOC-SIZE-01-v1: Tests for extracted handoff_pkg/operations.py module.
Tests: create_handoff, parse_handoff, write_handoff_evidence,
       read_handoff_evidence, get_pending_handoffs.
"""

import pytest
from pathlib import Path

from governance.orchestrator.handoff_pkg.operations import (
    create_handoff,
    parse_handoff,
    write_handoff_evidence,
    read_handoff_evidence,
    get_pending_handoffs,
)
from governance.orchestrator.handoff_pkg.models import HandoffStatus


class TestCreateHandoff:
    """Tests for create_handoff()."""

    def test_basic_creation(self):
        h = create_handoff(
            task_id="GAP-001",
            title="Test Handoff",
            from_agent="research",
            to_agent="coding",
            context_summary="Research done",
            recommended_action="Implement feature",
        )
        assert h.task_id == "GAP-001"
        assert h.from_agent == "RESEARCH"
        assert h.to_agent == "CODING"
        assert h.status == HandoffStatus.READY_FOR_CODING.value

    def test_status_mapping_research(self):
        h = create_handoff("T-1", "T", "coding", "research", "", "")
        assert h.status == HandoffStatus.READY_FOR_RESEARCH.value

    def test_status_mapping_curator(self):
        h = create_handoff("T-1", "T", "coding", "curator", "", "")
        assert h.status == HandoffStatus.READY_FOR_REVIEW.value

    def test_status_mapping_sync(self):
        h = create_handoff("T-1", "T", "coding", "sync", "", "")
        assert h.status == HandoffStatus.READY_FOR_SYNC.value

    def test_unknown_agent_defaults_in_progress(self):
        h = create_handoff("T-1", "T", "coding", "unknown", "", "")
        assert h.status == HandoffStatus.IN_PROGRESS.value

    def test_with_all_fields(self):
        h = create_handoff(
            task_id="GAP-002",
            title="Full Handoff",
            from_agent="research",
            to_agent="coding",
            context_summary="Summary",
            recommended_action="Build it",
            files_examined=["a.py"],
            evidence_gathered=["evidence"],
            action_steps=["step 1"],
            linked_rules=["R-01"],
            constraints=["max 300 lines"],
            priority="HIGH",
            source_session_id="SESSION-2026-02-11-TEST",
        )
        assert h.files_examined == ["a.py"]
        assert h.priority == "HIGH"
        assert h.source_session_id == "SESSION-2026-02-11-TEST"

    def test_defaults_empty_lists(self):
        h = create_handoff("T-1", "T", "r", "c", "", "")
        assert h.files_examined == []
        assert h.evidence_gathered == []
        assert h.action_steps == []


class TestParseHandoff:
    """Tests for parse_handoff()."""

    def test_valid_markdown(self):
        h = create_handoff("T-1", "Parse Test", "research", "coding", "ctx", "action")
        md = h.to_markdown()
        parsed = parse_handoff(md)
        assert parsed is not None
        assert parsed.task_id == "T-1"

    def test_invalid_markdown(self):
        assert parse_handoff("no task id here") is None


class TestWriteAndReadHandoffEvidence:
    """Tests for write_handoff_evidence() and read_handoff_evidence()."""

    def test_write_creates_file(self, tmp_path):
        h = create_handoff("GAP-005", "Write Test", "research", "coding", "ctx", "act")
        filepath = write_handoff_evidence(h, evidence_dir=tmp_path)
        assert filepath.exists()
        assert "HANDOFF-GAP-005-RESEARCH-CODING.md" == filepath.name

    def test_roundtrip(self, tmp_path):
        h = create_handoff("GAP-006", "Roundtrip", "coding", "curator", "ctx", "review it")
        filepath = write_handoff_evidence(h, evidence_dir=tmp_path)
        loaded = read_handoff_evidence(filepath)
        assert loaded is not None
        assert loaded.task_id == "GAP-006"
        assert loaded.from_agent == "CODING"

    def test_read_nonexistent(self, tmp_path):
        assert read_handoff_evidence(tmp_path / "nope.md") is None


class TestGetPendingHandoffs:
    """Tests for get_pending_handoffs()."""

    def test_empty_dir(self, tmp_path):
        assert get_pending_handoffs(evidence_dir=tmp_path) == []

    def test_finds_pending(self, tmp_path):
        h1 = create_handoff("T-1", "H1", "r", "coding", "", "")
        h2 = create_handoff("T-2", "H2", "r", "research", "", "")
        write_handoff_evidence(h1, evidence_dir=tmp_path)
        write_handoff_evidence(h2, evidence_dir=tmp_path)
        result = get_pending_handoffs(evidence_dir=tmp_path)
        assert len(result) == 2

    def test_filters_by_agent(self, tmp_path):
        h1 = create_handoff("T-1", "H1", "r", "coding", "", "")
        h2 = create_handoff("T-2", "H2", "r", "research", "", "")
        write_handoff_evidence(h1, evidence_dir=tmp_path)
        write_handoff_evidence(h2, evidence_dir=tmp_path)
        result = get_pending_handoffs(evidence_dir=tmp_path, for_agent="CODING")
        assert len(result) == 1
        assert result[0].task_id == "T-1"

    def test_excludes_completed(self, tmp_path):
        h = create_handoff("T-1", "H1", "r", "coding", "", "")
        h.status = HandoffStatus.COMPLETED.value
        write_handoff_evidence(h, evidence_dir=tmp_path)
        result = get_pending_handoffs(evidence_dir=tmp_path)
        assert len(result) == 0

    def test_nonexistent_dir(self, tmp_path):
        result = get_pending_handoffs(evidence_dir=tmp_path / "nope")
        assert result == []
