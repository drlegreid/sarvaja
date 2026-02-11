"""
Unit tests for CC Session Ingestion Service.

Per SESSION-CC-01-v1, DATA-INGEST-01-v1, DATA-LAZY-01-v1.
Tests: metadata scanning, session ID building, ingestion, lazy loading.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from tempfile import NamedTemporaryFile, TemporaryDirectory

from governance.services.cc_session_ingestion import (
    _derive_project_slug,
    _scan_jsonl_metadata,
    _build_session_id,
    ingest_session,
    ingest_all,
    get_session_detail,
)


class TestDeriveProjectSlug:
    """Tests for _derive_project_slug()."""

    def test_standard_cc_path(self, tmp_path):
        d = tmp_path / "-home-user-Documents-Vibe-sarvaja-platform"
        d.mkdir()
        assert _derive_project_slug(d) == "sarvaja-platform"

    def test_short_path(self, tmp_path):
        d = tmp_path / "single"
        d.mkdir()
        assert _derive_project_slug(d) == "single"

    def test_two_segments(self, tmp_path):
        d = tmp_path / "-foo-bar"
        d.mkdir()
        assert _derive_project_slug(d) == "foo-bar"

    def test_hyphen_encoding(self, tmp_path):
        d = tmp_path / "-home-oderid-Documents-project"
        d.mkdir()
        assert _derive_project_slug(d) == "documents-project"


class TestScanJsonlMetadata:
    """Tests for _scan_jsonl_metadata()."""

    def _write_jsonl(self, filepath, entries):
        with open(filepath, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.jsonl"
        f.write_text("")
        assert _scan_jsonl_metadata(f) is None

    def test_no_timestamp(self, tmp_path):
        f = tmp_path / "notime.jsonl"
        self._write_jsonl(f, [{"type": "user"}])
        assert _scan_jsonl_metadata(f) is None

    def test_basic_scan(self, tmp_path):
        f = tmp_path / "session-abc.jsonl"
        self._write_jsonl(f, [
            {"type": "user", "timestamp": "2026-02-11T10:00:00Z",
             "sessionId": "uuid-123", "gitBranch": "master"},
            {"type": "assistant", "timestamp": "2026-02-11T10:01:00Z",
             "message": {"content": [
                 {"type": "tool_use", "name": "Read"},
                 {"type": "thinking", "thinking": "Let me think..."},
             ], "model": "claude-opus-4-6"}},
        ])
        meta = _scan_jsonl_metadata(f)
        assert meta is not None
        assert meta["slug"] == "session-abc"
        assert meta["session_uuid"] == "uuid-123"
        assert meta["git_branch"] == "master"
        assert meta["first_ts"] == "2026-02-11T10:00:00Z"
        assert meta["last_ts"] == "2026-02-11T10:01:00Z"
        assert meta["user_count"] == 1
        assert meta["assistant_count"] == 1
        assert meta["tool_use_count"] == 1
        assert meta["thinking_chars"] == len("Let me think...")
        assert "claude-opus-4-6" in meta["models"]

    def test_compaction_count(self, tmp_path):
        f = tmp_path / "compact.jsonl"
        self._write_jsonl(f, [
            {"type": "user", "timestamp": "2026-02-11T10:00:00Z"},
            {"type": "system", "timestamp": "2026-02-11T10:05:00Z",
             "compactMetadata": {"tokensRemoved": 5000}},
            {"type": "system", "timestamp": "2026-02-11T10:10:00Z",
             "compactMetadata": {"tokensRemoved": 3000}},
        ])
        meta = _scan_jsonl_metadata(f)
        assert meta["compaction_count"] == 2

    def test_invalid_json_line(self, tmp_path):
        f = tmp_path / "bad.jsonl"
        with open(f, "w") as fh:
            fh.write('{"type": "user", "timestamp": "2026-02-11T10:00:00Z"}\n')
            fh.write("not json\n")
            fh.write('{"type": "assistant", "timestamp": "2026-02-11T10:01:00Z", "message": {}}\n')
        meta = _scan_jsonl_metadata(f)
        assert meta is not None
        assert meta["user_count"] == 1
        assert meta["assistant_count"] == 1

    def test_file_path_and_size_included(self, tmp_path):
        f = tmp_path / "size.jsonl"
        self._write_jsonl(f, [
            {"type": "user", "timestamp": "2026-02-11T10:00:00Z"},
        ])
        meta = _scan_jsonl_metadata(f)
        assert meta["file_path"] == str(f)
        assert meta["file_size"] > 0


class TestBuildSessionId:
    """Tests for _build_session_id()."""

    def test_standard_id(self):
        meta = {"first_ts": "2026-02-11T10:00:00Z", "slug": "test-session"}
        result = _build_session_id(meta, "sarvaja-platform")
        assert result == "SESSION-2026-02-11-CC-TEST-SESSION"

    def test_long_slug_truncated(self):
        meta = {"first_ts": "2026-01-01T00:00:00Z", "slug": "a" * 50}
        result = _build_session_id(meta, "proj")
        # slug truncated to 30 chars
        assert len(result.split("-CC-")[1]) <= 30

    def test_spaces_replaced(self):
        meta = {"first_ts": "2026-03-15T12:00:00Z", "slug": "my session file"}
        result = _build_session_id(meta, "proj")
        assert " " not in result


class TestIngestSession:
    """Tests for ingest_session()."""

    def _make_jsonl(self, tmp_path, name="test-session.jsonl"):
        f = tmp_path / name
        entries = [
            {"type": "user", "timestamp": "2026-02-11T10:00:00Z",
             "sessionId": "uuid-abc", "gitBranch": "master"},
            {"type": "assistant", "timestamp": "2026-02-11T10:01:00Z",
             "message": {"content": [{"type": "tool_use", "name": "Read"}]}},
        ]
        with open(f, "w") as fh:
            for e in entries:
                fh.write(json.dumps(e) + "\n")
        return f

    @patch("governance.services.cc_session_ingestion.session_service")
    def test_ingest_dry_run(self, mock_svc, tmp_path):
        mock_svc.get_session.return_value = None
        f = self._make_jsonl(tmp_path)
        result = ingest_session(f, project_slug="test", dry_run=True)
        assert result is not None
        assert result["dry_run"] is True
        assert result["cc_session_uuid"] == "uuid-abc"
        mock_svc.create_session.assert_not_called()

    @patch("governance.services.cc_session_ingestion.session_service")
    def test_ingest_skips_existing(self, mock_svc, tmp_path):
        mock_svc.get_session.return_value = {"session_id": "existing"}
        f = self._make_jsonl(tmp_path)
        result = ingest_session(f, project_slug="test")
        assert result is None
        mock_svc.create_session.assert_not_called()

    @patch("governance.services.cc_session_ingestion.session_service")
    def test_ingest_creates_session(self, mock_svc, tmp_path):
        mock_svc.get_session.return_value = None
        mock_svc.create_session.return_value = {"session_id": "SESSION-2026-02-11-CC-TEST-SESSION"}
        f = self._make_jsonl(tmp_path)
        result = ingest_session(f, project_slug="test")
        assert result is not None
        mock_svc.create_session.assert_called_once()
        call_kwargs = mock_svc.create_session.call_args
        assert call_kwargs.kwargs.get("cc_session_uuid") == "uuid-abc"
        assert call_kwargs.kwargs.get("cc_git_branch") == "master"

    @patch("governance.services.cc_session_ingestion.session_service")
    def test_ingest_links_to_project(self, mock_svc, tmp_path):
        mock_svc.get_session.return_value = None
        mock_svc.create_session.return_value = {"session_id": "S-1"}
        f = self._make_jsonl(tmp_path)
        with patch("governance.services.projects.link_session_to_project") as mock_link:
            result = ingest_session(
                f, project_slug="test", project_id="PROJ-TEST",
            )
            mock_link.assert_called_once_with("PROJ-TEST", "SESSION-2026-02-11-CC-TEST-SESSION")

    def test_ingest_empty_file(self, tmp_path):
        f = tmp_path / "empty.jsonl"
        f.write_text("")
        result = ingest_session(f, project_slug="test")
        assert result is None


class TestIngestAll:
    """Tests for ingest_all()."""

    @patch("governance.services.cc_session_ingestion.session_service")
    @patch("governance.services.cc_session_ingestion.discover_log_files")
    def test_ingest_all_processes_files(self, mock_discover, mock_svc, tmp_path):
        # Create test JSONL files
        f1 = tmp_path / "s1.jsonl"
        f2 = tmp_path / "s2.jsonl"
        for f in [f1, f2]:
            with open(f, "w") as fh:
                fh.write(json.dumps({"type": "user", "timestamp": "2026-02-11T10:00:00Z", "sessionId": f.stem}) + "\n")

        mock_discover.return_value = [f1, f2]
        mock_svc.get_session.return_value = None
        mock_svc.create_session.side_effect = [
            {"session_id": "S-1"}, {"session_id": "S-2"},
        ]

        results = ingest_all(directory=tmp_path, project_slug="test")
        assert len(results) == 2

    @patch("governance.services.cc_session_ingestion.discover_log_files")
    def test_ingest_all_skips_empty(self, mock_discover, tmp_path):
        f = tmp_path / "empty.jsonl"
        f.write_text("")
        mock_discover.return_value = [f]
        results = ingest_all(directory=tmp_path, project_slug="test")
        assert len(results) == 0

    def test_ingest_all_missing_dir(self):
        results = ingest_all(directory=Path("/nonexistent/dir"), project_slug="test")
        assert results == []


class TestGetSessionDetail:
    """Tests for get_session_detail() zoom levels."""

    @patch("governance.services.cc_session_ingestion.session_service")
    def test_zoom_0_summary_only(self, mock_svc):
        mock_svc.get_session.return_value = {
            "session_id": "S-1",
            "status": "COMPLETED",
            "description": "Test session",
            "start_time": "2026-02-11T10:00:00Z",
            "end_time": "2026-02-11T11:00:00Z",
            "cc_session_uuid": "uuid-1",
            "cc_project_slug": "test",
            "cc_git_branch": "master",
            "cc_tool_count": 42,
            "cc_thinking_chars": 5000,
            "cc_compaction_count": 2,
        }
        result = get_session_detail("S-1", zoom=0)
        assert result is not None
        assert result["zoom"] == 0
        assert result["summary"]["cc_session_uuid"] == "uuid-1"
        assert result["summary"]["cc_tool_count"] == 42
        assert "tool_breakdown" not in result

    @patch("governance.services.cc_session_ingestion.session_service")
    def test_zoom_1_includes_breakdown(self, mock_svc):
        mock_svc.get_session.return_value = {
            "session_id": "SESSION-2026-02-11-CC-TEST",
            "status": "COMPLETED",
            "cc_session_uuid": "uuid-2",
        }
        with patch(
            "governance.services.cc_session_ingestion._find_jsonl_for_session",
            return_value=None,
        ):
            result = get_session_detail("SESSION-2026-02-11-CC-TEST", zoom=1)
        assert result is not None
        assert result["zoom"] == 1
        # No JSONL found, so no breakdown
        assert "tool_breakdown" not in result

    @patch("governance.services.cc_session_ingestion.session_service")
    def test_nonexistent_session(self, mock_svc):
        mock_svc.get_session.return_value = None
        result = get_session_detail("NOPE")
        assert result is None

    @patch("governance.services.cc_session_ingestion.session_service")
    def test_summary_fields_present(self, mock_svc):
        mock_svc.get_session.return_value = {
            "session_id": "S-X", "status": "ACTIVE",
        }
        result = get_session_detail("S-X", zoom=0)
        summary = result["summary"]
        expected_keys = [
            "status", "description", "start_time", "end_time",
            "cc_session_uuid", "cc_project_slug", "cc_git_branch",
            "cc_tool_count", "cc_thinking_chars", "cc_compaction_count",
        ]
        for key in expected_keys:
            assert key in summary
