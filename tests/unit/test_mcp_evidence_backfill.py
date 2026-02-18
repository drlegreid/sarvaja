"""
Unit tests for Evidence Backfill MCP Tools.

Batch 151: Tests for governance/mcp_tools/evidence_backfill.py
- backfill_scan_task_sessions: dry-run scan
- backfill_execute_task_sessions: create linkages (dry_run flag)
- backfill_scan_evidence_sessions: evidence→session scan
- backfill_execute_evidence_sessions: create evidence links
- backfill_scan_all_evidence: comprehensive entity ref scan
"""

import json
from dataclasses import dataclass, field
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.evidence_backfill import register_evidence_backfill_tools


_MOD = "governance.mcp_tools.evidence_backfill"


def _json_fmt(data):
    return json.dumps(data, indent=2, default=str)


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


def _register():
    mcp = _CaptureMCP()
    register_evidence_backfill_tools(mcp)
    return mcp.tools


@pytest.fixture(autouse=True)
def _force_json():
    with patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt):
        yield


# ── Registration ────────────────────────────────────────

class TestRegistration:
    def test_registers_five_tools(self):
        tools = _register()
        assert len(tools) == 5
        assert "backfill_scan_task_sessions" in tools
        assert "backfill_execute_task_sessions" in tools
        assert "backfill_scan_evidence_sessions" in tools
        assert "backfill_execute_evidence_sessions" in tools
        assert "backfill_scan_all_evidence" in tools


# ── backfill_scan_task_sessions ─────────────────────────

class TestBackfillScanTaskSessions:
    @patch("governance.evidence_scanner.format_scan_summary")
    @patch("governance.evidence_scanner.scan_task_session_linkages")
    def test_success(self, mock_scan, mock_fmt):
        mock_scan.return_value = {"sessions": []}
        mock_fmt.return_value = {"total_sessions": 0, "total_tasks": 0}
        tools = _register()
        result = json.loads(tools["backfill_scan_task_sessions"]())
        assert "total_sessions" in result
        mock_scan.assert_called_once()

    def test_import_error(self):
        tools = _register()
        with patch.dict("sys.modules", {"governance.evidence_scanner": None}):
            result = json.loads(tools["backfill_scan_task_sessions"]())
            assert "error" in result

    @patch("governance.evidence_scanner.scan_task_session_linkages",
           side_effect=Exception("scan failed"))
    def test_exception(self, mock_scan):
        tools = _register()
        result = json.loads(tools["backfill_scan_task_sessions"]())
        assert "error" in result
        assert "backfill_scan_task_sessions failed: Exception" in result["error"]


# ── backfill_execute_task_sessions ──────────────────────

class TestBackfillExecuteTaskSessions:
    @patch("governance.evidence_scanner.format_apply_summary")
    @patch("governance.evidence_scanner.apply_task_session_linkages")
    def test_dry_run(self, mock_apply, mock_fmt):
        mock_apply.return_value = {"created": 0}
        mock_fmt.return_value = {"created": 0, "errors": []}
        tools = _register()
        result = json.loads(tools["backfill_execute_task_sessions"](dry_run=True))
        assert result["mode"] == "DRY_RUN"
        mock_apply.assert_called_once_with(dry_run=True)

    @patch("governance.evidence_scanner.format_apply_summary")
    @patch("governance.evidence_scanner.apply_task_session_linkages")
    def test_execute(self, mock_apply, mock_fmt):
        mock_apply.return_value = {"created": 3}
        mock_fmt.return_value = {"created": 3, "errors": []}
        tools = _register()
        result = json.loads(tools["backfill_execute_task_sessions"](dry_run=False))
        assert result["mode"] == "EXECUTED"

    @patch("governance.evidence_scanner.apply_task_session_linkages",
           side_effect=Exception("db error"))
    def test_exception(self, mock_apply):
        tools = _register()
        result = json.loads(tools["backfill_execute_task_sessions"]())
        assert "error" in result


# ── backfill_scan_evidence_sessions ─────────────────────

