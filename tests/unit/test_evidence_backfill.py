"""
Unit tests for Evidence Scanner — Backfill module.

Per DOC-SIZE-01-v1: Tests for extracted evidence_scanner/backfill.py.
Tests: scan_evidence_files, scan_task_session_linkages, format_scan_summary,
       format_apply_summary.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from governance.evidence_scanner.backfill import (
    scan_evidence_files,
    scan_task_session_linkages,
    format_scan_summary,
    format_apply_summary,
)
from governance.evidence_scanner.extractors import BackfillResult, LinkageProposal


class TestScanEvidenceFiles:
    """Tests for scan_evidence_files()."""

    def test_nonexistent_directory(self, tmp_path):
        result = scan_evidence_files(evidence_dir=str(tmp_path / "nope"))
        assert result == []

    def test_empty_directory(self, tmp_path):
        result = scan_evidence_files(evidence_dir=str(tmp_path))
        assert result == []

    def test_scans_matching_files(self, tmp_path):
        ev = tmp_path / "SESSION-2026-01-01-TEST.md"
        ev.write_text("Task: TASK-001\n")

        with patch(
            "governance.evidence_scanner.backfill.WORKSPACE_ROOT",
            str(tmp_path),
        ), patch(
            "governance.evidence_scanner.backfill.extract_session_id",
            return_value="SESSION-2026-01-01-TEST",
        ):
            result = scan_evidence_files(
                pattern="SESSION-*.md",
                evidence_dir=str(tmp_path),
            )

        assert len(result) == 1
        assert result[0].session_id == "SESSION-2026-01-01-TEST"

    def test_ignores_non_matching(self, tmp_path):
        (tmp_path / "README.md").write_text("not evidence")
        result = scan_evidence_files(
            pattern="SESSION-*.md",
            evidence_dir=str(tmp_path),
        )
        assert result == []


class TestScanTaskSessionLinkages:
    """Tests for scan_task_session_linkages()."""

    @patch("governance.evidence_scanner.backfill.get_existing_task_ids")
    @patch("governance.evidence_scanner.backfill.scan_evidence_files")
    def test_empty_scan(self, mock_scan, mock_tasks):
        mock_scan.return_value = []
        mock_tasks.return_value = set()
        result = scan_task_session_linkages()
        assert isinstance(result, BackfillResult)
        assert result.scanned == 0
        assert result.proposed == 0

    @patch("governance.evidence_scanner.backfill.get_existing_task_ids")
    @patch("governance.evidence_scanner.backfill.scan_evidence_files")
    def test_proposes_existing_tasks(self, mock_scan, mock_tasks):
        mock_sr = MagicMock()
        mock_sr.task_refs = ["TASK-001", "TASK-002"]
        mock_sr.session_id = "SESSION-2026-01-01-X"
        mock_sr.file_path = "evidence/SESSION-2026-01-01-X.md"
        mock_scan.return_value = [mock_sr]
        mock_tasks.return_value = {"TASK-001"}

        result = scan_task_session_linkages()
        assert result.proposed == 1
        assert result.skipped == 1  # TASK-002 not in TypeDB

    @patch("governance.evidence_scanner.backfill.get_existing_task_ids")
    @patch("governance.evidence_scanner.backfill.scan_evidence_files")
    def test_proposal_structure(self, mock_scan, mock_tasks):
        mock_sr = MagicMock()
        mock_sr.task_refs = ["TASK-001"]
        mock_sr.session_id = "SESSION-X"
        mock_sr.file_path = "evidence/SESSION-X.md"
        mock_scan.return_value = [mock_sr]
        mock_tasks.return_value = {"TASK-001"}

        result = scan_task_session_linkages()
        assert len(result.proposals) == 1
        p = result.proposals[0]
        assert p.source_id == "TASK-001"
        assert p.target_id == "SESSION-X"
        assert p.relation == "completed-in"


class TestFormatScanSummary:
    """Tests for format_scan_summary()."""

    def test_empty_result(self):
        result = BackfillResult()
        summary = format_scan_summary(result)
        assert summary["scanned_files"] == 0
        assert summary["proposed_linkages"] == 0
        assert summary["by_session"] == {}

    def test_groups_by_session(self):
        result = BackfillResult()
        result.scanned = 2
        result.proposed = 3
        result.proposals = [
            LinkageProposal("TASK-1", "SESSION-A", "completed-in", "ev1.md"),
            LinkageProposal("TASK-2", "SESSION-A", "completed-in", "ev1.md"),
            LinkageProposal("TASK-3", "SESSION-B", "completed-in", "ev2.md"),
        ]
        summary = format_scan_summary(result)
        assert summary["by_session"]["SESSION-A"]["task_count"] == 2
        assert summary["by_session"]["SESSION-B"]["task_count"] == 1

    def test_caps_tasks_at_5(self):
        result = BackfillResult()
        result.proposals = [
            LinkageProposal(f"TASK-{i}", "SESSION-X", "completed-in", "ev.md")
            for i in range(8)
        ]
        summary = format_scan_summary(result)
        assert len(summary["by_session"]["SESSION-X"]["tasks"]) == 5
        assert summary["by_session"]["SESSION-X"]["more"] == 3


class TestFormatApplySummary:
    """Tests for format_apply_summary()."""

    def test_includes_created_and_errors(self):
        result = BackfillResult()
        result.scanned = 5
        result.created = 3
        result.errors = ["err1", "err2"]
        summary = format_apply_summary(result)
        assert summary["created"] == 3
        assert len(summary["errors"]) == 2
        assert summary["error_count"] == 2

    def test_caps_errors_at_5(self):
        result = BackfillResult()
        result.errors = [f"err{i}" for i in range(10)]
        summary = format_apply_summary(result)
        assert len(summary["errors"]) == 5
        assert summary["error_count"] == 10
