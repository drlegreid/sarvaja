"""
Unit tests for Session Content Ingestion MCP Tools.

Batch 151: Tests for governance/mcp_tools/ingestion.py
- ingest_session_content: content indexing
- mine_session_links: entity ref mining
- ingest_session_full: full pipeline
- ingestion_status: status check
- ingestion_estimate: file analysis
- _resolve_jsonl_path: path resolution
- _list_all_checkpoints: checkpoint listing
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.ingestion import (
    register_ingestion_tools,
    _resolve_jsonl_path,
    _list_all_checkpoints,
)


_MOD = "governance.mcp_tools.ingestion"


def _json_fmt(*args):
    if len(args) == 1:
        return json.dumps(args[0], indent=2, default=str)
    # format_mcp_result(status, data) variant
    return json.dumps(args[1] if len(args) > 1 else args[0], indent=2, default=str)


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
    register_ingestion_tools(mcp)
    return mcp.tools


@pytest.fixture(autouse=True)
def _force_json():
    with patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt):
        yield


# ── Registration ────────────────────────────────────────

class TestRegistration:
    def test_registers_five_tools(self):
        tools = _register()
        assert "ingest_session_content" in tools
        assert "mine_session_links" in tools
        assert "ingest_session_full" in tools
        assert "ingestion_status" in tools
        assert "ingestion_estimate" in tools


# ── _resolve_jsonl_path ─────────────────────────────────

class TestResolveJsonlPath:
    def test_explicit_path_exists(self):
        # BUG-299-ING-001: _resolve_jsonl_path validates path is under allowed dirs;
        # create temp file under project root so it passes validation.
        project_root = Path(__file__).resolve().parent.parent.parent
        f = project_root / "_test_resolve_mcp_tmp.jsonl"
        f.touch()
        try:
            result = _resolve_jsonl_path("S-1", str(f))
            assert result == f
        finally:
            f.unlink()

    def test_explicit_path_missing(self):
        result = _resolve_jsonl_path("S-1", "/nonexistent/file.jsonl")
        assert result is None

    @patch("governance.services.cc_session_scanner.find_jsonl_for_session")
    def test_auto_discovery(self, mock_find):
        mock_find.return_value = Path("/found/session.jsonl")
        result = _resolve_jsonl_path("S-1", None)
        assert result == Path("/found/session.jsonl")

    def test_auto_discovery_import_error(self):
        with patch.dict("sys.modules", {"governance.services.cc_session_scanner": None}):
            result = _resolve_jsonl_path("S-1", None)
            assert result is None


# ── ingest_session_content ──────────────────────────────

class TestIngestSessionContent:
    @patch(f"{_MOD}._resolve_jsonl_path", return_value=None)
    def test_file_not_found(self, mock_resolve):
        tools = _register()
        result = json.loads(tools["ingest_session_content"](session_id="S-1"))
        assert "error" in result

    @patch("governance.services.cc_content_indexer.index_session_content")
    @patch(f"{_MOD}._resolve_jsonl_path")
    def test_success(self, mock_resolve, mock_index):
        mock_resolve.return_value = Path("/data/session.jsonl")
        mock_index.return_value = {"chunks_indexed": 42, "status": "complete"}
        tools = _register()
        result = json.loads(tools["ingest_session_content"](
            session_id="S-1", dry_run=False))
        assert result["chunks_indexed"] == 42
        mock_index.assert_called_once()


# ── mine_session_links ──────────────────────────────────

class TestMineSessionLinks:
    @patch(f"{_MOD}._resolve_jsonl_path", return_value=None)
    def test_file_not_found(self, mock_resolve):
        tools = _register()
        result = json.loads(tools["mine_session_links"](session_id="S-1"))
        assert "error" in result

    @patch("governance.services.cc_link_miner.mine_session_links")
    @patch(f"{_MOD}._resolve_jsonl_path")
    def test_success(self, mock_resolve, mock_mine):
        mock_resolve.return_value = Path("/data/session.jsonl")
        mock_mine.return_value = {"tasks_linked": 5, "rules_linked": 3}
        tools = _register()
        result = json.loads(tools["mine_session_links"](
            session_id="S-1", dry_run=True))
        assert result["tasks_linked"] == 5


# ── ingest_session_full ─────────────────────────────────

class TestIngestSessionFull:
    @patch(f"{_MOD}._resolve_jsonl_path", return_value=None)
    def test_file_not_found(self, mock_resolve):
        tools = _register()
        result = json.loads(tools["ingest_session_full"](session_id="S-1"))
        assert "error" in result

    @patch("governance.services.ingestion_orchestrator.run_ingestion_pipeline")
    @patch(f"{_MOD}._resolve_jsonl_path")
    def test_success(self, mock_resolve, mock_pipeline):
        mock_resolve.return_value = Path("/data/session.jsonl")
        mock_pipeline.return_value = {"status": "complete", "phases": 2}
        tools = _register()
        result = json.loads(tools["ingest_session_full"](session_id="S-1"))
        assert result["status"] == "complete"


# ── ingestion_status ────────────────────────────────────

class TestIngestionStatus:
    @patch("governance.services.ingestion_orchestrator.get_ingestion_status")
    def test_specific_session(self, mock_status):
        mock_status.return_value = {"phase": "content", "lines": 1000}
        tools = _register()
        result = json.loads(tools["ingestion_status"](session_id="S-1"))
        assert result["phase"] == "content"

    @patch(f"{_MOD}._list_all_checkpoints")
    def test_empty_session_lists_all(self, mock_list):
        mock_list.return_value = json.dumps({"checkpoints": [], "count": 0})
        tools = _register()
        result = json.loads(tools["ingestion_status"](session_id=""))
        assert "checkpoints" in result


# ── _list_all_checkpoints ───────────────────────────────

_CP_MOD = "governance.services.ingestion_checkpoint"


class TestListAllCheckpoints:
    def test_nonexistent_dir(self):
        mock_dir = MagicMock()
        mock_dir.exists.return_value = False
        with patch(f"{_CP_MOD}._DEFAULT_CHECKPOINT_DIR", mock_dir):
            result = json.loads(_list_all_checkpoints())
            assert result["count"] == 0

    def test_with_checkpoint_files(self, tmp_path):
        cp_dir = tmp_path / "checkpoints"
        cp_dir.mkdir()
        (cp_dir / "S-1.json").write_text(json.dumps({
            "session_id": "S-1", "phase": "complete",
            "lines_processed": 100, "chunks_indexed": 10,
            "updated_at": "2026-01-01",
        }))
        with patch(f"{_CP_MOD}._DEFAULT_CHECKPOINT_DIR", cp_dir):
            result = json.loads(_list_all_checkpoints())
            assert result["count"] == 1
            assert result["checkpoints"][0]["session_id"] == "S-1"

    def test_skips_corrupt_json(self, tmp_path):
        cp_dir = tmp_path / "checkpoints"
        cp_dir.mkdir()
        (cp_dir / "bad.json").write_text("not json{{{")
        with patch(f"{_CP_MOD}._DEFAULT_CHECKPOINT_DIR", cp_dir):
            result = json.loads(_list_all_checkpoints())
            assert result["count"] == 0
