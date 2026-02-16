"""TDD Tests for P2: Filesystem-Based Project Discovery.

Root cause: discover_cc_projects() only scans ~/.claude/projects/ and requires
JSONL files. Game projects (tic-tac-toe, sea-battle) have no CC directories.

Solution: discover_filesystem_projects() scans configurable parent directories
for project markers (project.godot, CLAUDE.md, package.json, etc.) and returns
discovered projects with auto-detected types via detect_project_type().

These tests are TDD — verify fix works for game project discovery.
"""
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Test Group 1: discover_filesystem_projects exists and is importable
# ---------------------------------------------------------------------------

class TestFilesystemDiscoveryExists:
    """Verify filesystem discovery function exists."""

    def test_function_importable(self):
        """discover_filesystem_projects can be imported."""
        from governance.services.cc_session_scanner import discover_filesystem_projects
        assert callable(discover_filesystem_projects)

    def test_returns_list(self):
        """Returns a list when called with empty dir."""
        from governance.services.cc_session_scanner import discover_filesystem_projects

        with tempfile.TemporaryDirectory() as tmpdir:
            result = discover_filesystem_projects(scan_dirs=[tmpdir])
            assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Test Group 2: Discovers Godot projects
# ---------------------------------------------------------------------------

class TestDiscoversGodotProjects:
    """Filesystem scanner finds Godot projects by project.godot marker."""

    def test_finds_godot_project(self):
        """Directory with project.godot is discovered as gamedev."""
        from governance.services.cc_session_scanner import discover_filesystem_projects

        with tempfile.TemporaryDirectory() as tmpdir:
            game_dir = Path(tmpdir) / "my-game"
            game_dir.mkdir()
            (game_dir / "project.godot").write_text("[gd_scene]\n")

            result = discover_filesystem_projects(scan_dirs=[tmpdir])
            assert len(result) >= 1
            found = [p for p in result if "my-game" in p.get("name", "").lower()
                     or "my-game" in p.get("path", "")]
            assert len(found) == 1
            assert found[0]["project_type"] == "gamedev"

    def test_finds_multiple_game_projects(self):
        """Discovers multiple game projects in same parent dir."""
        from governance.services.cc_session_scanner import discover_filesystem_projects

        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ["tic-tac-toe", "sea-battle"]:
                d = Path(tmpdir) / name
                d.mkdir()
                (d / "project.godot").write_text("[gd_scene]\n")

            result = discover_filesystem_projects(scan_dirs=[tmpdir])
            assert len(result) >= 2

    def test_project_has_required_fields(self):
        """Discovered project has project_id, name, path, project_type."""
        from governance.services.cc_session_scanner import discover_filesystem_projects

        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir) / "test-proj"
            d.mkdir()
            (d / "project.godot").write_text("[gd_scene]\n")

            result = discover_filesystem_projects(scan_dirs=[tmpdir])
            assert len(result) >= 1
            proj = result[0]
            assert "project_id" in proj
            assert "name" in proj
            assert "path" in proj
            assert "project_type" in proj


# ---------------------------------------------------------------------------
# Test Group 3: Discovers other project types
# ---------------------------------------------------------------------------

class TestDiscoversOtherProjectTypes:
    """Filesystem scanner finds non-Godot projects too."""

    def test_finds_python_project_with_claude_md(self):
        """Directory with CLAUDE.md is discovered."""
        from governance.services.cc_session_scanner import discover_filesystem_projects

        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir) / "my-python-app"
            d.mkdir()
            (d / "CLAUDE.md").write_text("# Project\n")

            result = discover_filesystem_projects(scan_dirs=[tmpdir])
            assert len(result) >= 1

    def test_skips_hidden_directories(self):
        """Hidden directories (starting with .) are skipped."""
        from governance.services.cc_session_scanner import discover_filesystem_projects

        with tempfile.TemporaryDirectory() as tmpdir:
            hidden = Path(tmpdir) / ".hidden-proj"
            hidden.mkdir()
            (hidden / "project.godot").write_text("[gd_scene]\n")

            result = discover_filesystem_projects(scan_dirs=[tmpdir])
            assert len(result) == 0

    def test_skips_empty_directories(self):
        """Directories without project markers are skipped."""
        from governance.services.cc_session_scanner import discover_filesystem_projects

        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "empty-dir").mkdir()
            (Path(tmpdir) / "another-empty").mkdir()

            result = discover_filesystem_projects(scan_dirs=[tmpdir])
            assert len(result) == 0


# ---------------------------------------------------------------------------
# Test Group 4: Deduplication with CC projects
# ---------------------------------------------------------------------------

class TestDeduplicationWithCC:
    """Filesystem projects don't duplicate existing CC-discovered projects."""

    def test_excludes_already_known_paths(self):
        """Projects already in existing_paths are excluded."""
        from governance.services.cc_session_scanner import discover_filesystem_projects

        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir) / "already-known"
            d.mkdir()
            (d / "project.godot").write_text("[gd_scene]\n")

            result = discover_filesystem_projects(
                scan_dirs=[tmpdir],
                existing_paths={str(d)},
            )
            assert len(result) == 0

    def test_excludes_already_known_project_ids(self):
        """Projects matching existing project_ids are excluded."""
        from governance.services.cc_session_scanner import discover_filesystem_projects

        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir) / "my-proj"
            d.mkdir()
            (d / "CLAUDE.md").write_text("# Stuff\n")

            result = discover_filesystem_projects(
                scan_dirs=[tmpdir],
                existing_ids={"PROJ-MY-PROJ"},
            )
            assert len(result) == 0


# ---------------------------------------------------------------------------
# Test Group 5: Integration with _load_projects
# ---------------------------------------------------------------------------

class TestLoadProjectsIntegration:
    """_load_projects uses filesystem discovery for game projects."""

    def test_discover_filesystem_projects_finds_real_godot_games(self):
        """Integration: discover_filesystem_projects finds Godot games directory."""
        from governance.services.cc_session_scanner import discover_filesystem_projects

        # Scan the actual godot-games parent directory
        godot_parent = "/home/oderid/Documents/Vibe/godot-games"
        result = discover_filesystem_projects(scan_dirs=[godot_parent])

        # Should find tic-tac-toe and sea-battle
        names = [p["name"].lower() for p in result]
        paths = [p["path"] for p in result]

        # At least one game found (both should exist)
        assert len(result) >= 1
        # Check project type is gamedev
        for proj in result:
            assert proj["project_type"] == "gamedev"

    def test_discover_filesystem_projects_generates_correct_ids(self):
        """Integration: project_id follows PROJ-{SLUG} convention."""
        from governance.services.cc_session_scanner import discover_filesystem_projects

        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir) / "my-cool-game"
            d.mkdir()
            (d / "project.godot").write_text("[gd_scene]\n")

            result = discover_filesystem_projects(scan_dirs=[tmpdir])
            assert len(result) == 1
            assert result[0]["project_id"] == "PROJ-MY-COOL-GAME"
