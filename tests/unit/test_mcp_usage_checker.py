"""
Tests for MCP Usage Pattern Checker.

Per GOV-MCP-FIRST-01-v1: Verify MCP-first enforcement hook behavior.

Tests:
- track_tool: tool counting + category tracking
- Warning threshold: only warns after MIN_TOOL_COUNT
- Warning trigger: TodoWrite without gov-tasks
- Warning suppression: gov-tasks used = no warning
- Max warnings cap
- reset: clears state
- get_summary: returns readable summary
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

import sys
import importlib.util

CHECKER_PATH = (
    Path(__file__).parent.parent.parent
    / ".claude" / "hooks" / "checkers" / "mcp_usage_checker.py"
)

CLI_PATH = (
    Path(__file__).parent.parent.parent
    / ".claude" / "hooks" / "mcp_usage_check.py"
)


def _load_checker():
    """Import the checker module."""
    spec = importlib.util.spec_from_file_location("mcp_usage_checker", str(CHECKER_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_cli():
    """Import the CLI entry point."""
    spec = importlib.util.spec_from_file_location("mcp_usage_check", str(CLI_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestMCPUsageChecker:
    """Core checker module tests."""

    def test_files_exist(self):
        """Both checker module and CLI exist."""
        assert CHECKER_PATH.exists()
        assert CLI_PATH.exists()

    def test_default_state_shape(self):
        """Default state has all required fields."""
        mod = _load_checker()
        state = mod._default_state()
        assert "session_start" in state
        assert state["tool_count"] == 0
        assert state["todowrite_count"] == 0
        assert state["mcp_categories_used"] == {}
        assert state["warnings_issued"] == 0

    def test_no_warning_below_min_threshold(self):
        """No warning before MIN_TOOL_COUNT calls."""
        mod = _load_checker()
        with patch.object(mod, "load_state", return_value=mod._default_state()):
            with patch.object(mod, "save_state"):
                # Call a few times — should be under threshold
                for _ in range(5):
                    result = mod.track_tool("TodoWrite")
                assert result is None

    def test_warning_when_todowrite_without_gov_tasks(self):
        """Warning issued when TodoWrite used >= 2x but gov-tasks not called."""
        mod = _load_checker()
        state = mod._default_state()
        state["tool_count"] = mod.MIN_TOOL_COUNT  # At threshold
        state["todowrite_count"] = 2  # Trigger
        state["mcp_categories_used"] = {}  # No gov-tasks

        with patch.object(mod, "load_state", return_value=state):
            with patch.object(mod, "save_state"):
                with patch.object(mod, "check_mcp_health", return_value=True):
                    result = mod.track_tool("SomeOtherTool")
        assert result is not None
        assert "MCP-FIRST" in result
        assert "mcp__gov-tasks__task_create()" in result

    def test_no_warning_when_gov_tasks_used(self):
        """No warning when gov-tasks MCP has been called."""
        mod = _load_checker()
        state = mod._default_state()
        state["tool_count"] = mod.MIN_TOOL_COUNT
        state["todowrite_count"] = 5
        state["mcp_categories_used"] = {"gov-tasks": 1}  # Used!

        with patch.object(mod, "load_state", return_value=state):
            with patch.object(mod, "save_state"):
                result = mod.track_tool("TodoWrite")
        assert result is None

    def test_max_two_warnings_per_session(self):
        """Only MAX_WARNINGS warnings per session to avoid noise."""
        mod = _load_checker()
        state = mod._default_state()
        state["tool_count"] = 20
        state["todowrite_count"] = 5
        state["warnings_issued"] = mod.MAX_WARNINGS  # Already at cap

        with patch.object(mod, "load_state", return_value=state):
            with patch.object(mod, "save_state"):
                result = mod.track_tool("Read")
        assert result is None  # No more warnings

    def test_tracks_todowrite_count(self):
        """TodoWrite calls are counted."""
        mod = _load_checker()
        saved = {}

        def capture(s):
            saved.update(s)

        state = mod._default_state()
        with patch.object(mod, "load_state", return_value=state):
            with patch.object(mod, "save_state", side_effect=capture):
                mod.track_tool("TodoWrite")
        assert saved["todowrite_count"] == 1

    def test_tracks_mcp_categories(self):
        """MCP tool calls are categorized correctly."""
        mod = _load_checker()
        saved = {}

        def capture(s):
            saved.update(s)

        state = mod._default_state()
        with patch.object(mod, "load_state", return_value=state):
            with patch.object(mod, "save_state", side_effect=capture):
                mod.track_tool("task_create")
        assert saved["mcp_categories_used"].get("gov-tasks") == 1

    def test_tracks_gov_sessions_category(self):
        """Gov-sessions tools tracked."""
        mod = _load_checker()
        saved = {}

        def capture(s):
            saved.update(s)

        state = mod._default_state()
        with patch.object(mod, "load_state", return_value=state):
            with patch.object(mod, "save_state", side_effect=capture):
                mod.track_tool("session_start")
        assert saved["mcp_categories_used"].get("gov-sessions") == 1

    def test_tracks_gov_core_category(self):
        """Gov-core tools tracked."""
        mod = _load_checker()
        saved = {}

        def capture(s):
            saved.update(s)

        state = mod._default_state()
        with patch.object(mod, "load_state", return_value=state):
            with patch.object(mod, "save_state", side_effect=capture):
                mod.track_tool("rule_create")
        assert saved["mcp_categories_used"].get("gov-core") == 1

    def test_reset_clears_state(self):
        """Reset creates fresh default state."""
        mod = _load_checker()
        saved = {}

        def capture(s):
            saved.update(s)

        with patch.object(mod, "save_state", side_effect=capture):
            mod.reset()
        assert saved["tool_count"] == 0
        assert saved["todowrite_count"] == 0
        assert saved["warnings_issued"] == 0

    def test_get_summary_shape(self):
        """get_summary returns expected structure."""
        mod = _load_checker()
        state = mod._default_state()
        state["tool_count"] = 15
        state["todowrite_count"] = 3
        state["mcp_categories_used"] = {"gov-tasks": 2}
        state["warnings_issued"] = 1

        with patch.object(mod, "load_state", return_value=state):
            summary = mod.get_summary()
        assert summary["tool_count"] == 15
        assert summary["todowrite_count"] == 3
        assert summary["mcp_categories"]["gov-tasks"] == 2
        assert summary["warnings_issued"] == 1


class TestMCPUsageCLI:
    """Tests for the thin CLI entry point.

    The CLI imports from checkers.mcp_usage_checker which triggers
    checkers/__init__.py relative imports. We mock the checkers module
    to avoid that import chain in unit tests.
    """

    def _load_cli_with_mocks(self):
        """Load CLI with mocked checker imports to avoid __init__.py chain."""
        # Pre-register the checker module so the CLI import doesn't
        # trigger the full checkers package __init__.py
        checker_mod = _load_checker()
        mock_checkers_pkg = MagicMock()
        mock_checkers_pkg.mcp_usage_checker = checker_mod

        with patch.dict(sys.modules, {
            "checkers": mock_checkers_pkg,
            "checkers.mcp_usage_checker": checker_mod,
        }):
            spec = importlib.util.spec_from_file_location(
                "mcp_usage_check", str(CLI_PATH))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod, checker_mod

    def test_reset_flag(self):
        """--reset calls reset()."""
        mod, checker = self._load_cli_with_mocks()
        with patch.object(sys, "argv", ["mcp_usage_check.py", "--reset"]):
            with patch.object(checker, "reset") as mock_reset:
                # Re-bind after module load
                mod.reset = mock_reset
                result = mod.main()
        assert result == 0

    def test_no_tool_name_returns_zero(self):
        """Empty CLAUDE_TOOL_NAME returns 0 immediately."""
        mod, checker = self._load_cli_with_mocks()
        import os
        with patch.dict(os.environ, {"CLAUDE_TOOL_NAME": ""}):
            with patch.object(sys, "argv", ["mcp_usage_check.py"]):
                result = mod.main()
        assert result == 0

    def test_warning_written_to_stderr(self):
        """When track_tool returns warning, it's written to stderr."""
        mod, checker = self._load_cli_with_mocks()
        import os
        import io
        buf = io.StringIO()
        with patch.dict(os.environ, {"CLAUDE_TOOL_NAME": "TodoWrite"}):
            with patch.object(sys, "argv", ["mcp_usage_check.py"]):
                with patch.object(checker, "track_tool", return_value="[MCP-FIRST] Warning"):
                    mod.track_tool = checker.track_tool
                    with patch.object(sys, "stderr", buf):
                        result = mod.main()
        assert result == 0
        assert "[MCP-FIRST] Warning" in buf.getvalue()

    def test_no_warning_no_stderr(self):
        """When track_tool returns None, no stderr output."""
        mod, checker = self._load_cli_with_mocks()
        import os
        import io
        buf = io.StringIO()
        with patch.dict(os.environ, {"CLAUDE_TOOL_NAME": "Read"}):
            with patch.object(sys, "argv", ["mcp_usage_check.py"]):
                with patch.object(checker, "track_tool", return_value=None):
                    mod.track_tool = checker.track_tool
                    with patch.object(sys, "stderr", buf):
                        result = mod.main()
        assert result == 0
        assert buf.getvalue() == ""


