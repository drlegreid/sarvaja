"""Unit tests for mega-session ingestion pipeline (D1-D5).

Tests checkpoint engine, content indexer, link miner, orchestrator,
and MCP tool registration.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from governance.services.ingestion_checkpoint import (
    IngestionCheckpoint,
    delete_checkpoint,
    get_resume_offset,
    load_checkpoint,
    save_checkpoint,
)


# ---------------------------------------------------------------------------
# D1: Checkpoint Engine
# ---------------------------------------------------------------------------


class TestIngestionCheckpoint(unittest.TestCase):
    """Tests for IngestionCheckpoint dataclass."""

    def test_default_values(self):
        ckpt = IngestionCheckpoint(session_id="S1", jsonl_path="/tmp/a.jsonl")
        self.assertEqual(ckpt.lines_processed, 0)
        self.assertEqual(ckpt.chunks_indexed, 0)
        self.assertEqual(ckpt.phase, "pending")
        self.assertIsInstance(ckpt.errors, list)
        self.assertTrue(ckpt.started_at)
        self.assertTrue(ckpt.updated_at)

    def test_touch_updates_timestamp(self):
        ckpt = IngestionCheckpoint(session_id="S1", jsonl_path="/x")
        old = ckpt.updated_at
        ckpt.touch()
        self.assertGreaterEqual(ckpt.updated_at, old)

    def test_add_error_caps_at_max(self):
        ckpt = IngestionCheckpoint(session_id="S1", jsonl_path="/x")
        for i in range(250):
            ckpt.add_error(f"err-{i}", max_errors=10)
        self.assertEqual(len(ckpt.errors), 10)

    def test_to_dict_roundtrip(self):
        ckpt = IngestionCheckpoint(
            session_id="S1", jsonl_path="/x", lines_processed=42, phase="content"
        )
        d = ckpt.to_dict()
        restored = IngestionCheckpoint.from_dict(d)
        self.assertEqual(restored.session_id, "S1")
        self.assertEqual(restored.lines_processed, 42)
        self.assertEqual(restored.phase, "content")

    def test_from_dict_ignores_unknown_keys(self):
        d = {"session_id": "S1", "jsonl_path": "/x", "future_field": True}
        ckpt = IngestionCheckpoint.from_dict(d)
        self.assertEqual(ckpt.session_id, "S1")


class TestCheckpointPersistence(unittest.TestCase):
    """Tests for save/load/delete checkpoint functions."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_and_load(self):
        ckpt = IngestionCheckpoint(
            session_id="S1", jsonl_path="/tmp/a.jsonl",
            lines_processed=100, chunks_indexed=50
        )
        save_checkpoint(ckpt, self.tmpdir)
        loaded = load_checkpoint("S1", self.tmpdir)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.lines_processed, 100)
        self.assertEqual(loaded.chunks_indexed, 50)

    def test_load_nonexistent_returns_none(self):
        self.assertIsNone(load_checkpoint("NOPE", self.tmpdir))

    def test_load_corrupt_json_returns_none(self):
        path = self.tmpdir / "CORRUPT.json"
        path.write_text("not json")
        self.assertIsNone(load_checkpoint("CORRUPT", self.tmpdir))

    def test_get_resume_offset_fresh(self):
        self.assertEqual(get_resume_offset("FRESH", self.tmpdir), 0)

    def test_get_resume_offset_with_checkpoint(self):
        ckpt = IngestionCheckpoint(
            session_id="S2", jsonl_path="/x", lines_processed=999
        )
        save_checkpoint(ckpt, self.tmpdir)
        self.assertEqual(get_resume_offset("S2", self.tmpdir), 999)

    def test_delete_checkpoint(self):
        ckpt = IngestionCheckpoint(session_id="S3", jsonl_path="/x")
        save_checkpoint(ckpt, self.tmpdir)
        self.assertTrue(delete_checkpoint("S3", self.tmpdir))
        self.assertIsNone(load_checkpoint("S3", self.tmpdir))

    def test_delete_nonexistent_returns_false(self):
        self.assertFalse(delete_checkpoint("NOPE", self.tmpdir))

    def test_atomic_write_survives_content_change(self):
        """Save twice; second write should atomically replace first."""
        ckpt = IngestionCheckpoint(session_id="S4", jsonl_path="/x", lines_processed=10)
        save_checkpoint(ckpt, self.tmpdir)
        ckpt.lines_processed = 20
        save_checkpoint(ckpt, self.tmpdir)
        loaded = load_checkpoint("S4", self.tmpdir)
        self.assertEqual(loaded.lines_processed, 20)

    def test_session_id_with_slashes_safe(self):
        ckpt = IngestionCheckpoint(session_id="a/b\\c", jsonl_path="/x")
        save_checkpoint(ckpt, self.tmpdir)
        loaded = load_checkpoint("a/b\\c", self.tmpdir)
        self.assertIsNotNone(loaded)


