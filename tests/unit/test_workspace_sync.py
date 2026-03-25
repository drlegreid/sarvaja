"""
Unit tests for Workspace Sync Status MCP Tools.

Per DOC-SIZE-01-v1: Tests for governance/mcp_tools/workspace_sync.py module.
Tests: register_workspace_sync_tools — governance_sync_status,
       workspace_sync_status, workspace_sync_gaps_to_typedb.
"""

import json
from unittest.mock import patch, MagicMock

import pytest


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


_P = "governance.mcp_tools.workspace_sync"


@pytest.fixture()
def sync_tools():
    from governance.mcp_tools.workspace_sync import register_workspace_sync_tools
    mcp = _CaptureMCP()
    register_workspace_sync_tools(mcp)
    return mcp.tools


@pytest.fixture(autouse=True)
def _mock_format():
    with patch(f"{_P}.format_mcp_result", side_effect=json.dumps):
        yield


# ── governance_sync_status ─────────────────────────────────────


class TestGovernanceSyncStatus:
    def test_all_synced(self, sync_tools, tmp_path):
        mock_client = MagicMock()
        mock_rule = MagicMock()
        mock_rule.id = "R-1"
        mock_client.get_all_rules.return_value = [mock_rule]
        mock_client.get_all_tasks.return_value = []
        mock_client.get_all_sessions.return_value = []

        mock_doc = MagicMock()
        mock_doc.rule_ids = {"R-1"}

        evidence_dir = tmp_path / "evidence"
        evidence_dir.mkdir()

        with patch("governance.client.TypeDBClient", return_value=mock_client, create=True), \
             patch("governance.rule_linker.scan_rule_documents", return_value=[mock_doc], create=True), \
             patch("governance.workspace_scanner.WORKSPACE_ROOT", str(tmp_path), create=True), \
             patch("governance.workspace_scanner.scan_workspace", return_value=[], create=True):
            result = json.loads(sync_tools["governance_sync_status"]())

        assert result["rules"]["synced"] is True
        assert result["sync_needed"] is False

    def test_rules_divergence(self, sync_tools, tmp_path):
        mock_client = MagicMock()
        r1 = MagicMock(); r1.id = "R-1"
        r2 = MagicMock(); r2.id = "R-2"
        mock_client.get_all_rules.return_value = [r1, r2]
        mock_client.get_all_tasks.return_value = []
        mock_client.get_all_sessions.return_value = []

        mock_doc = MagicMock()
        mock_doc.rule_ids = {"R-1", "R-3"}  # R-3 in files but not TypeDB

        with patch("governance.client.TypeDBClient", return_value=mock_client, create=True), \
             patch("governance.rule_linker.scan_rule_documents", return_value=[mock_doc], create=True), \
             patch("governance.workspace_scanner.WORKSPACE_ROOT", str(tmp_path), create=True), \
             patch("governance.workspace_scanner.scan_workspace", return_value=[], create=True):
            result = json.loads(sync_tools["governance_sync_status"]())

        assert result["rules"]["synced"] is False
        assert "R-3" in result["rules"]["missing_in_typedb"]
        assert "R-2" in result["rules"]["missing_in_files"]
        assert result["sync_needed"] is True

    def test_tasks_status_mismatch(self, sync_tools, tmp_path):
        mock_client = MagicMock()
        mock_client.get_all_rules.return_value = []
        mock_client.get_all_sessions.return_value = []
        t1 = MagicMock(); t1.id = "T-1"; t1.status = "OPEN"
        mock_client.get_all_tasks.return_value = [t1]

        file_task = MagicMock()
        file_task.task_id = "T-1"
        file_task.status = "DONE"

        mock_doc = MagicMock()
        mock_doc.rule_ids = set()

        with patch("governance.client.TypeDBClient", return_value=mock_client, create=True), \
             patch("governance.rule_linker.scan_rule_documents", return_value=[mock_doc], create=True), \
             patch("governance.workspace_scanner.WORKSPACE_ROOT", str(tmp_path), create=True), \
             patch("governance.workspace_scanner.scan_workspace", return_value=[file_task], create=True):
            result = json.loads(sync_tools["governance_sync_status"]())

        assert result["tasks"]["synced"] is False
        assert len(result["tasks"]["status_mismatches"]) == 1

    def test_partial_failure_still_returns(self, sync_tools, tmp_path):
        """Verify individual section failures don't crash the whole report."""
        mock_client = MagicMock()
        mock_client.get_all_rules.side_effect = Exception("rules fail")
        mock_client.get_all_tasks.return_value = []
        mock_client.get_all_sessions.return_value = []
        mock_doc = MagicMock(); mock_doc.rule_ids = set()

        with patch("governance.client.TypeDBClient", return_value=mock_client, create=True), \
             patch("governance.rule_linker.scan_rule_documents", return_value=[mock_doc], create=True), \
             patch("governance.workspace_scanner.WORKSPACE_ROOT", str(tmp_path), create=True), \
             patch("governance.workspace_scanner.scan_workspace", return_value=[], create=True):
            result = json.loads(sync_tools["governance_sync_status"]())

        assert result["rules"]["typedb_count"] == 0  # failed, stayed at default

    def test_evidence_files_counted(self, sync_tools, tmp_path):
        mock_client = MagicMock()
        mock_client.get_all_rules.return_value = []
        mock_client.get_all_tasks.return_value = []
        mock_client.get_all_sessions.return_value = [MagicMock()]

        evidence_dir = tmp_path / "evidence"
        evidence_dir.mkdir()
        (evidence_dir / "SESSION-2026-02-11-TEST.md").write_text("# test")
        (evidence_dir / "other.md").write_text("# not session")

        mock_doc = MagicMock(); mock_doc.rule_ids = set()

        with patch("governance.client.TypeDBClient", return_value=mock_client, create=True), \
             patch("governance.rule_linker.scan_rule_documents", return_value=[mock_doc], create=True), \
             patch("governance.workspace_scanner.WORKSPACE_ROOT", str(tmp_path), create=True), \
             patch("governance.workspace_scanner.scan_workspace", return_value=[], create=True):
            result = json.loads(sync_tools["governance_sync_status"]())

        assert result["sessions"]["evidence_files"] == 1
        assert result["sessions"]["typedb_count"] == 1