class TestMCPUsageSettings:
    """Verify hooks are wired in settings.local.json."""

    def test_posttooluse_hook_registered(self):
        """mcp_usage_check.py is in PostToolUse hooks."""
        settings_path = Path(__file__).parent.parent.parent / ".claude" / "settings.local.json"
        settings = json.loads(settings_path.read_text())
        post_hooks = settings.get("hooks", {}).get("PostToolUse", [])

        found = False
        for group in post_hooks:
            for hook in group.get("hooks", []):
                if "mcp_usage_check.py" in hook.get("command", ""):
                    if "--reset" not in hook.get("command", ""):
                        found = True
        assert found, "mcp_usage_check.py not found in PostToolUse hooks"

    def test_sessionstart_reset_registered(self):
        """mcp_usage_check.py --reset is in SessionStart hooks."""
        settings_path = Path(__file__).parent.parent.parent / ".claude" / "settings.local.json"
        settings = json.loads(settings_path.read_text())
        start_hooks = settings.get("hooks", {}).get("SessionStart", [])

        found = False
        for group in start_hooks:
            for hook in group.get("hooks", []):
                cmd = hook.get("command", "")
                if "mcp_usage_check.py" in cmd and "--reset" in cmd:
                    found = True
        assert found, "mcp_usage_check.py --reset not found in SessionStart hooks"