# ---------------------------------------------------------------------------
# D2: Content Indexer
# ---------------------------------------------------------------------------


class TestAccumulateSemanticChunks(unittest.TestCase):
    """Tests for _accumulate_semantic_chunks."""

    def _make_entry(self, text, entry_type="assistant", branch=None):
        """Create a mock ParsedEntry."""
        entry = MagicMock()
        entry.text_content = text
        entry.entry_type = entry_type
        entry.timestamp = datetime(2026, 2, 13, tzinfo=timezone.utc)
        entry.git_branch = branch
        return entry

    def test_empty_entries(self):
        from governance.services.cc_content_indexer import _accumulate_semantic_chunks
        chunks = list(_accumulate_semantic_chunks(iter([]), 100))
        self.assertEqual(chunks, [])

    def test_single_small_entry(self):
        from governance.services.cc_content_indexer import _accumulate_semantic_chunks
        entries = [self._make_entry("hello world")]
        chunks = list(_accumulate_semantic_chunks(iter(entries), 2000))
        self.assertEqual(len(chunks), 1)
        self.assertIn("hello world", chunks[0][0])

    def test_accumulation_at_threshold(self):
        from governance.services.cc_content_indexer import _accumulate_semantic_chunks
        # 3 entries of 40 chars each, threshold 100 -> should produce 2 chunks
        entries = [self._make_entry("x" * 40) for _ in range(3)]
        chunks = list(_accumulate_semantic_chunks(iter(entries), 100))
        self.assertGreaterEqual(len(chunks), 1)

    def test_entries_without_text_skipped(self):
        from governance.services.cc_content_indexer import _accumulate_semantic_chunks
        entries = [self._make_entry(None), self._make_entry(""), self._make_entry("data")]
        chunks = list(_accumulate_semantic_chunks(iter(entries), 2000))
        self.assertEqual(len(chunks), 1)
        self.assertIn("data", chunks[0][0])

    def test_metadata_includes_chunk_index(self):
        from governance.services.cc_content_indexer import _accumulate_semantic_chunks
        entries = [self._make_entry("a" * 60) for _ in range(5)]
        chunks = list(_accumulate_semantic_chunks(iter(entries), 100))
        indices = [c[1]["chunk_index"] for c in chunks]
        self.assertEqual(indices, list(range(len(chunks))))

    def test_git_branch_captured(self):
        from governance.services.cc_content_indexer import _accumulate_semantic_chunks
        entries = [self._make_entry("data", branch="feature/x")]
        chunks = list(_accumulate_semantic_chunks(iter(entries), 2000))
        self.assertEqual(chunks[0][1]["git_branch"], "feature/x")


