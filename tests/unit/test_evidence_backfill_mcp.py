"""
Unit tests for Evidence Backfill MCP Tools.

Per DOC-SIZE-01-v1: Tests for governance/mcp_tools/evidence_backfill.py module.
Tests: register_evidence_backfill_tools — scan/execute task-sessions,
       scan/execute evidence-sessions, scan all evidence.
"""

import json
import os
from dataclasses import dataclass
from typing import Set
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.evidence_backfill import register_evidence_backfill_tools


@dataclass
class _MockScanResult:
    """Mock ScanResult for backfill_scan_all_evidence."""
    session_id: str
    file_path: str
    task_refs: Set[str]
    rule_refs: Set[str]
    gap_refs: Set[str]


class _CaptureMCP:
    """Capture @mcp.tool() decorated functions."""

    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@pytest.fixture(autouse=True)
def _json_output(monkeypatch):
    """Force JSON output from format_mcp_result."""
    monkeypatch.setenv("MCP_OUTPUT_FORMAT", "json")


@pytest.fixture
def mcp():
    m = _CaptureMCP()
    register_evidence_backfill_tools(m)
    return m


# ── Registration ─────────────────────────────────────────


class TestRegistration:
    def test_registers_five_tools(self, mcp):
        assert len(mcp.tools) == 5

    def test_tool_names(self, mcp):
        expected = {
            "backfill_scan_task_sessions",
            "backfill_execute_task_sessions",
            "backfill_scan_evidence_sessions",
            "backfill_execute_evidence_sessions",
            "backfill_scan_all_evidence",
        }
        assert set(mcp.tools.keys()) == expected


# ── backfill_scan_task_sessions ──────────────────────────


class TestScanTaskSessions:
    def test_scan_success(self, mcp):
        with patch("governance.evidence_scanner.scan_task_session_linkages") as mock_scan, \
             patch("governance.evidence_scanner.format_scan_summary") as mock_fmt:
            mock_scan.return_value = {"sessions": 5, "links": 10}
            mock_fmt.return_value = {"summary": "5 sessions, 10 links"}
            result = mcp.tools["backfill_scan_task_sessions"]()
        data = json.loads(result)
        assert data["summary"] == "5 sessions, 10 links"

    def test_scan_exception(self, mcp):
        with patch.dict("sys.modules", {"governance.evidence_scanner": MagicMock(
            scan_task_session_linkages=MagicMock(side_effect=Exception("scan failed"))
        )}):
            result = mcp.tools["backfill_scan_task_sessions"]()
        data = json.loads(result)
        assert "error" in data


# ── backfill_execute_task_sessions ───────────────────────


class TestExecuteTaskSessions:
    def test_execute_dry_run(self, mcp):
        with patch("governance.evidence_scanner.apply_task_session_linkages") as mock_apply, \
             patch("governance.evidence_scanner.format_apply_summary") as mock_fmt:
            mock_apply.return_value = {"created": 0}
            mock_fmt.return_value = {"total": 5, "created": 0}
            result = mcp.tools["backfill_execute_task_sessions"](dry_run=True)
        data = json.loads(result)
        assert data["mode"] == "DRY_RUN"

    def test_execute_real(self, mcp):
        with patch("governance.evidence_scanner.apply_task_session_linkages") as mock_apply, \
             patch("governance.evidence_scanner.format_apply_summary") as mock_fmt:
            mock_apply.return_value = {"created": 3}
            mock_fmt.return_value = {"total": 5, "created": 3}
            result = mcp.tools["backfill_execute_task_sessions"](dry_run=False)
        data = json.loads(result)
        assert data["mode"] == "EXECUTED"

    def test_execute_exception(self, mcp):
        with patch.dict("sys.modules", {"governance.evidence_scanner": MagicMock(
            apply_task_session_linkages=MagicMock(side_effect=Exception("write failed"))
        )}):
            result = mcp.tools["backfill_execute_task_sessions"]()
        data = json.loads(result)
        assert "error" in data


# ── backfill_scan_evidence_sessions ──────────────────────


class TestScanEvidenceSessions:
    def test_scan_success(self, mcp):
        with patch("governance.evidence_scanner.scan_evidence_session_links") as mock_scan, \
             patch("governance.evidence_scanner.format_evidence_link_summary") as mock_fmt:
            mock_scan.return_value = {"links": 8}
            mock_fmt.return_value = {"total_links": 8}
            result = mcp.tools["backfill_scan_evidence_sessions"]()
        data = json.loads(result)
        assert data["total_links"] == 8

    def test_scan_exception(self, mcp):
        with patch.dict("sys.modules", {"governance.evidence_scanner": MagicMock(
            scan_evidence_session_links=MagicMock(side_effect=Exception("io error"))
        )}):
            result = mcp.tools["backfill_scan_evidence_sessions"]()
        data = json.loads(result)
        assert "error" in data


# ── backfill_execute_evidence_sessions ───────────────────


class TestExecuteEvidenceSessions:
    def test_execute_dry_run(self, mcp):
        with patch("governance.evidence_scanner.apply_evidence_session_links") as mock_apply, \
             patch("governance.evidence_scanner.format_evidence_link_summary") as mock_fmt:
            mock_apply.return_value = {"linked": 0}
            mock_fmt.return_value = {"total": 5, "linked": 0}
            result = mcp.tools["backfill_execute_evidence_sessions"](dry_run=True)
        data = json.loads(result)
        assert data["mode"] == "DRY_RUN"

    def test_execute_real(self, mcp):
        with patch("governance.evidence_scanner.apply_evidence_session_links") as mock_apply, \
             patch("governance.evidence_scanner.format_evidence_link_summary") as mock_fmt:
            mock_apply.return_value = {"linked": 4}
            mock_fmt.return_value = {"total": 5, "linked": 4}
            result = mcp.tools["backfill_execute_evidence_sessions"](dry_run=False)
        data = json.loads(result)
        assert data["mode"] == "EXECUTED"

    def test_exception(self, mcp):
        with patch.dict("sys.modules", {"governance.evidence_scanner": MagicMock(
            apply_evidence_session_links=MagicMock(side_effect=Exception("err"))
        )}):
            result = mcp.tools["backfill_execute_evidence_sessions"]()
        data = json.loads(result)
        assert "error" in data


# ── backfill_scan_all_evidence ───────────────────────────


class TestScanAllEvidence:
    def test_scan_success(self, mcp):
        mock_results = [
            _MockScanResult("S-001", "evidence/S-001.md", {"T-1", "T-2"}, {"R-1"}, set()),
            _MockScanResult("S-002", "evidence/S-002.md", set(), {"R-2"}, {"GAP-001"}),
        ]
        with patch("governance.evidence_scanner.scan_all_evidence_files", return_value=mock_results):
            result = mcp.tools["backfill_scan_all_evidence"]()
        data = json.loads(result)
        assert data["total_files"] == 2
        assert data["totals"]["task_refs"] == 2
        assert data["totals"]["rule_refs"] == 2
        assert data["totals"]["gap_refs"] == 1

    def test_scan_empty(self, mcp):
        with patch("governance.evidence_scanner.scan_all_evidence_files", return_value=[]):
            result = mcp.tools["backfill_scan_all_evidence"]()
        data = json.loads(result)
        assert data["total_files"] == 0

    def test_scan_exception(self, mcp):
        with patch.dict("sys.modules", {"governance.evidence_scanner": MagicMock(
            scan_all_evidence_files=MagicMock(side_effect=Exception("crash"))
        )}):
            result = mcp.tools["backfill_scan_all_evidence"]()
        data = json.loads(result)
        assert "error" in data
