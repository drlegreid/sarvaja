"""Tests for auto_save.py — ChromaDB auto-save from hooks.

Per P3-13: Context prevention wiring.
Tests auto-save at entropy thresholds + context recovery for preloading.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".claude" / "hooks"))
import auto_save


# =============================================================================
# auto_save_context() tests
# =============================================================================

class TestAutoSaveContext:
    """Tests for auto_save_context()."""

    @patch("auto_save._get_chromadb_collection")
    @patch("auto_save._get_entropy_state")
    @patch("auto_save._get_git_info")
    @patch("auto_save._get_modified_files")
    def test_saves_to_chromadb(self, mock_files, mock_git, mock_entropy, mock_coll):
        """Should save context document to ChromaDB collection."""
        mock_collection = MagicMock()
        mock_coll.return_value = mock_collection
        mock_entropy.return_value = {
            "tool_count": 120,
            "session_start": "2026-03-20T10:00:00",
            "session_hash": "AB12",
            "recent_tools": ["Read", "Edit", "Read"],
        }
        mock_git.return_value = {"branch": "master", "recent_commits": ["abc Fix bug"]}
        mock_files.return_value = ["file1.py", "file2.py"]

        result = auto_save.auto_save_context(trigger="test")

        assert result == "ctx-SESSION-2026-03-20-AUTO-AB12"
        mock_collection.upsert.assert_called_once()
        call_args = mock_collection.upsert.call_args
        assert call_args.kwargs["ids"] == ["ctx-SESSION-2026-03-20-AUTO-AB12"]
        assert "test" in call_args.kwargs["metadatas"][0]["trigger"]
        assert call_args.kwargs["metadatas"][0]["type"] == "session_context"
        assert call_args.kwargs["metadatas"][0]["auto_saved"] == "true"

    @patch("auto_save._get_chromadb_collection")
    def test_returns_none_when_chromadb_unavailable(self, mock_coll):
        """Should return None when ChromaDB is not reachable."""
        mock_coll.return_value = None
        result = auto_save.auto_save_context()
        assert result is None

    @patch("auto_save._get_chromadb_collection")
    @patch("auto_save._get_entropy_state")
    @patch("auto_save._get_git_info")
    @patch("auto_save._get_modified_files")
    def test_handles_upsert_failure(self, mock_files, mock_git, mock_entropy, mock_coll):
        """Should return None when ChromaDB upsert fails."""
        mock_collection = MagicMock()
        mock_collection.upsert.side_effect = Exception("network error")
        mock_coll.return_value = mock_collection
        mock_entropy.return_value = {"tool_count": 100, "session_start": "2026-03-20T10:00:00", "session_hash": "DEAD"}
        mock_git.return_value = {"branch": "master", "recent_commits": []}
        mock_files.return_value = []

        result = auto_save.auto_save_context()
        assert result is None

    @patch("auto_save._get_chromadb_collection")
    @patch("auto_save._get_entropy_state")
    @patch("auto_save._get_git_info")
    @patch("auto_save._get_modified_files")
    def test_includes_tool_summary(self, mock_files, mock_git, mock_entropy, mock_coll):
        """Should include top tools in context document."""
        mock_collection = MagicMock()
        mock_coll.return_value = mock_collection
        mock_entropy.return_value = {
            "tool_count": 80,
            "session_start": "2026-03-20T10:00:00",
            "session_hash": "CAFE",
            "recent_tools": ["Read", "Read", "Edit", "Bash", "Read", "Edit"],
        }
        mock_git.return_value = {"branch": "feat/x", "recent_commits": []}
        mock_files.return_value = []

        auto_save.auto_save_context(trigger="high")

        doc = mock_collection.upsert.call_args.kwargs["documents"][0]
        assert "Read(3)" in doc
        assert "Edit(2)" in doc

    @patch("auto_save._get_chromadb_collection")
    @patch("auto_save._get_entropy_state")
    @patch("auto_save._get_git_info")
    @patch("auto_save._get_modified_files")
    def test_caps_modified_files(self, mock_files, mock_git, mock_entropy, mock_coll):
        """Should cap modified files list at 15."""
        mock_collection = MagicMock()
        mock_coll.return_value = mock_collection
        mock_entropy.return_value = {
            "tool_count": 50,
            "session_start": "2026-03-20T10:00:00",
            "session_hash": "BEEF",
        }
        mock_git.return_value = {"branch": "master", "recent_commits": []}
        mock_files.return_value = [f"file{i}.py" for i in range(20)]

        auto_save.auto_save_context()

        doc = mock_collection.upsert.call_args.kwargs["documents"][0]
        # Should have at most 15 file lines
        file_lines = [l for l in doc.split("\n") if l.startswith("- file")]
        assert len(file_lines) <= 15

    @patch("auto_save._get_chromadb_collection")
    @patch("auto_save._get_entropy_state")
    @patch("auto_save._get_git_info")
    @patch("auto_save._get_modified_files")
    def test_handles_empty_entropy_state(self, mock_files, mock_git, mock_entropy, mock_coll):
        """Should handle empty entropy state gracefully."""
        mock_collection = MagicMock()
        mock_coll.return_value = mock_collection
        mock_entropy.return_value = {}
        mock_git.return_value = {"branch": "main", "recent_commits": []}
        mock_files.return_value = []

        result = auto_save.auto_save_context()
        assert result is not None  # Should still save with defaults
        mock_collection.upsert.assert_called_once()


# =============================================================================
# recover_recent_contexts() tests
# =============================================================================

class TestRecoverRecentContexts:
    """Tests for recover_recent_contexts()."""

    @patch("auto_save._get_chromadb_collection")
    def test_returns_contexts(self, mock_coll):
        """Should return list of context dicts from ChromaDB."""
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "ids": [["ctx-SESSION-A", "ctx-SESSION-B"]],
            "documents": [["Doc A content", "Doc B content"]],
            "metadatas": [[
                {"session_id": "SESSION-A", "tool_count": 100},
                {"session_id": "SESSION-B", "tool_count": 50},
            ]],
        }
        mock_coll.return_value = mock_collection

        result = auto_save.recover_recent_contexts(n_results=2)

        assert len(result) == 2
        assert result[0]["id"] == "ctx-SESSION-A"
        assert result[0]["metadata"]["tool_count"] == 100
        assert result[1]["document"] == "Doc B content"

    @patch("auto_save._get_chromadb_collection")
    def test_returns_empty_on_chromadb_failure(self, mock_coll):
        """Should return empty list when ChromaDB unavailable."""
        mock_coll.return_value = None
        result = auto_save.recover_recent_contexts()
        assert result == []

    @patch("auto_save._get_chromadb_collection")
    def test_handles_query_exception(self, mock_coll):
        """Should return empty list on query failure."""
        mock_collection = MagicMock()
        mock_collection.query.side_effect = Exception("timeout")
        mock_coll.return_value = mock_collection

        result = auto_save.recover_recent_contexts()
        assert result == []

    @patch("auto_save._get_chromadb_collection")
    def test_queries_with_correct_filter(self, mock_coll):
        """Should filter by type=session_context."""
        mock_collection = MagicMock()
        mock_collection.query.return_value = {"ids": [[]], "documents": [[]], "metadatas": [[]]}
        mock_coll.return_value = mock_collection

        auto_save.recover_recent_contexts(n_results=5)

        mock_collection.query.assert_called_once()
        call_args = mock_collection.query.call_args
        assert call_args.kwargs["where"] == {"type": "session_context"}
        assert call_args.kwargs["n_results"] == 5

    @patch("auto_save._get_chromadb_collection")
    def test_handles_empty_results(self, mock_coll):
        """Should handle empty query results gracefully."""
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
        }
        mock_coll.return_value = mock_collection

        result = auto_save.recover_recent_contexts()
        assert result == []


# =============================================================================
# Helper function tests
# =============================================================================

class TestGetEntropyState:
    """Tests for _get_entropy_state()."""

    def test_reads_state_file(self, tmp_path):
        """Should read entropy state from file."""
        state_file = tmp_path / ".entropy_state.json"
        state_file.write_text(json.dumps({"tool_count": 42}))

        with patch.object(auto_save, "ENTROPY_STATE_FILE", state_file):
            result = auto_save._get_entropy_state()
            assert result["tool_count"] == 42

    def test_returns_empty_on_missing_file(self, tmp_path):
        """Should return empty dict if state file missing."""
        with patch.object(auto_save, "ENTROPY_STATE_FILE", tmp_path / "nope.json"):
            result = auto_save._get_entropy_state()
            assert result == {}

    def test_returns_empty_on_corrupt_file(self, tmp_path):
        """Should return empty dict if state file is corrupted."""
        state_file = tmp_path / ".entropy_state.json"
        state_file.write_text("not json{{{")

        with patch.object(auto_save, "ENTROPY_STATE_FILE", state_file):
            result = auto_save._get_entropy_state()
            assert result == {}


class TestGetGitInfo:
    """Tests for _get_git_info()."""

    @patch("subprocess.run")
    def test_returns_branch_and_commits(self, mock_run):
        """Should return git branch and recent commits."""
        mock_run.side_effect = [
            MagicMock(stdout="master\n", returncode=0),
            MagicMock(stdout="abc Fix\ndef Add\n", returncode=0),
        ]
        result = auto_save._get_git_info()
        assert result["branch"] == "master"
        assert len(result["recent_commits"]) == 2

    @patch("subprocess.run", side_effect=Exception("no git"))
    def test_handles_git_failure(self, mock_run):
        """Should return defaults when git unavailable."""
        result = auto_save._get_git_info()
        assert result["branch"] == "unknown"
        assert result["recent_commits"] == []


class TestGetModifiedFiles:
    """Tests for _get_modified_files()."""

    @patch("subprocess.run")
    def test_returns_file_list(self, mock_run):
        """Should return list of modified files."""
        mock_run.return_value = MagicMock(stdout="a.py\nb.py\nc.py\n", returncode=0)
        result = auto_save._get_modified_files()
        assert result == ["a.py", "b.py", "c.py"]

    @patch("subprocess.run")
    def test_caps_at_20_files(self, mock_run):
        """Should cap results at 20 files."""
        files = "\n".join(f"file{i}.py" for i in range(30))
        mock_run.return_value = MagicMock(stdout=files, returncode=0)
        result = auto_save._get_modified_files()
        assert len(result) == 20

    @patch("subprocess.run", side_effect=Exception("error"))
    def test_handles_failure(self, mock_run):
        """Should return empty list on failure."""
        result = auto_save._get_modified_files()
        assert result == []


# =============================================================================
# Module-level tests
# =============================================================================

class TestModuleIntegrity:
    """Tests for module structure."""

    def test_auto_save_module_importable(self):
        """auto_save should be importable."""
        assert hasattr(auto_save, "auto_save_context")
        assert hasattr(auto_save, "recover_recent_contexts")

    def test_auto_save_script_compiles(self):
        """auto_save.py should compile without errors."""
        import py_compile
        hook_path = Path(__file__).parent.parent.parent / ".claude" / "hooks" / "auto_save.py"
        py_compile.compile(str(hook_path), doraise=True)