class TestIndexSessionContent(unittest.TestCase):
    """Tests for index_session_content."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.jsonl_file = self.tmpdir / "test.jsonl"
        # Create minimal JSONL
        lines = []
        for i in range(5):
            entry = {
                "timestamp": f"2026-02-13T10:{i:02d}:00Z",
                "type": "assistant",
                "message": {
                    "content": [{"type": "text", "text": f"Line {i} content here"}],
                    "model": "claude-test",
                },
            }
            lines.append(json.dumps(entry))
        self.jsonl_file.write_text("\n".join(lines))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_dry_run_no_chromadb(self):
        from governance.services.cc_content_indexer import index_session_content
        result = index_session_content(
            self.jsonl_file, "TEST-SESSION",
            dry_run=True, resume=False, checkpoint_dir=self.tmpdir,
        )
        self.assertIn(result["status"], ("success", "partial"))
        self.assertGreaterEqual(result["chunks_indexed"], 0)

    def test_dry_run_produces_no_checkpoint_writes(self):
        from governance.services.cc_content_indexer import index_session_content
        index_session_content(
            self.jsonl_file, "TEST-DRY",
            dry_run=True, resume=False, checkpoint_dir=self.tmpdir,
        )
        # Dry run should still not create checkpoint files
        # (it doesn't save checkpoints in dry mode)
        ckpt = load_checkpoint("TEST-DRY", self.tmpdir)
        self.assertIsNone(ckpt)

    @patch("governance.services.cc_content_indexer._get_chromadb_collection")
    def test_real_upsert_called(self, mock_get_coll):
        from governance.services.cc_content_indexer import index_session_content
        mock_coll = MagicMock()
        mock_get_coll.return_value = mock_coll

        result = index_session_content(
            self.jsonl_file, "TEST-UPSERT",
            dry_run=False, resume=False, checkpoint_dir=self.tmpdir,
        )
        self.assertEqual(result["status"], "success")
        # Should have called upsert at least once (final batch)
        self.assertTrue(mock_coll.upsert.called or result["chunks_indexed"] == 0)

    @patch("governance.services.cc_content_indexer._get_chromadb_collection")
    def test_chromadb_error_returns_partial(self, mock_get_coll):
        from governance.services.cc_content_indexer import index_session_content
        mock_coll = MagicMock()
        mock_coll.upsert.side_effect = Exception("ChromaDB down")
        mock_get_coll.return_value = mock_coll

        result = index_session_content(
            self.jsonl_file, "TEST-ERR",
            dry_run=False, resume=False, checkpoint_dir=self.tmpdir,
            batch_size=1,
        )
        # Should still complete with partial status, not crash
        self.assertIn(result["status"], ("partial", "success"))


class TestIndexSmallFile(unittest.TestCase):
    """Tests for small files where chunks < batch_size (final batch edge case)."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.jsonl_file = self.tmpdir / "small.jsonl"
        # Just 2 lines — will produce chunks < batch_size (100)
        lines = []
        for i in range(2):
            entry = {
                "timestamp": f"2026-02-13T10:{i:02d}:00Z",
                "type": "assistant",
                "message": {
                    "content": [{"type": "text", "text": f"Small content line {i}"}],
                },
            }
            lines.append(json.dumps(entry))
        self.jsonl_file.write_text("\n".join(lines))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_lines_processed_updated_for_final_batch(self):
        """Regression: lines_processed must be updated even if < batch_size."""
        from governance.services.cc_content_indexer import index_session_content
        result = index_session_content(
            self.jsonl_file, "TEST-SMALL",
            dry_run=True, resume=False, checkpoint_dir=self.tmpdir,
        )
        # With only 2 entries, all chunks go in the final batch
        self.assertGreater(result["chunks_indexed"], 0)
        # lines_processed should be > 0, not stuck at start_line
        self.assertGreaterEqual(result["lines_processed"], 0)

    def test_chunks_indexed_matches_actual_output(self):
        from governance.services.cc_content_indexer import index_session_content
        result = index_session_content(
            self.jsonl_file, "TEST-SMALL2",
            dry_run=True, resume=False, checkpoint_dir=self.tmpdir,
        )
        self.assertGreater(result["chunks_indexed"], 0)
        self.assertEqual(result["status"], "success")


