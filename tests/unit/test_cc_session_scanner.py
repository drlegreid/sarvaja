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
    get_sibling_scan_dirs,
    _resolve_host_path,
    discover_filesystem_projects,
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


class TestGetSiblingScandDirs:
    """Tests for get_sibling_scan_dirs() — GAP-GAMEDEV-WS."""

    def test_returns_empty_when_unset(self):
        with patch("governance.services.cc_session_scanner._SIBLING_SCAN_DIR", None):
            assert get_sibling_scan_dirs() == []

    def test_returns_empty_when_dir_missing(self, tmp_path):
        fake = str(tmp_path / "nonexistent")
        with patch("governance.services.cc_session_scanner._SIBLING_SCAN_DIR", fake):
            assert get_sibling_scan_dirs() == []

    def test_returns_dir_when_exists(self, tmp_path):
        with patch("governance.services.cc_session_scanner._SIBLING_SCAN_DIR", str(tmp_path)):
            result = get_sibling_scan_dirs()
            assert result == [str(tmp_path)]


class TestResolveHostPath:
    """Tests for _resolve_host_path() — GAP-GAMEDEV-WS."""

    def test_no_mapping_returns_unchanged(self):
        with patch("governance.services.cc_session_scanner._SIBLING_SCAN_DIR", None), \
             patch("governance.services.cc_session_scanner._SIBLING_HOST_DIR", None):
            assert _resolve_host_path("/app/project-siblings/gamedev") == "/app/project-siblings/gamedev"

    def test_maps_container_to_host(self):
        with patch("governance.services.cc_session_scanner._SIBLING_SCAN_DIR", "/app/project-siblings"), \
             patch("governance.services.cc_session_scanner._SIBLING_HOST_DIR", "/home/user/projects"):
            result = _resolve_host_path("/app/project-siblings/gamedev")
            assert result == "/home/user/projects/gamedev"

    def test_non_matching_prefix_unchanged(self):
        with patch("governance.services.cc_session_scanner._SIBLING_SCAN_DIR", "/app/project-siblings"), \
             patch("governance.services.cc_session_scanner._SIBLING_HOST_DIR", "/home/user/projects"):
            result = _resolve_host_path("/other/path/gamedev")
            assert result == "/other/path/gamedev"


class TestDiscoverFilesystemProjectsSibling:
    """Tests for discover_filesystem_projects() with sibling scanning — GAP-GAMEDEV-WS."""

    def test_discovers_sibling_with_claude_marker(self, tmp_path):
        """Sibling dir with CLAUDE.md is discovered."""
        gamedev = tmp_path / "gamedev"
        gamedev.mkdir()
        (gamedev / "CLAUDE.md").write_text("# Gamedev")

        with patch("governance.services.cc_session_scanner._SIBLING_SCAN_DIR", str(tmp_path)), \
             patch("governance.services.cc_session_scanner._SIBLING_HOST_DIR", "/home/user/sarvaja"):
            result = discover_filesystem_projects()
            assert len(result) == 1
            assert result[0]["project_id"] == "PROJ-GAMEDEV"
            assert result[0]["name"] == "Gamedev"
            assert result[0]["path"] == "/home/user/sarvaja/gamedev"

    def test_discovers_godot_project(self, tmp_path):
        """Sibling dir with project.godot is discovered."""
        game = tmp_path / "chess-ai"
        game.mkdir()
        (game / "project.godot").write_text("[gd_scene]")

        with patch("governance.services.cc_session_scanner._SIBLING_SCAN_DIR", str(tmp_path)), \
             patch("governance.services.cc_session_scanner._SIBLING_HOST_DIR", "/host/projects"):
            result = discover_filesystem_projects()
            assert len(result) == 1
            assert result[0]["project_id"] == "PROJ-CHESS-AI"
            assert result[0]["path"] == "/host/projects/chess-ai"

    def test_skips_existing_ids(self, tmp_path):
        """Already-known project IDs are excluded."""
        gamedev = tmp_path / "gamedev"
        gamedev.mkdir()
        (gamedev / "CLAUDE.md").write_text("# Gamedev")

        with patch("governance.services.cc_session_scanner._SIBLING_SCAN_DIR", str(tmp_path)), \
             patch("governance.services.cc_session_scanner._SIBLING_HOST_DIR", "/host"):
            result = discover_filesystem_projects(existing_ids={"PROJ-GAMEDEV"})
            assert len(result) == 0

    def test_skips_existing_paths(self, tmp_path):
        """Already-known project paths are excluded (using host path)."""
        gamedev = tmp_path / "gamedev"
        gamedev.mkdir()
        (gamedev / "CLAUDE.md").write_text("# Gamedev")

        with patch("governance.services.cc_session_scanner._SIBLING_SCAN_DIR", str(tmp_path)), \
             patch("governance.services.cc_session_scanner._SIBLING_HOST_DIR", "/host"):
            result = discover_filesystem_projects(existing_paths={"/host/gamedev"})
            assert len(result) == 0

    def test_skips_hidden_dirs(self, tmp_path):
        """Directories starting with . are skipped."""
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "CLAUDE.md").write_text("# Hidden")

        with patch("governance.services.cc_session_scanner._SIBLING_SCAN_DIR", str(tmp_path)), \
             patch("governance.services.cc_session_scanner._SIBLING_HOST_DIR", "/host"):
            result = discover_filesystem_projects()
            assert len(result) == 0

    def test_skips_dirs_without_markers(self, tmp_path):
        """Directories without project markers are skipped."""
        empty = tmp_path / "empty-dir"
        empty.mkdir()

        with patch("governance.services.cc_session_scanner._SIBLING_SCAN_DIR", str(tmp_path)), \
             patch("governance.services.cc_session_scanner._SIBLING_HOST_DIR", "/host"):
            result = discover_filesystem_projects()
            assert len(result) == 0

    def test_combines_scan_dirs_with_sibling(self, tmp_path):
        """Explicit scan_dirs + sibling dir are both scanned."""
        explicit = tmp_path / "explicit"
        explicit.mkdir()
        proj_a = explicit / "proj-a"
        proj_a.mkdir()
        (proj_a / "package.json").write_text("{}")

        sibling = tmp_path / "sibling"
        sibling.mkdir()
        proj_b = sibling / "proj-b"
        proj_b.mkdir()
        (proj_b / "CLAUDE.md").write_text("# B")

        with patch("governance.services.cc_session_scanner._SIBLING_SCAN_DIR", str(sibling)), \
             patch("governance.services.cc_session_scanner._SIBLING_HOST_DIR", "/host"):
            result = discover_filesystem_projects(scan_dirs=[str(explicit)])
            ids = {p["project_id"] for p in result}
            assert "PROJ-PROJ-A" in ids
            assert "PROJ-PROJ-B" in ids
