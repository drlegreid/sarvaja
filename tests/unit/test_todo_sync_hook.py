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
