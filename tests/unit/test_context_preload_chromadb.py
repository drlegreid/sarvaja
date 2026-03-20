"""Tests for context_preload_hook.py ChromaDB recovery enhancement.

Per P3-13: SessionStart hook preloads recent context from ChromaDB.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".claude" / "hooks"))
import context_preload_hook


class TestRecoverChromadbContexts:
    """Tests for _recover_chromadb_contexts()."""

    @patch("auto_save.recover_recent_contexts")
    def test_returns_summaries(self, mock_recover):
        """Should return formatted summary strings."""
        mock_recover.return_value = [
            {
                "id": "ctx-SESSION-A",
                "document": "content A",
                "metadata": {
                    "session_id": "SESSION-A",
                    "tool_count": 120,
                    "trigger": "entropy_high_100",
                },
            },
            {
                "id": "ctx-SESSION-B",
                "document": "content B",
                "metadata": {
                    "session_id": "SESSION-B",
                    "tool_count": 50,
                    "trigger": "manual_test",
                },
            },
        ]

        result = context_preload_hook._recover_chromadb_contexts(limit=2)

        assert len(result) == 2
        assert "SESSION-A" in result[0]
        assert "120" in result[0]
        assert "SESSION-B" in result[1]

    @patch("auto_save.recover_recent_contexts")
    def test_returns_empty_on_no_contexts(self, mock_recover):
        """Should return empty list when no saved contexts."""
        mock_recover.return_value = []
        result = context_preload_hook._recover_chromadb_contexts()
        assert result == []

    def test_returns_empty_on_import_failure(self):
        """Should return empty list when auto_save module unavailable."""
        with patch.dict(sys.modules, {"auto_save": None}):
            with patch("builtins.__import__", side_effect=ImportError("no module")):
                result = context_preload_hook._recover_chromadb_contexts()
                assert result == []

    @patch("auto_save.recover_recent_contexts")
    def test_handles_missing_metadata(self, mock_recover):
        """Should handle contexts with missing metadata fields."""
        mock_recover.return_value = [
            {"id": "ctx-X", "document": "doc", "metadata": {}},
        ]
        result = context_preload_hook._recover_chromadb_contexts()
        assert len(result) == 1
        assert "unknown" in result[0]

    @patch("auto_save.recover_recent_contexts")
    def test_passes_limit_through(self, mock_recover):
        """Should pass limit to recover_recent_contexts."""
        mock_recover.return_value = []
        context_preload_hook._recover_chromadb_contexts(limit=7)
        mock_recover.assert_called_once_with(n_results=7)


class TestMainWithChromaRecovery:
    """Tests for main() including ChromaDB recovery section."""

    @patch("context_preload_hook._recover_chromadb_contexts")
    def test_includes_chromadb_section(self, mock_recover, tmp_path, capsys):
        """Should include ChromaDB section in output when contexts exist."""
        mock_recover.return_value = [
            "- **SESSION-2026-03-20-AUTO-AB12** (tools: 120, trigger: entropy_high_100)"
        ]

        with patch.object(context_preload_hook, "PROJECT_ROOT", tmp_path):
            with patch("governance.context_preloader.preload_session_context", side_effect=ImportError):
                with pytest.raises(SystemExit) as exc:
                    context_preload_hook.main()
                assert exc.value.code == 0

        output = capsys.readouterr().out
        data = json.loads(output)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        assert "Recovered Session Contexts" in ctx
        assert "SESSION-2026-03-20-AUTO-AB12" in ctx

    @patch("context_preload_hook._recover_chromadb_contexts")
    def test_omits_chromadb_section_when_empty(self, mock_recover, tmp_path, capsys):
        """Should omit ChromaDB section when no contexts saved."""
        mock_recover.return_value = []

        with patch.object(context_preload_hook, "PROJECT_ROOT", tmp_path):
            # Create at least one evidence file so hook has something to output
            evidence_dir = tmp_path / "evidence"
            evidence_dir.mkdir()
            (evidence_dir / "SESSION-2026-01-01-WORK.md").write_text("evidence")

            with patch("governance.context_preloader.preload_session_context", side_effect=ImportError):
                with pytest.raises(SystemExit) as exc:
                    context_preload_hook.main()
                assert exc.value.code == 0

        output = capsys.readouterr().out
        data = json.loads(output)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        assert "Recovered Session Contexts" not in ctx

    @patch("context_preload_hook._recover_chromadb_contexts")
    def test_chromadb_failure_doesnt_break_hook(self, mock_recover, tmp_path, capsys):
        """ChromaDB failure should not prevent other context from loading."""
        mock_recover.side_effect = Exception("ChromaDB down")

        with patch.object(context_preload_hook, "PROJECT_ROOT", tmp_path):
            evidence_dir = tmp_path / "evidence"
            evidence_dir.mkdir()
            (evidence_dir / "SESSION-2026-01-01-WORK.md").write_text("evidence")

            with patch("governance.context_preloader.preload_session_context", side_effect=ImportError):
                with pytest.raises(SystemExit) as exc:
                    context_preload_hook.main()
                assert exc.value.code == 0

        output = capsys.readouterr().out
        data = json.loads(output)
        # Should still have other sections (evidence, partial error)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        assert "Recent Sessions" in ctx


class TestHookPaths:
    """Tests for hook path setup."""

    def test_hooks_dir_on_sys_path(self):
        """HOOKS_DIR should be on sys.path for auto_save import."""
        hooks_dir = str(Path(__file__).parent.parent.parent / ".claude" / "hooks")
        assert hooks_dir in sys.path

    def test_context_preload_hook_compiles(self):
        """Hook should compile without errors."""
        import py_compile
        hook_path = Path(__file__).parent.parent.parent / ".claude" / "hooks" / "context_preload_hook.py"
        py_compile.compile(str(hook_path), doraise=True)
