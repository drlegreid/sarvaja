"""
Tests for streaming content indexer (JSONL -> ChromaDB).

Batch 168: New coverage for governance/services/cc_content_indexer.py (0->18 tests).
"""
from dataclasses import dataclass
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


@dataclass
class _FakeEntry:
    text_content: str = ""
    entry_type: str = "assistant"
    timestamp: datetime | None = None
    git_branch: str = ""


class TestConstants:
    def test_content_collection_name(self):
        from governance.services.cc_content_indexer import CONTENT_COLLECTION
        assert CONTENT_COLLECTION == "sim_ai_session_content"

    def test_module_has_logger(self):
        from governance.services.cc_content_indexer import logger
        assert logger.name == "governance.services.cc_content_indexer"


class TestAccumulateSemanticChunks:
    def test_empty_entries(self):
        from governance.services.cc_content_indexer import _accumulate_semantic_chunks
        result = list(_accumulate_semantic_chunks(iter([]), chunk_size=100))
        assert result == []

    def test_single_small_entry(self):
        from governance.services.cc_content_indexer import _accumulate_semantic_chunks
        entries = iter([_FakeEntry(text_content="hello world")])
        result = list(_accumulate_semantic_chunks(entries, chunk_size=100))
        assert len(result) == 1
        text, meta = result[0]
        assert "hello world" in text
        assert meta["chunk_index"] == 0

    def test_chunk_boundary(self):
        from governance.services.cc_content_indexer import _accumulate_semantic_chunks
        entries = iter([
            _FakeEntry(text_content="a" * 60),
            _FakeEntry(text_content="b" * 60),
        ])
        result = list(_accumulate_semantic_chunks(entries, chunk_size=50))
        assert len(result) >= 2

    def test_metadata_includes_entry_types(self):
        from governance.services.cc_content_indexer import _accumulate_semantic_chunks
        entries = iter([
            _FakeEntry(text_content="hello", entry_type="assistant"),
        ])
        result = list(_accumulate_semantic_chunks(entries, chunk_size=2000))
        _, meta = result[0]
        assert "assistant" in meta["entry_types"]

    def test_skips_empty_text(self):
        from governance.services.cc_content_indexer import _accumulate_semantic_chunks
        entries = iter([
            _FakeEntry(text_content=""),
            _FakeEntry(text_content="valid"),
        ])
        result = list(_accumulate_semantic_chunks(entries, chunk_size=2000))
        assert len(result) == 1
        assert "valid" in result[0][0]

    def test_timestamp_captured(self):
        from governance.services.cc_content_indexer import _accumulate_semantic_chunks
        ts = datetime(2026, 2, 13, 10, 0)
        entries = iter([_FakeEntry(text_content="text", timestamp=ts)])
        result = list(_accumulate_semantic_chunks(entries, chunk_size=2000))
        _, meta = result[0]
        assert "2026-02-13" in meta["timestamp"]

    def test_git_branch_captured(self):
        from governance.services.cc_content_indexer import _accumulate_semantic_chunks
        entries = iter([_FakeEntry(text_content="text", git_branch="main")])
        result = list(_accumulate_semantic_chunks(entries, chunk_size=2000))
        _, meta = result[0]
        assert meta["git_branch"] == "main"

    def test_line_start_end_tracked(self):
        from governance.services.cc_content_indexer import _accumulate_semantic_chunks
        entries = iter([
            _FakeEntry(text_content="first"),
            _FakeEntry(text_content="second"),
        ])
        result = list(_accumulate_semantic_chunks(entries, chunk_size=2000))
        _, meta = result[0]
        assert meta["line_start"] == 0
        assert meta["line_end"] == 1


class TestIndexSessionContent:
    @patch("governance.services.cc_content_indexer.save_checkpoint")
    @patch("governance.services.cc_content_indexer.load_checkpoint", return_value=None)
    @patch("governance.services.cc_content_indexer.get_resume_offset", return_value=0)
    @patch("governance.services.cc_content_indexer.chunk_content")
    @patch("governance.session_metrics.parser.parse_log_file_extended")
    def test_dry_run_returns_results(self, mock_parse, mock_chunk, mock_offset, mock_load, mock_save):
        from governance.services.cc_content_indexer import index_session_content
        from pathlib import Path

        mock_parse.return_value = iter([_FakeEntry(text_content="test content")])
        mock_chunk.return_value = ["test content"]

        result = index_session_content(
            Path("/fake/path.jsonl"), "SESSION-TEST", dry_run=True
        )
        assert result["status"] == "success"
        assert isinstance(result["chunks_indexed"], int)
        assert isinstance(result["errors"], list)

    @patch("governance.services.cc_content_indexer.save_checkpoint")
    @patch("governance.services.cc_content_indexer.load_checkpoint", return_value=None)
    @patch("governance.services.cc_content_indexer.get_resume_offset", return_value=0)
    @patch("governance.services.cc_content_indexer._get_chromadb_collection")
    @patch("governance.services.cc_content_indexer.chunk_content")
    @patch("governance.session_metrics.parser.parse_log_file_extended")
    def test_chromadb_failure_returns_error(self, mock_parse, mock_chunk, mock_coll, mock_offset, mock_load, mock_save):
        from governance.services.cc_content_indexer import index_session_content
        from pathlib import Path

        mock_coll.side_effect = ConnectionError("ChromaDB down")
        result = index_session_content(
            Path("/fake/path.jsonl"), "SESSION-TEST", dry_run=False
        )
        assert result["status"] == "error"
        assert len(result["errors"]) > 0

    @patch("governance.services.cc_content_indexer.save_checkpoint")
    @patch("governance.services.cc_content_indexer.load_checkpoint", return_value=None)
    @patch("governance.services.cc_content_indexer.get_resume_offset", return_value=5)
    @patch("governance.services.cc_content_indexer.chunk_content")
    @patch("governance.session_metrics.parser.parse_log_file_extended")
    def test_resume_from_offset(self, mock_parse, mock_chunk, mock_offset, mock_load, mock_save):
        from governance.services.cc_content_indexer import index_session_content
        from pathlib import Path

        mock_parse.return_value = iter([])
        result = index_session_content(
            Path("/fake/path.jsonl"), "SESSION-TEST", dry_run=True, resume=True
        )
        assert result["resumed_from"] == 5


class TestDeleteSessionContent:
    @patch("governance.services.cc_content_indexer._get_chromadb_collection")
    def test_delete_success(self, mock_coll):
        from governance.services.cc_content_indexer import delete_session_content
        mock_collection = MagicMock()
        mock_coll.return_value = mock_collection

        result = delete_session_content("SESSION-TEST")
        assert result["status"] == "success"
        mock_collection.delete.assert_called_once()

    @patch("governance.services.cc_content_indexer._get_chromadb_collection")
    def test_delete_error(self, mock_coll):
        from governance.services.cc_content_indexer import delete_session_content
        mock_coll.side_effect = ConnectionError("down")

        result = delete_session_content("SESSION-TEST")
        assert result["status"] == "error"