class TestBackfillScanEvidenceSessions:
    @patch("governance.evidence_scanner.format_evidence_link_summary")
    @patch("governance.evidence_scanner.scan_evidence_session_links")
    def test_success(self, mock_scan, mock_fmt):
        mock_scan.return_value = []
        mock_fmt.return_value = {"total_files": 0}
        tools = _register()
        result = json.loads(tools["backfill_scan_evidence_sessions"]())
        assert "total_files" in result

    @patch("governance.evidence_scanner.scan_evidence_session_links",
           side_effect=Exception("io error"))
    def test_exception(self, mock_scan):
        tools = _register()
        result = json.loads(tools["backfill_scan_evidence_sessions"]())
        assert "error" in result


# ── backfill_execute_evidence_sessions ──────────────────

class TestBackfillExecuteEvidenceSessions:
    @patch("governance.evidence_scanner.format_evidence_link_summary")
    @patch("governance.evidence_scanner.apply_evidence_session_links")
    def test_dry_run(self, mock_apply, mock_fmt):
        mock_apply.return_value = {"linked": 0}
        mock_fmt.return_value = {"linked": 0}
        tools = _register()
        result = json.loads(tools["backfill_execute_evidence_sessions"](dry_run=True))
        assert result["mode"] == "DRY_RUN"

    @patch("governance.evidence_scanner.format_evidence_link_summary")
    @patch("governance.evidence_scanner.apply_evidence_session_links")
    def test_execute(self, mock_apply, mock_fmt):
        mock_apply.return_value = {"linked": 5}
        mock_fmt.return_value = {"linked": 5}
        tools = _register()
        result = json.loads(tools["backfill_execute_evidence_sessions"](dry_run=False))
        assert result["mode"] == "EXECUTED"
        assert result["linked"] == 5

    @patch("governance.evidence_scanner.apply_evidence_session_links",
           side_effect=Exception("fail"))
    def test_exception(self, mock_apply):
        tools = _register()
        result = json.loads(tools["backfill_execute_evidence_sessions"]())
        assert "error" in result


# ── backfill_scan_all_evidence ──────────────────────────

@dataclass
class _FakeScanResult:
    session_id: str = "SESSION-2026-01-01-TEST"
    file_path: str = "evidence/SESSION-2026-01-01-TEST.md"
    task_refs: set = field(default_factory=lambda: {"T-1", "T-2"})
    rule_refs: set = field(default_factory=lambda: {"RULE-001"})
    gap_refs: set = field(default_factory=lambda: {"GAP-AUTH-001"})


class TestBackfillScanAllEvidence:
    @patch("governance.evidence_scanner.scan_all_evidence_files")
    def test_success(self, mock_scan):
        mock_scan.return_value = [_FakeScanResult()]
        tools = _register()
        result = json.loads(tools["backfill_scan_all_evidence"]())
        assert result["total_files"] == 1
        assert result["totals"]["task_refs"] == 2
        assert result["totals"]["rule_refs"] == 1
        assert result["totals"]["gap_refs"] == 1

    @patch("governance.evidence_scanner.scan_all_evidence_files")
    def test_empty(self, mock_scan):
        mock_scan.return_value = []
        tools = _register()
        result = json.loads(tools["backfill_scan_all_evidence"]())
        assert result["total_files"] == 0

    @patch("governance.evidence_scanner.scan_all_evidence_files")
    def test_truncates_refs(self, mock_scan):
        sr = _FakeScanResult()
        sr.task_refs = {f"T-{i}" for i in range(10)}
        mock_scan.return_value = [sr]
        tools = _register()
        result = json.loads(tools["backfill_scan_all_evidence"]())
        assert len(result["files"][0]["tasks"]) == 5  # Truncated to 5

    @patch("governance.evidence_scanner.scan_all_evidence_files",
           side_effect=Exception("scan crash"))
    def test_exception(self, mock_scan):
        tools = _register()
        result = json.loads(tools["backfill_scan_all_evidence"]())
        assert "error" in result