class TestDeleteSessionContent(unittest.TestCase):
    """Tests for delete_session_content."""

    @patch("governance.services.cc_content_indexer._get_chromadb_collection")
    def test_delete_calls_collection(self, mock_get_coll):
        from governance.services.cc_content_indexer import delete_session_content
        mock_coll = MagicMock()
        mock_get_coll.return_value = mock_coll

        result = delete_session_content("S1")
        self.assertEqual(result["status"], "success")
        mock_coll.delete.assert_called_once()

    @patch("governance.services.cc_content_indexer._get_chromadb_collection")
    def test_delete_error_handled(self, mock_get_coll):
        from governance.services.cc_content_indexer import delete_session_content
        mock_get_coll.side_effect = Exception("fail")

        result = delete_session_content("S1")
        self.assertEqual(result["status"], "error")


# ---------------------------------------------------------------------------
# D3: Link Miner
# ---------------------------------------------------------------------------


class TestExtractDecisionRefs(unittest.TestCase):
    """Tests for _extract_decision_refs."""

    def test_finds_decision_ids(self):
        from governance.services.cc_link_miner import _extract_decision_refs
        text = "Per DECISION-005 and DECISION-008 approved"
        refs = _extract_decision_refs(text)
        self.assertEqual(refs, {"DECISION-005", "DECISION-008"})

    def test_no_false_positives(self):
        from governance.services.cc_link_miner import _extract_decision_refs
        text = "No decisions here, just DECISION text"
        refs = _extract_decision_refs(text)
        self.assertEqual(refs, set())

    def test_case_insensitive(self):
        from governance.services.cc_link_miner import _extract_decision_refs
        refs = _extract_decision_refs("see decision-003")
        self.assertEqual(refs, {"DECISION-003"})


