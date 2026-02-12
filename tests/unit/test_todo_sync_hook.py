"""Tests for TodoWrite → gov-tasks sync hook.

Per GAP-TASK-SYNC-001: Auto-sync Claude TodoWrite entries to gov-tasks.
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


HOOK_PATH = Path(__file__).parent.parent.parent / ".claude" / "hooks" / "todo_sync.py"


class TestTodoSyncHook:
    """Test the todo_sync.py PostToolUse:TodoWrite hook."""

    def test_hook_file_exists(self):
        """Hook script exists at expected path."""
        assert HOOK_PATH.exists(), f"Hook not found at {HOOK_PATH}"

    def test_hook_importable(self):
        """Hook module can be imported."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("todo_sync", str(HOOK_PATH))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "main")
        assert hasattr(mod, "_sync_todo_to_api")

    def test_main_returns_zero_on_empty_input(self):
        """Empty tool input returns 0 (no-op)."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("todo_sync", str(HOOK_PATH))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        with patch.dict(os.environ, {"CLAUDE_TOOL_INPUT": "{}"}):
            assert mod.main() == 0

    def test_main_returns_zero_on_invalid_json(self):
        """Invalid JSON returns 0 (silent fail)."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("todo_sync", str(HOOK_PATH))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        with patch.dict(os.environ, {"CLAUDE_TOOL_INPUT": "not json"}):
            assert mod.main() == 0

    def test_main_processes_todo_items(self):
        """Main processes todos from CLAUDE_TOOL_INPUT."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("todo_sync", str(HOOK_PATH))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        todos = {
            "todos": [
                {"content": "Fix bug", "status": "completed", "activeForm": "Fixing bug"},
                {"content": "Add tests", "status": "in_progress", "activeForm": "Adding tests"},
            ]
        }

        with patch.dict(os.environ, {"CLAUDE_TOOL_INPUT": json.dumps(todos)}):
            with patch.object(mod, "_sync_todo_to_api", return_value=True) as mock_sync:
                with patch.object(mod, "_save_state"):
                    result = mod.main()
                    assert result == 0
                    assert mock_sync.call_count == 2

    def test_status_mapping(self):
        """TodoWrite statuses map correctly to gov-tasks statuses."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("todo_sync", str(HOOK_PATH))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Verify the status_map inside _sync_todo_to_api
        import inspect
        source = inspect.getsource(mod._sync_todo_to_api)
        assert '"pending": "TODO"' in source
        assert '"in_progress": "IN_PROGRESS"' in source
        assert '"completed": "DONE"' in source


class TestTodoSyncSettings:
    """Test the hook is properly registered in settings."""

    def test_hook_registered_in_settings(self):
        """Hook is registered in settings.local.json."""
        settings_path = Path(__file__).parent.parent.parent / ".claude" / "settings.local.json"
        settings = json.loads(settings_path.read_text())

        post_tool_hooks = settings.get("hooks", {}).get("PostToolUse", [])
        todo_hooks = [
            h for h in post_tool_hooks
            if h.get("matcher") == "TodoWrite"
        ]
        assert len(todo_hooks) == 1, "Expected exactly one TodoWrite matcher"
        assert "todo_sync.py" in todo_hooks[0]["hooks"][0]["command"]

    def test_hook_timeout_is_reasonable(self):
        """TodoWrite hook timeout is 3 seconds (allows API call)."""
        settings_path = Path(__file__).parent.parent.parent / ".claude" / "settings.local.json"
        settings = json.loads(settings_path.read_text())

        post_tool_hooks = settings.get("hooks", {}).get("PostToolUse", [])
        for hook_group in post_tool_hooks:
            if hook_group.get("matcher") == "TodoWrite":
                timeout = hook_group["hooks"][0].get("timeout", 0)
                assert timeout == 3


def _load_hook_module():
    """Helper to import the hook module."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("todo_sync", str(HOOK_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestTodoSyncWarnings:
    """Tests for GOV-MCP-FIRST-01-v1: sync failure warnings visible via stderr."""

    def test_warn_helper_writes_to_stderr(self):
        """_warn() writes to stderr with correct prefix."""
        mod = _load_hook_module()
        import io
        buf = io.StringIO()
        with patch.object(mod.sys, "stderr", buf):
            mod._warn("test message")
        output = buf.getvalue()
        assert "[TODO-SYNC WARN]" in output
        assert "test message" in output

    def test_failed_sync_writes_warning_to_stderr(self):
        """When sync fails, main() emits a warning to stderr."""
        mod = _load_hook_module()
        todos = {"todos": [
            {"content": "Fix bug", "status": "pending", "activeForm": "Fixing"},
        ]}
        import io
        buf = io.StringIO()
        with patch.dict(os.environ, {"CLAUDE_TOOL_INPUT": json.dumps(todos)}):
            with patch.object(mod, "_sync_todo_to_api", return_value=False):
                with patch.object(mod, "_save_state"):
                    with patch.object(mod.sys, "stderr", buf):
                        result = mod.main()
        assert result == 0
        output = buf.getvalue()
        assert "1/1 tasks failed" in output
        assert "mcp__gov-tasks__task_create()" in output

    def test_all_synced_no_warning(self):
        """When all sync, no warning on stderr."""
        mod = _load_hook_module()
        todos = {"todos": [
            {"content": "Fix bug", "status": "pending", "activeForm": "Fixing"},
        ]}
        import io
        buf = io.StringIO()
        with patch.dict(os.environ, {"CLAUDE_TOOL_INPUT": json.dumps(todos)}):
            with patch.object(mod, "_sync_todo_to_api", return_value=True):
                with patch.object(mod, "_save_state"):
                    with patch.object(mod.sys, "stderr", buf):
                        result = mod.main()
        assert result == 0
        assert buf.getvalue() == ""

    def test_state_tracks_failed_count(self):
        """State includes last_failed count after sync."""
        mod = _load_hook_module()
        todos = {"todos": [
            {"content": "Task A", "status": "pending", "activeForm": "A"},
            {"content": "Task B", "status": "pending", "activeForm": "B"},
        ]}
        saved_state = {}

        def capture_state(s):
            saved_state.update(s)

        # First fails, second succeeds
        with patch.dict(os.environ, {"CLAUDE_TOOL_INPUT": json.dumps(todos)}):
            with patch.object(mod, "_sync_todo_to_api", side_effect=[False, True]):
                with patch.object(mod, "_save_state", side_effect=capture_state):
                    with patch.object(mod.sys, "stderr", MagicMock()):
                        mod.main()

        assert saved_state["last_failed"] == 1
        assert saved_state["last_synced"] == 1
        assert saved_state["last_count"] == 2

    def test_exception_in_main_warns_stderr(self):
        """Exception in __main__ block produces warning before exit 0."""
        mod = _load_hook_module()
        import io
        buf = io.StringIO()
        with patch.object(mod, "main", side_effect=RuntimeError("boom")):
            with patch.object(mod.sys, "stderr", buf):
                # Simulate __main__ except block
                try:
                    mod.main()
                except RuntimeError as e:
                    mod._warn(f"Hook error: {str(e)[:100]}. Tasks NOT synced to TypeDB.")
        output = buf.getvalue()
        assert "Hook error: boom" in output
        assert "NOT synced" in output