# ── workspace_sync_status ──────────────────────────────────────


class TestWorkspaceSyncStatus:
    def test_alias(self, sync_tools, tmp_path):
        mock_client = MagicMock()
        mock_client.get_all_rules.return_value = []
        mock_client.get_all_tasks.return_value = []
        mock_client.get_all_sessions.return_value = []
        mock_doc = MagicMock(); mock_doc.rule_ids = set()

        with patch("governance.client.TypeDBClient", return_value=mock_client, create=True), \
             patch("governance.rule_linker.scan_rule_documents", return_value=[mock_doc], create=True), \
             patch("governance.workspace_scanner.WORKSPACE_ROOT", str(tmp_path), create=True), \
             patch("governance.workspace_scanner.scan_workspace", return_value=[], create=True):
            result = json.loads(sync_tools["workspace_sync_status"]())

        assert "sync_needed" in result


# ── workspace_sync_gaps_to_typedb ──────────────────────────────


class TestSyncGapsToTypedb:
    def test_dry_run_insert(self, sync_tools):
        mock_gap = MagicMock()
        mock_gap.id = "GAP-001"
        mock_gap.is_resolved = False
        mock_gap.description = "Test gap"
        mock_gap.priority = "high"

        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = []
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("governance.utils.gap_parser.GapParser", create=True) as MockParser, \
             patch("governance.mcp_tools.common.typedb_client", return_value=mock_client, create=True):
            MockParser.return_value.parse.return_value = [mock_gap]
            result = json.loads(sync_tools["workspace_sync_gaps_to_typedb"](dry_run=True))

        assert result["dry_run"] is True
        assert len(result["to_insert"]) == 1
        assert result["to_insert"][0]["gap_id"] == "GAP-001"

    def test_dry_run_update(self, sync_tools):
        mock_gap = MagicMock()
        mock_gap.id = "GAP-002"
        mock_gap.is_resolved = True
        mock_gap.description = "Resolved"
        mock_gap.priority = "low"

        existing = MagicMock()
        existing.id = "GAP-002"
        existing.status = "OPEN"

        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [existing]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("governance.utils.gap_parser.GapParser", create=True) as MockParser, \
             patch("governance.mcp_tools.common.typedb_client", return_value=mock_client, create=True):
            MockParser.return_value.parse.return_value = [mock_gap]
            result = json.loads(sync_tools["workspace_sync_gaps_to_typedb"](dry_run=True))

        assert len(result["to_update"]) == 1
        assert result["to_update"][0]["new_status"] == "DONE"

    def test_skipped_when_synced(self, sync_tools):
        mock_gap = MagicMock()
        mock_gap.id = "GAP-003"
        mock_gap.is_resolved = False

        existing = MagicMock()
        existing.id = "GAP-003"
        existing.status = "OPEN"

        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [existing]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("governance.utils.gap_parser.GapParser", create=True) as MockParser, \
             patch("governance.mcp_tools.common.typedb_client", return_value=mock_client, create=True):
            MockParser.return_value.parse.return_value = [mock_gap]
            result = json.loads(sync_tools["workspace_sync_gaps_to_typedb"](dry_run=True))

        assert "GAP-003" in result["skipped"]

    def test_exception(self, sync_tools):
        with patch("governance.utils.gap_parser.GapParser", side_effect=Exception("fail"), create=True):
            result = json.loads(sync_tools["workspace_sync_gaps_to_typedb"]())
        assert "error" in result
