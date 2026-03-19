"""
Unit tests for CC Session Scanner module.

Per DOC-SIZE-01-v1: Tests for extracted scanner functions.
Tests: derive_project_slug, scan_jsonl_metadata, build_session_id, find_jsonl_for_session.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from tests.fixtures.cc_jsonl_factory import CCJsonlFactory

from governance.services.cc_session_scanner import (
    DEFAULT_CC_DIR,
    derive_project_slug,
    scan_jsonl_metadata,
    build_session_id,
    find_jsonl_for_session,
)


class TestDefaultCCDir:
    """Verify DEFAULT_CC_DIR constant."""

    def test_is_path(self):
        assert isinstance(DEFAULT_CC_DIR, Path)

    def test_ends_with_projects(self):
        assert DEFAULT_CC_DIR.name == "projects"
        assert DEFAULT_CC_DIR.parent.name == ".claude"


class TestDeriveProjectSlug:
    """Tests for derive_project_slug()."""

    def test_standard_cc_encoding(self, tmp_path):
        d = tmp_path / "-home-user-Documents-Vibe-sarvaja-platform"
        d.mkdir()
        assert derive_project_slug(d) == "sarvaja-platform"

    def test_single_segment(self, tmp_path):
        d = tmp_path / "myproject"
        d.mkdir()
        assert derive_project_slug(d) == "myproject"

    def test_two_segments(self, tmp_path):
        d = tmp_path / "-alpha-beta"
        d.mkdir()
        assert derive_project_slug(d) == "alpha-beta"

    def test_many_segments(self, tmp_path):
        d = tmp_path / "-home-oderid-Documents-Vibe-sarvaja-platform"
        d.mkdir()
        result = derive_project_slug(d)
        assert result == "sarvaja-platform"

    def test_lowercase_output(self, tmp_path):
        d = tmp_path / "-FOO-BAR"
        d.mkdir()
        assert derive_project_slug(d) == "foo-bar"


class TestScanJsonlMetadata:
    """Tests for scan_jsonl_metadata()."""

    def test_empty_file_returns_none(self, tmp_path):
        f = tmp_path / "empty.jsonl"
        f.write_text("")
        assert scan_jsonl_metadata(f) is None

    def test_zero_size_file(self, tmp_path):
        f = tmp_path / "zero.jsonl"
        f.touch()
        assert scan_jsonl_metadata(f) is None

    def test_no_timestamps_returns_none(self, tmp_path):
        f = tmp_path / "notime.jsonl"
        CCJsonlFactory.write_jsonl([{"type": "user"}], f)
        assert scan_jsonl_metadata(f) is None

    def test_basic_metadata_extraction(self, tmp_path):
        f = tmp_path / "session.jsonl"
        CCJsonlFactory.write_jsonl([
            {"type": "user", "timestamp": "2026-02-11T10:00:00Z",
             "sessionId": "uuid-1", "gitBranch": "feature-x"},
            {"type": "assistant", "timestamp": "2026-02-11T10:05:00Z",
             "message": {"content": [
                 {"type": "tool_use", "name": "Read"},
                 {"type": "tool_use", "name": "Write"},
                 {"type": "thinking", "thinking": "analyzing..."},
             ], "model": "claude-opus-4-6"}},
        ], f)
        meta = scan_jsonl_metadata(f)
        assert meta is not None
        assert meta["slug"] == "session"
        assert meta["session_uuid"] == "uuid-1"
        assert meta["git_branch"] == "feature-x"
        assert meta["first_ts"] == "2026-02-11T10:00:00Z"
        assert meta["last_ts"] == "2026-02-11T10:05:00Z"
        assert meta["user_count"] == 1
        assert meta["assistant_count"] == 1
        assert meta["tool_use_count"] == 2
        assert meta["thinking_chars"] == len("analyzing...")
        assert "claude-opus-4-6" in meta["models"]

    def test_compaction_counting(self, tmp_path):
        f = tmp_path / "compact.jsonl"
        CCJsonlFactory.write_jsonl([
            {"type": "user", "timestamp": "2026-02-11T10:00:00Z"},
            {"type": "system", "timestamp": "2026-02-11T10:05:00Z",
             "compactMetadata": {"tokensRemoved": 5000}},
            {"type": "system", "timestamp": "2026-02-11T10:10:00Z",
             "compactMetadata": {"tokensRemoved": 3000}},
        ], f)
        meta = scan_jsonl_metadata(f)
        assert meta["compaction_count"] == 2

    def test_skips_invalid_json(self, tmp_path):
        f = tmp_path / "mixed.jsonl"
        with open(f, "w") as fh:
            fh.write('{"type": "user", "timestamp": "2026-02-11T10:00:00Z"}\n')
            fh.write("not-json-line\n")
            fh.write('{"type": "assistant", "timestamp": "2026-02-11T10:01:00Z", "message": {}}\n')
        meta = scan_jsonl_metadata(f)
        assert meta is not None
        assert meta["user_count"] == 1
        assert meta["assistant_count"] == 1

    def test_file_path_and_size(self, tmp_path):
        f = tmp_path / "info.jsonl"
        CCJsonlFactory.write_jsonl([
            {"type": "user", "timestamp": "2026-02-11T10:00:00Z"},
        ], f)
        meta = scan_jsonl_metadata(f)
        assert meta["file_path"] == str(f)
        assert meta["file_size"] > 0

    def test_multiple_models_tracked(self, tmp_path):
        f = tmp_path / "multi.jsonl"
        CCJsonlFactory.write_jsonl([
            {"type": "user", "timestamp": "2026-02-11T10:00:00Z"},
            {"type": "assistant", "timestamp": "2026-02-11T10:01:00Z",
             "message": {"content": [], "model": "claude-opus-4-6"}},
            {"type": "assistant", "timestamp": "2026-02-11T10:02:00Z",
             "message": {"content": [], "model": "claude-sonnet-4-5-20250929"}},
        ], f)
        meta = scan_jsonl_metadata(f)
        assert len(meta["models"]) == 2
        assert "claude-opus-4-6" in meta["models"]

    def test_slug_from_stem(self, tmp_path):
        f = tmp_path / "my-custom-name.jsonl"
        CCJsonlFactory.write_jsonl([
            {"type": "user", "timestamp": "2026-02-11T10:00:00Z"},
        ], f)
        meta = scan_jsonl_metadata(f)
        assert meta["slug"] == "my-custom-name"


class TestBuildSessionId:
    """Tests for build_session_id()."""

    def test_standard_format(self):
        meta = {"first_ts": "2026-02-11T10:00:00Z", "slug": "my-session"}
        result = build_session_id(meta, "sarvaja-platform")
        assert result == "SESSION-2026-02-11-CC-MY-SESSION"

    def test_uppercase_conversion(self):
        meta = {"first_ts": "2026-01-01T00:00:00Z", "slug": "lower-case"}
        result = build_session_id(meta, "proj")
        assert result == "SESSION-2026-01-01-CC-LOWER-CASE"

    def test_slug_truncation_at_30(self):
        meta = {"first_ts": "2026-01-01T00:00:00Z", "slug": "a" * 50}
        result = build_session_id(meta, "proj")
        slug_part = result.split("-CC-")[1]
        assert len(slug_part) <= 30

    def test_spaces_replaced(self):
        meta = {"first_ts": "2026-03-15T12:00:00Z", "slug": "my session name"}
        result = build_session_id(meta, "proj")
        assert " " not in result

    def test_date_extraction(self):
        meta = {"first_ts": "2026-06-15T23:59:59Z", "slug": "test"}
        result = build_session_id(meta, "proj")
        assert "2026-06-15" in result


class TestFindJsonlForSession:
    """Tests for find_jsonl_for_session()."""

    def test_returns_none_when_no_match(self, tmp_path):
        with patch("governance.services.cc_session_scanner.DEFAULT_CC_DIR", tmp_path):
            result = find_jsonl_for_session({"session_id": "SESSION-2026-02-11-CC-NONEXISTENT"})
            assert result is None

    def test_finds_by_slug_match(self, tmp_path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        jsonl = project_dir / "my-session.jsonl"
        jsonl.write_text('{"type": "user"}\n')

        with patch("governance.services.cc_session_scanner.DEFAULT_CC_DIR", tmp_path):
            result = find_jsonl_for_session({
                "session_id": "SESSION-2026-02-11-CC-MY-SESSION",
            })
            assert result == jsonl

    def test_finds_by_uuid_match(self, tmp_path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        jsonl = project_dir / "uuid-abc-123.jsonl"
        jsonl.write_text('{"type": "user"}\n')

        with patch("governance.services.cc_session_scanner.DEFAULT_CC_DIR", tmp_path):
            result = find_jsonl_for_session({
                "session_id": "SESSION-2026-02-11-CC-SOMETHING",
                "cc_session_uuid": "uuid-abc-123",
            })
            assert result == jsonl

    def test_ignores_non_directories(self, tmp_path):
        regular_file = tmp_path / "not-a-dir.txt"
        regular_file.write_text("hello")

        with patch("governance.services.cc_session_scanner.DEFAULT_CC_DIR", tmp_path):
            result = find_jsonl_for_session({
                "session_id": "SESSION-2026-02-11-CC-TEST",
            })
            assert result is None

    def test_session_without_cc_prefix(self, tmp_path):
        with patch("governance.services.cc_session_scanner.DEFAULT_CC_DIR", tmp_path):
            result = find_jsonl_for_session({
                "session_id": "SESSION-2026-02-11-CHAT-HELLO",
            })
            assert result is None
