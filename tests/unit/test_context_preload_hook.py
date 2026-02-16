"""Tests for context preload SessionStart hook.

Per GAP-CONTEXT-PREVENT: Context preloader wired into SessionStart.
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the hook module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".claude" / "hooks"))
import context_preload_hook


class TestGetRecentSessions:
    """Tests for _get_recent_sessions()."""

    def test_returns_recent_evidence_files(self, tmp_path):
        """Should return session names sorted by mtime."""
        for i, name in enumerate(["SESSION-2026-01-01-A.md", "SESSION-2026-01-02-B.md"]):
            p = tmp_path / name
            p.write_text("content")
            # Ensure different mtimes
            import os
            os.utime(p, (1000000 + i * 100, 1000000 + i * 100))
        result = context_preload_hook._get_recent_sessions(tmp_path, limit=5)
        assert result[0] == "SESSION-2026-01-02-B"
        assert result[1] == "SESSION-2026-01-01-A"

    def test_limits_results(self, tmp_path):
        """Should limit to requested count."""
        for i in range(10):
            (tmp_path / f"SESSION-2026-01-{i:02d}-X.md").write_text("content")
        result = context_preload_hook._get_recent_sessions(tmp_path, limit=3)
        assert len(result) == 3

    def test_skips_test_artifacts(self, tmp_path):
        """Should skip CHAT-TEST and CHAT-FAIL sessions."""
        (tmp_path / "SESSION-2026-01-01-CHAT-TEST.md").write_text("test")
        (tmp_path / "SESSION-2026-01-01-CHAT-FAIL.md").write_text("fail")
        (tmp_path / "SESSION-2026-01-01-CHAT-BOOM.md").write_text("boom")
        (tmp_path / "SESSION-2026-01-01-REAL-WORK.md").write_text("real")
        result = context_preload_hook._get_recent_sessions(tmp_path)
        assert len(result) == 1
        assert "REAL-WORK" in result[0]

    def test_empty_directory(self, tmp_path):
        """Should return empty list for empty dir."""
        result = context_preload_hook._get_recent_sessions(tmp_path)
        assert result == []

    def test_nonexistent_directory(self, tmp_path):
        """Should return empty list for missing dir."""
        result = context_preload_hook._get_recent_sessions(tmp_path / "nope")
        assert result == []

    def test_ignores_non_session_files(self, tmp_path):
        """Should only match SESSION-*.md pattern."""
        (tmp_path / "DECISION-001.md").write_text("decision")
        (tmp_path / "README.md").write_text("readme")
        (tmp_path / "SESSION-2026-01-01-WORK.md").write_text("session")
        result = context_preload_hook._get_recent_sessions(tmp_path)
        assert len(result) == 1


class TestMainHookOutput:
    """Tests for main() hook output format."""

    @patch("context_preload_hook.PROJECT_ROOT", new_callable=lambda: MagicMock)
    @patch("context_preload_hook.preload_session_context", create=True)
    def test_outputs_valid_json(self, mock_preload, mock_root, tmp_path, capsys):
        """Should output valid additionalContext JSON."""
        # Setup mocks
        mock_context = MagicMock()
        mock_context.to_agent_prompt.return_value = "## Strategic Context\nTest"

        with patch("governance.context_preloader.preload_session_context", return_value=mock_context):
            with patch.object(context_preload_hook, "PROJECT_ROOT", tmp_path):
                # Create evidence dir with a session
                evidence_dir = tmp_path / "evidence"
                evidence_dir.mkdir()
                (evidence_dir / "SESSION-2026-01-01-WORK.md").write_text("evidence")

                # Create gap index
                gaps_dir = tmp_path / "docs" / "gaps"
                gaps_dir.mkdir(parents=True)
                (gaps_dir / "GAP-INDEX.md").write_text("| OPEN |")

                with pytest.raises(SystemExit) as exc:
                    context_preload_hook.main()
                assert exc.value.code == 0

                output = capsys.readouterr().out
                data = json.loads(output)
                assert "hookSpecificOutput" in data
                assert data["hookSpecificOutput"]["hookEventName"] == "SessionStart"
                assert "additionalContext" in data["hookSpecificOutput"]

    def test_exits_cleanly_on_no_context(self, tmp_path, capsys):
        """Should exit 0 with no output when no context available."""
        with patch.object(context_preload_hook, "PROJECT_ROOT", tmp_path):
            with patch("governance.context_preloader.preload_session_context", side_effect=ImportError("no module")):
                with pytest.raises(SystemExit) as exc:
                    context_preload_hook.main()
                # Even with partial failure, should still collect gaps/sessions
                assert exc.value.code == 0

    def test_hook_is_executable(self):
        """Hook script should exist and be syntactically valid."""
        hook_path = Path(__file__).parent.parent.parent / ".claude" / "hooks" / "context_preload_hook.py"
        assert hook_path.exists()
        # Verify it compiles
        import py_compile
        py_compile.compile(str(hook_path), doraise=True)


class TestSettingsWiring:
    """Tests for settings.local.json hook registration."""

    def test_context_preload_hook_registered(self):
        """Context preload hook should be in SessionStart hooks."""
        settings_path = Path(__file__).parent.parent.parent / ".claude" / "settings.local.json"
        settings = json.loads(settings_path.read_text())
        session_start = settings["hooks"]["SessionStart"]

        # Find the main hooks block (no matcher)
        main_block = None
        for block in session_start:
            if "matcher" not in block:
                main_block = block
                break

        assert main_block is not None, "Main SessionStart hooks block not found"
        commands = [h["command"] for h in main_block["hooks"]]
        hook_found = any("context_preload_hook.py" in cmd for cmd in commands)
        assert hook_found, f"context_preload_hook.py not found in SessionStart commands: {commands}"

    def test_context_preload_has_reasonable_timeout(self):
        """Hook should have timeout <= 5 seconds."""
        settings_path = Path(__file__).parent.parent.parent / ".claude" / "settings.local.json"
        settings = json.loads(settings_path.read_text())
        session_start = settings["hooks"]["SessionStart"]

        for block in session_start:
            if "matcher" not in block:
                for hook in block["hooks"]:
                    if "context_preload_hook.py" in hook.get("command", ""):
                        assert hook.get("timeout", 10) <= 5
                        return

        pytest.fail("context_preload_hook not found in settings")


class TestPreloaderIntegration:
    """Integration tests for the preloader module."""

    def test_preload_session_context_importable(self):
        """preload_session_context should be importable."""
        from governance.context_preloader import preload_session_context
        assert callable(preload_session_context)

    def test_context_summary_to_agent_prompt(self):
        """ContextSummary.to_agent_prompt() should return markdown."""
        from governance.context_preloader import ContextSummary, Decision
        ctx = ContextSummary(
            decisions=[Decision(
                id="DECISION-001", name="Test", status="APPROVED",
                date="2026-01-01", summary="A test decision",
            )],
            active_phase="Phase 5",
            open_gaps_count=3,
        )
        prompt = ctx.to_agent_prompt()
        assert "DECISION-001" in prompt
        assert "Phase 5" in prompt
        assert "Strategic Context" in prompt

    def test_preloader_handles_missing_dirs(self, tmp_path):
        """Should handle missing evidence/docs dirs gracefully."""
        from governance.context_preloader import ContextPreloader
        preloader = ContextPreloader(project_root=tmp_path)
        ctx = preloader.load_context()
        assert ctx.decisions == []
        assert ctx.technology_choices == []
        assert ctx.open_gaps_count == 0
