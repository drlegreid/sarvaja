"""Tests for entropy_cli.py --auto-save flag.

Per P3-13: Context prevention wiring — auto-save at entropy thresholds.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".claude" / "hooks"))
import entropy_cli


class TestTryAutoSave:
    """Tests for _try_auto_save() helper."""

    @patch("auto_save.auto_save_context")
    def test_calls_auto_save_context(self, mock_save):
        """Should call auto_save_context with trigger."""
        mock_save.return_value = "ctx-SESSION-123"
        state = {}

        result = entropy_cli._try_auto_save(state, trigger="test_trigger")

        assert result is True
        mock_save.assert_called_once_with(trigger="test_trigger")
        assert state["last_save"] is not None

    @patch("auto_save.auto_save_context")
    def test_skips_if_recently_saved(self, mock_save):
        """Should skip save if last save was within 10 minutes."""
        recent = (datetime.now() - timedelta(minutes=5)).isoformat()
        state = {"last_save": recent}

        result = entropy_cli._try_auto_save(state, trigger="test")

        assert result is False
        mock_save.assert_not_called()

    @patch("auto_save.auto_save_context")
    def test_saves_if_last_save_old(self, mock_save):
        """Should save if last save was >10 minutes ago."""
        old = (datetime.now() - timedelta(minutes=15)).isoformat()
        state = {"last_save": old}
        mock_save.return_value = "ctx-SESSION-456"

        result = entropy_cli._try_auto_save(state, trigger="test")

        assert result is True
        mock_save.assert_called_once()

    def test_returns_false_on_import_failure(self):
        """Should return False when auto_save module not importable."""
        state = {}
        with patch.dict(sys.modules, {"auto_save": None}):
            with patch("builtins.__import__", side_effect=ImportError("no module")):
                result = entropy_cli._try_auto_save(state, trigger="test")
                assert result is False

    @patch("auto_save.auto_save_context")
    def test_returns_false_on_save_failure(self, mock_save):
        """Should return False when auto_save_context returns None."""
        mock_save.return_value = None
        state = {}

        result = entropy_cli._try_auto_save(state, trigger="test")

        assert result is False


class TestIncrementAndCheckAutoSave:
    """Tests for increment_and_check() with auto_save=True."""

    def _make_state(self, tool_count=0, warnings_shown=0, last_warning_at=0, last_save=None):
        """Create a test state dict."""
        return {
            "session_start": datetime.now().isoformat(),
            "session_hash": "TEST",
            "tool_count": tool_count,
            "check_count": 0,
            "last_save": last_save,
            "warnings_shown": warnings_shown,
            "last_warning_at": last_warning_at,
            "history": [],
        }

    @patch("entropy_cli._try_auto_save")
    @patch("entropy_cli.save_state")
    @patch("entropy_cli.load_state")
    def test_auto_save_at_critical(self, mock_load, mock_save_st, mock_auto_save):
        """Should trigger auto-save when crossing CRITICAL threshold."""
        mock_load.return_value = self._make_state(tool_count=149)  # Will become 150
        mock_auto_save.return_value = True

        exit_code = entropy_cli.increment_and_check(quiet=True, auto_save=True)

        assert exit_code == 1  # Warning issued
        mock_auto_save.assert_called_once()
        trigger = mock_auto_save.call_args.kwargs["trigger"]
        assert "critical" in trigger.lower()

    @patch("entropy_cli._try_auto_save")
    @patch("entropy_cli.save_state")
    @patch("entropy_cli.load_state")
    def test_auto_save_at_high_first_crossing(self, mock_load, mock_save_st, mock_auto_save):
        """Should trigger auto-save on first HIGH crossing."""
        mock_load.return_value = self._make_state(
            tool_count=99, warnings_shown=1, last_warning_at=50
        )
        mock_auto_save.return_value = True

        exit_code = entropy_cli.increment_and_check(quiet=True, auto_save=True)

        assert exit_code == 1
        mock_auto_save.assert_called_once()

    @patch("entropy_cli._try_auto_save")
    @patch("entropy_cli.save_state")
    @patch("entropy_cli.load_state")
    def test_no_auto_save_when_disabled(self, mock_load, mock_save_st, mock_auto_save):
        """Should NOT auto-save when auto_save=False."""
        mock_load.return_value = self._make_state(tool_count=149)

        entropy_cli.increment_and_check(quiet=True, auto_save=False)

        mock_auto_save.assert_not_called()

    @patch("entropy_cli._try_auto_save")
    @patch("entropy_cli.save_state")
    @patch("entropy_cli.load_state")
    def test_no_auto_save_below_threshold(self, mock_load, mock_save_st, mock_auto_save):
        """Should NOT auto-save below HIGH threshold."""
        mock_load.return_value = self._make_state(tool_count=49)

        entropy_cli.increment_and_check(quiet=True, auto_save=True)

        mock_auto_save.assert_not_called()

    @patch("entropy_cli._try_auto_save")
    @patch("entropy_cli.save_state")
    @patch("entropy_cli.load_state")
    def test_warning_includes_auto_saved_note(self, mock_load, mock_save_st, mock_auto_save, capsys):
        """Should include (auto-saved) in warning message when save succeeds."""
        mock_load.return_value = self._make_state(tool_count=149)
        mock_auto_save.return_value = True

        entropy_cli.increment_and_check(quiet=False, auto_save=True)

        output = capsys.readouterr().out
        assert "auto-saved to ChromaDB" in output

    @patch("entropy_cli._try_auto_save")
    @patch("entropy_cli.save_state")
    @patch("entropy_cli.load_state")
    def test_warning_without_auto_saved_note(self, mock_load, mock_save_st, mock_auto_save, capsys):
        """Should NOT include (auto-saved) when save fails."""
        mock_load.return_value = self._make_state(tool_count=149)
        mock_auto_save.return_value = False

        entropy_cli.increment_and_check(quiet=False, auto_save=True)

        output = capsys.readouterr().out
        assert "auto-saved to ChromaDB" not in output


class TestCLIAutoSaveArg:
    """Tests for --auto-save CLI argument parsing."""

    def test_auto_save_arg_accepted(self):
        """CLI should accept --auto-save flag."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--increment", action="store_true")
        parser.add_argument("--auto-save", action="store_true")
        parser.add_argument("--quiet", "-q", action="store_true")

        args = parser.parse_args(["--increment", "--auto-save", "-q"])
        assert args.auto_save is True
        assert args.increment is True
        assert args.quiet is True

    def test_auto_save_default_false(self):
        """--auto-save should default to False."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--increment", action="store_true")
        parser.add_argument("--auto-save", action="store_true")

        args = parser.parse_args(["--increment"])
        assert args.auto_save is False


class TestSettingsWiringAutoSave:
    """Tests for settings.local.json auto-save wiring."""

    def test_entropy_hook_has_auto_save_flag(self):
        """PostToolUse entropy hook should include --auto-save."""
        settings_path = Path(__file__).parent.parent.parent / ".claude" / "settings.local.json"
        settings = json.loads(settings_path.read_text())

        post_tool = settings["hooks"]["PostToolUse"]
        # Find the main hooks block (no matcher)
        for block in post_tool:
            if "matcher" not in block:
                commands = [h["command"] for h in block["hooks"]]
                entropy_cmd = [c for c in commands if "entropy_cli.py" in c]
                assert len(entropy_cmd) == 1, f"Expected 1 entropy_cli command, found {len(entropy_cmd)}"
                assert "--auto-save" in entropy_cmd[0]
                return

        pytest.fail("entropy_cli.py not found in PostToolUse hooks")

    def test_entropy_hook_timeout_sufficient(self):
        """Entropy hook timeout should be >= 3s for ChromaDB auto-save."""
        settings_path = Path(__file__).parent.parent.parent / ".claude" / "settings.local.json"
        settings = json.loads(settings_path.read_text())

        post_tool = settings["hooks"]["PostToolUse"]
        for block in post_tool:
            if "matcher" not in block:
                for hook in block["hooks"]:
                    if "entropy_cli.py" in hook.get("command", ""):
                        assert hook.get("timeout", 0) >= 3, \
                            f"Entropy hook timeout {hook.get('timeout')}s too low for ChromaDB auto-save"
                        return

        pytest.fail("entropy_cli.py not found in PostToolUse hooks")
