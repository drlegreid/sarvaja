"""
Unit tests for Evidence Scanner — Linking module.

Per DOC-SIZE-01-v1: Tests for extracted evidence_scanner/linking.py.
Tests: _extract_session_id_from_evidence, scan_all_evidence_files,
       scan_evidence_session_links, format_evidence_link_summary.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from governance.evidence_scanner.linking import (
    _extract_session_id_from_evidence,
    scan_all_evidence_files,
    scan_evidence_session_links,
    format_evidence_link_summary,
)
from governance.evidence_scanner.extractors import EvidenceLinkResult


class TestExtractSessionIdFromEvidence:
    """Tests for _extract_session_id_from_evidence()."""

    def test_session_file(self):
        path = Path("/evidence/SESSION-2026-01-28-TOPIC.md")
        assert _extract_session_id_from_evidence(path) == "SESSION-2026-01-28-TOPIC"

    def test_dsm_file(self):
        path = Path("/evidence/DSM-2026-01-25-015206.md")
        assert _extract_session_id_from_evidence(path) == "DSM-2026-01-25-015206"

    def test_nested_path(self):
        path = Path("/a/b/c/SESSION-2026-02-10-TEST.md")
        assert _extract_session_id_from_evidence(path) == "SESSION-2026-02-10-TEST"


class TestScanAllEvidenceFiles:
    """Tests for scan_all_evidence_files()."""

    def test_nonexistent_directory(self, tmp_path):
        result = scan_all_evidence_files(str(tmp_path / "nope"))
        assert result == []

    def test_empty_directory(self, tmp_path):
        result = scan_all_evidence_files(str(tmp_path))
        assert result == []

    def test_scans_session_files(self, tmp_path):
        # Create a test evidence file
        ev = tmp_path / "SESSION-2026-02-11-TEST.md"
        ev.write_text("# Session\nTask: TASK-001\nRule: RULE-001-v1\n")

        with patch(
            "governance.evidence_scanner.linking.WORKSPACE_ROOT",
            str(tmp_path),
        ), patch(
            "governance.evidence_scanner.linking.EVIDENCE_PATTERNS",
            ["SESSION-*.md"],
        ):
            result = scan_all_evidence_files(str(tmp_path))

        assert len(result) == 1
        assert result[0].session_id == "SESSION-2026-02-11-TEST"

    def test_deduplicates_files(self, tmp_path):
        ev = tmp_path / "SESSION-2026-01-01-DUP.md"
        ev.write_text("test")

        with patch(
            "governance.evidence_scanner.linking.WORKSPACE_ROOT",
            str(tmp_path),
        ), patch(
            "governance.evidence_scanner.linking.EVIDENCE_PATTERNS",
            ["SESSION-*.md", "*.md"],  # Would match twice
        ):
            result = scan_all_evidence_files(str(tmp_path))

        assert len(result) == 1


class TestScanEvidenceSessionLinks:
    """Tests for scan_evidence_session_links()."""

    def test_returns_link_result(self, tmp_path):
        with patch(
            "governance.evidence_scanner.linking.scan_all_evidence_files",
            return_value=[],
        ):
            result = scan_evidence_session_links(str(tmp_path))

        assert isinstance(result, EvidenceLinkResult)
        assert result.scanned == 0

    def test_populates_details(self, tmp_path):
        mock_sr = MagicMock()
        mock_sr.file_path = "evidence/SESSION-2026-01-01-X.md"
        mock_sr.session_id = "SESSION-2026-01-01-X"
        mock_sr.task_refs = ["TASK-001"]
        mock_sr.rule_refs = ["RULE-001"]
        mock_sr.gap_refs = []

        with patch(
            "governance.evidence_scanner.linking.scan_all_evidence_files",
            return_value=[mock_sr],
        ):
            result = scan_evidence_session_links(str(tmp_path))

        assert result.scanned == 1
        assert len(result.details) == 1
        assert result.details[0]["session_id"] == "SESSION-2026-01-01-X"
        assert result.details[0]["task_refs"] == 1


class TestFormatEvidenceLinkSummary:
    """Tests for format_evidence_link_summary()."""

    def test_empty_result(self):
        result = EvidenceLinkResult()
        summary = format_evidence_link_summary(result)
        assert summary["scanned_files"] == 0
        assert summary["linked"] == 0
        assert summary["errors"] == []

    def test_with_data(self):
        result = EvidenceLinkResult()
        result.scanned = 5
        result.linked = 3
        result.skipped = 2
        result.details = [{"evidence_path": f"ev{i}.md"} for i in range(5)]
        summary = format_evidence_link_summary(result)
        assert summary["scanned_files"] == 5
        assert summary["linked"] == 3
        assert summary["skipped"] == 2
        assert len(summary["evidence_files"]) == 5

    def test_caps_evidence_files_at_10(self):
        result = EvidenceLinkResult()
        result.details = [{"evidence_path": f"ev{i}.md"} for i in range(15)]
        summary = format_evidence_link_summary(result)
        assert len(summary["evidence_files"]) == 10
        assert summary["more"] == 5

    def test_caps_errors_at_5(self):
        result = EvidenceLinkResult()
        result.errors = [f"error {i}" for i in range(10)]
        summary = format_evidence_link_summary(result)
        assert len(summary["errors"]) == 5
        assert summary["error_count"] == 10
