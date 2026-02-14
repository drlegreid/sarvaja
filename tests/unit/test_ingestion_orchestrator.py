"""
Tests for ingestion orchestrator (content indexing + link mining coordination).

Batch 168: New coverage for governance/services/ingestion_orchestrator.py (0->16 tests).
"""
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestGetRssMb:
    @patch("governance.services.ingestion_orchestrator.resource")
    def test_returns_float(self, mock_resource):
        from governance.services.ingestion_orchestrator import _get_rss_mb
        mock_usage = MagicMock()
        mock_usage.ru_maxrss = 102400  # 100MB in KB
        mock_resource.getrusage.return_value = mock_usage
        result = _get_rss_mb()
        assert isinstance(result, float)
        assert result == 100.0

    @patch("governance.services.ingestion_orchestrator.resource")
    def test_divides_by_1024(self, mock_resource):
        from governance.services.ingestion_orchestrator import _get_rss_mb
        mock_usage = MagicMock()
        mock_usage.ru_maxrss = 1024
        mock_resource.getrusage.return_value = mock_usage
        result = _get_rss_mb()
        assert result == 1.0


class TestEstimateIngestion:
    def test_file_not_found(self):
        from governance.services.ingestion_orchestrator import estimate_ingestion
        result = estimate_ingestion(Path("/nonexistent/file.jsonl"))
        assert result["status"] == "error"
        assert "not found" in result["error"]

    def test_valid_file(self):
        from governance.services.ingestion_orchestrator import estimate_ingestion
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"line": 1}\n')
            f.write('{"line": 2}\n')
            f.write('{"line": 3}\n')
            path = Path(f.name)

        try:
            result = estimate_ingestion(path)
            assert result["status"] == "ok"
            assert result["line_count"] == 3
            assert result["size_bytes"] > 0
            assert "est_chunks" in result
            assert result["est_memory_mb"] == 55
        finally:
            path.unlink()

    def test_empty_file(self):
        from governance.services.ingestion_orchestrator import estimate_ingestion
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = Path(f.name)

        try:
            result = estimate_ingestion(path)
            assert result["status"] == "ok"
            assert result["line_count"] == 0
        finally:
            path.unlink()


class TestGetIngestionStatus:
    @patch("governance.services.ingestion_orchestrator.load_checkpoint", return_value=None)
    def test_not_started(self, mock_load):
        from governance.services.ingestion_orchestrator import get_ingestion_status
        result = get_ingestion_status("SESSION-X")
        assert result["status"] == "not_started"

    @patch("governance.services.ingestion_orchestrator.load_checkpoint")
    def test_with_checkpoint(self, mock_load):
        from governance.services.ingestion_orchestrator import get_ingestion_status
        mock_ckpt = MagicMock()
        mock_ckpt.phase = "content"
        mock_ckpt.lines_processed = 100
        mock_ckpt.chunks_indexed = 50
        mock_ckpt.links_created = 10
        mock_ckpt.started_at = "2026-02-13T10:00:00"
        mock_ckpt.updated_at = "2026-02-13T10:05:00"
        mock_ckpt.errors = []
        mock_load.return_value = mock_ckpt

        result = get_ingestion_status("SESSION-X")
        assert result["status"] == "content"
        assert result["lines_processed"] == 100
        assert result["chunks_indexed"] == 50


class TestRollbackContentIndex:
    @patch("governance.services.ingestion_orchestrator.delete_checkpoint", return_value=True)
    @patch("governance.services.ingestion_orchestrator.delete_session_content")
    def test_rollback(self, mock_delete, mock_del_ckpt):
        from governance.services.ingestion_orchestrator import rollback_content_index
        mock_delete.return_value = {"status": "success"}
        result = rollback_content_index("SESSION-X")
        assert result["status"] == "rolled_back"
        assert result["checkpoint_deleted"] is True


class TestRunIngestionPipeline:
    def test_file_not_found(self):
        from governance.services.ingestion_orchestrator import run_ingestion_pipeline
        result = run_ingestion_pipeline(Path("/nonexistent.jsonl"), "SESSION-X")
        assert result["status"] == "error"

    @patch("governance.services.ingestion_orchestrator.save_checkpoint")
    @patch("governance.services.ingestion_orchestrator.load_checkpoint", return_value=None)
    @patch("governance.services.ingestion_orchestrator._get_rss_mb", return_value=600.0)
    @patch("governance.services.ingestion_orchestrator.index_session_content")
    def test_memory_limit_skips_content(self, mock_index, mock_rss, mock_load, mock_save):
        from governance.services.ingestion_orchestrator import run_ingestion_pipeline
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            f.write(b'{"x":1}\n')
            path = Path(f.name)

        try:
            result = run_ingestion_pipeline(path, "SESSION-X", memory_limit_mb=500)
            assert result["status"] == "memory_limit"
            mock_index.assert_not_called()
        finally:
            path.unlink()

    @patch("governance.services.ingestion_orchestrator.save_checkpoint")
    @patch("governance.services.ingestion_orchestrator.load_checkpoint", return_value=None)
    @patch("governance.services.ingestion_orchestrator._get_rss_mb", return_value=50.0)
    @patch("governance.services.ingestion_orchestrator.mine_session_links")
    @patch("governance.services.ingestion_orchestrator.index_session_content")
    def test_both_phases_run(self, mock_index, mock_mine, mock_rss, mock_load, mock_save):
        from governance.services.ingestion_orchestrator import run_ingestion_pipeline
        mock_index.return_value = {"status": "success"}
        mock_mine.return_value = {"status": "success"}

        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            f.write(b'{"x":1}\n')
            path = Path(f.name)

        try:
            result = run_ingestion_pipeline(path, "SESSION-X", dry_run=True)
            assert result["status"] == "success"
            mock_index.assert_called_once()
            mock_mine.assert_called_once()
        finally:
            path.unlink()

    @patch("governance.services.ingestion_orchestrator.save_checkpoint")
    @patch("governance.services.ingestion_orchestrator.load_checkpoint", return_value=None)
    @patch("governance.services.ingestion_orchestrator._get_rss_mb", return_value=50.0)
    @patch("governance.services.ingestion_orchestrator.index_session_content")
    def test_content_only_phase(self, mock_index, mock_rss, mock_load, mock_save):
        from governance.services.ingestion_orchestrator import run_ingestion_pipeline
        mock_index.return_value = {"status": "success"}

        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            f.write(b'{"x":1}\n')
            path = Path(f.name)

        try:
            result = run_ingestion_pipeline(
                path, "SESSION-X", phases=["content"], dry_run=True
            )
            assert result["content"] is not None
            assert result["linking"] is None
        finally:
            path.unlink()