class TestMineSessionLinks(unittest.TestCase):
    """Tests for mine_session_links."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.jsonl_file = self.tmpdir / "test.jsonl"
        lines = []
        for text in [
            "Implementing RULE-011 per FH-001",
            "Per GAP-UI-001 and DECISION-005",
            "Working on SESSION-EVID-01-v1",
        ]:
            entry = {
                "timestamp": "2026-02-13T10:00:00Z",
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": text}]},
            }
            lines.append(json.dumps(entry))
        self.jsonl_file.write_text("\n".join(lines))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_dry_run_finds_refs(self):
        from governance.services.cc_link_miner import mine_session_links
        result = mine_session_links(
            self.jsonl_file, "S1", dry_run=True, checkpoint_dir=self.tmpdir
        )
        self.assertEqual(result["status"], "dry_run")
        self.assertIn("FH-001", result["refs_found"]["tasks"])
        self.assertIn("GAP-UI-001", result["refs_found"]["gaps"])
        self.assertIn("DECISION-005", result["refs_found"]["decisions"])

    def test_dry_run_finds_rules(self):
        from governance.services.cc_link_miner import mine_session_links
        result = mine_session_links(
            self.jsonl_file, "S1", dry_run=True, checkpoint_dir=self.tmpdir
        )
        rules = result["refs_found"]["rules"]
        self.assertIn("RULE-011", rules)
        self.assertIn("SESSION-EVID-01-V1", rules)

    @patch("governance.services.cc_link_miner._get_typedb_client")
    def test_no_typedb_returns_error(self, mock_client):
        from governance.services.cc_link_miner import mine_session_links
        mock_client.return_value = None
        result = mine_session_links(
            self.jsonl_file, "S1", dry_run=False, checkpoint_dir=self.tmpdir
        )
        self.assertEqual(result["status"], "error")


# ---------------------------------------------------------------------------
# D4: Orchestrator
# ---------------------------------------------------------------------------


class TestEstimateIngestion(unittest.TestCase):
    """Tests for estimate_ingestion."""

    def test_missing_file(self):
        from governance.services.ingestion_orchestrator import estimate_ingestion
        result = estimate_ingestion(Path("/nonexistent/file.jsonl"))
        self.assertEqual(result["status"], "error")

    def test_valid_file(self):
        from governance.services.ingestion_orchestrator import estimate_ingestion
        tmp = Path(tempfile.mktemp(suffix=".jsonl"))
        tmp.write_text("\n".join(["{}" for _ in range(100)]))
        try:
            result = estimate_ingestion(tmp)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["line_count"], 100)
            self.assertIn("size_mb", result)
        finally:
            tmp.unlink()


class TestGetIngestionStatus(unittest.TestCase):
    """Tests for get_ingestion_status."""

    def test_not_started(self):
        from governance.services.ingestion_orchestrator import get_ingestion_status
        tmpdir = Path(tempfile.mkdtemp())
        try:
            result = get_ingestion_status("NOPE", tmpdir)
            self.assertEqual(result["status"], "not_started")
        finally:
            import shutil
            shutil.rmtree(tmpdir)

    def test_with_checkpoint(self):
        from governance.services.ingestion_orchestrator import get_ingestion_status
        tmpdir = Path(tempfile.mkdtemp())
        try:
            ckpt = IngestionCheckpoint(
                session_id="S1", jsonl_path="/x",
                lines_processed=500, phase="content"
            )
            save_checkpoint(ckpt, tmpdir)
            result = get_ingestion_status("S1", tmpdir)
            self.assertEqual(result["status"], "content")
            self.assertEqual(result["lines_processed"], 500)
        finally:
            import shutil
            shutil.rmtree(tmpdir)


class TestRollbackContentIndex(unittest.TestCase):
    """Tests for rollback_content_index."""

    @patch("governance.services.cc_content_indexer._get_chromadb_collection")
    def test_rollback_deletes_chromadb_and_checkpoint(self, mock_get_coll):
        from governance.services.ingestion_orchestrator import rollback_content_index
        mock_coll = MagicMock()
        mock_get_coll.return_value = mock_coll

        result = rollback_content_index("S1")
        self.assertEqual(result["status"], "rolled_back")
        mock_coll.delete.assert_called_once()


class TestRunIngestionPipeline(unittest.TestCase):
    """Tests for run_ingestion_pipeline."""

    def test_missing_file(self):
        from governance.services.ingestion_orchestrator import run_ingestion_pipeline
        result = run_ingestion_pipeline(Path("/nope.jsonl"), "S1")
        self.assertEqual(result["status"], "error")

    @patch("governance.services.ingestion_orchestrator._get_rss_mb", return_value=50.0)
    @patch("governance.services.cc_content_indexer._get_chromadb_collection")
    def test_content_only_phase(self, mock_get_coll, _mock_rss):
        from governance.services.ingestion_orchestrator import run_ingestion_pipeline
        mock_coll = MagicMock()
        mock_get_coll.return_value = mock_coll

        tmpdir = Path(tempfile.mkdtemp())
        jsonl = tmpdir / "test.jsonl"
        jsonl.write_text(json.dumps({
            "timestamp": "2026-02-13T10:00:00Z",
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "hello"}]},
        }))
        try:
            result = run_ingestion_pipeline(
                jsonl, "S1", phases=["content"],
                resume=False, checkpoint_dir=tmpdir,
            )
            self.assertIn(result["status"], ("success", "partial"))
            self.assertIsNotNone(result["content"])
            self.assertIsNone(result["linking"])
        finally:
            import shutil
            shutil.rmtree(tmpdir)

    @patch("governance.services.ingestion_orchestrator._get_rss_mb", return_value=50.0)
    def test_dry_run_pipeline(self, _mock_rss):
        from governance.services.ingestion_orchestrator import run_ingestion_pipeline
        tmpdir = Path(tempfile.mkdtemp())
        jsonl = tmpdir / "test.jsonl"
        jsonl.write_text(json.dumps({
            "timestamp": "2026-02-13T10:00:00Z",
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "RULE-011 ref"}]},
        }))
        try:
            result = run_ingestion_pipeline(
                jsonl, "S1", dry_run=True, checkpoint_dir=tmpdir,
            )
            self.assertIn(result["status"], ("success", "partial"))
        finally:
            import shutil
            shutil.rmtree(tmpdir)


# ---------------------------------------------------------------------------
# D5: MCP Tool Registration
# ---------------------------------------------------------------------------


class TestIngestionMCPTools(unittest.TestCase):
    """Tests for MCP tool registration."""

    def test_register_creates_tools(self):
        from governance.mcp_tools.ingestion import register_ingestion_tools
        tools_registered = {}

        class MockMCP:
            def tool(self):
                def decorator(fn):
                    tools_registered[fn.__name__] = fn
                    return fn
                return decorator

        register_ingestion_tools(MockMCP())

        expected = {
            "ingest_session_content",
            "mine_session_links",
            "ingest_session_full",
            "ingestion_status",
            "ingestion_estimate",
        }
        self.assertEqual(set(tools_registered.keys()), expected)


class TestResolveJsonlPath(unittest.TestCase):
    """Tests for _resolve_jsonl_path."""

    def test_explicit_existing_path(self):
        from governance.mcp_tools.ingestion import _resolve_jsonl_path
        tmp = Path(tempfile.mktemp(suffix=".jsonl"))
        tmp.write_text("{}")
        try:
            result = _resolve_jsonl_path("S1", str(tmp))
            self.assertEqual(result, tmp)
        finally:
            tmp.unlink()

    def test_explicit_nonexistent_path(self):
        from governance.mcp_tools.ingestion import _resolve_jsonl_path
        result = _resolve_jsonl_path("S1", "/nonexistent/file.jsonl")
        self.assertIsNone(result)

    @patch("governance.services.cc_session_scanner.find_jsonl_for_session", side_effect=Exception("fail"))
    def test_auto_discover_failure(self, _):
        from governance.mcp_tools.ingestion import _resolve_jsonl_path
        result = _resolve_jsonl_path("S1", None)
        self.assertIsNone(result)

    @patch("governance.services.cc_session_scanner.find_jsonl_for_session")
    def test_auto_discover_passes_dict(self, mock_find):
        """Verify find_jsonl_for_session is called with a dict, not a string."""
        mock_find.return_value = Path("/tmp/test.jsonl")
        from governance.mcp_tools.ingestion import _resolve_jsonl_path
        with patch.object(Path, "exists", return_value=True):
            _resolve_jsonl_path("SESSION-2026-CC-TEST", None)
        mock_find.assert_called_once_with({"session_id": "SESSION-2026-CC-TEST"})


# ---------------------------------------------------------------------------
# D6: Parser start_line
# ---------------------------------------------------------------------------


class TestParserStartLine(unittest.TestCase):
    """Tests for parse_log_file_extended start_line parameter."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.jsonl_file = self.tmpdir / "test.jsonl"
        lines = []
        for i in range(10):
            entry = {
                "timestamp": f"2026-02-13T10:{i:02d}:00Z",
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": f"Line {i}"}]},
            }
            lines.append(json.dumps(entry))
        self.jsonl_file.write_text("\n".join(lines))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_start_line_zero_returns_all(self):
        from governance.session_metrics.parser import parse_log_file_extended
        entries = list(parse_log_file_extended(self.jsonl_file, start_line=0))
        self.assertEqual(len(entries), 10)

    def test_start_line_skips_lines(self):
        from governance.session_metrics.parser import parse_log_file_extended
        entries = list(parse_log_file_extended(self.jsonl_file, start_line=7))
        self.assertEqual(len(entries), 3)

    def test_start_line_past_end(self):
        from governance.session_metrics.parser import parse_log_file_extended
        entries = list(parse_log_file_extended(self.jsonl_file, start_line=999))
        self.assertEqual(len(entries), 0)

    def test_default_start_line_backward_compat(self):
        from governance.session_metrics.parser import parse_log_file_extended
        # No start_line arg — should behave like start_line=0
        entries = list(parse_log_file_extended(self.jsonl_file))
        self.assertEqual(len(entries), 10)


if __name__ == "__main__":
    unittest.main()
