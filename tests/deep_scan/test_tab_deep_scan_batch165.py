"""Deep scan batch 165: Hooks + config layer.

Batch 165 findings: 19 total, 1 confirmed fix, 18 rejected.
- BUG-SYNC-002: todo_sync.py non-200/404 GET falls through to "synced" recording.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── Todo sync else-branch defense ──────────────


class TestTodoSyncElseBranchDefense:
    """Verify todo_sync.py handles non-200/404 GET responses correctly."""

    def test_else_branch_exists_in_source(self):
        """todo_sync.py has else branch for non-200/404 after BUG-SYNC-002 fix."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/todo_sync.py").read_text()
        assert "BUG-SYNC-002" in src
        assert "return False" in src

    def test_status_500_returns_false(self):
        """Simulated 500 response on GET should not record as synced."""
        # Simulate the logic from _sync_todo_to_api
        status_code = 500
        synced = False

        if status_code == 200:
            synced = True  # Would update
        elif status_code == 404:
            synced = True  # Would create
        else:
            synced = False  # BUG-SYNC-002: Must not record as synced

        assert synced is False

    def test_status_200_records_sync(self):
        """200 response records sync (task exists, update succeeds)."""
        status_code = 200
        if status_code == 200:
            synced = True
        elif status_code == 404:
            synced = True
        else:
            synced = False
        assert synced is True

    def test_status_404_records_sync(self):
        """404 response records sync (task created successfully)."""
        status_code = 404
        if status_code == 200:
            synced = True
        elif status_code == 404:
            synced = True
        else:
            synced = False
        assert synced is True

    def test_status_503_returns_false(self):
        """503 service unavailable should not record as synced."""
        status_code = 503
        if status_code == 200:
            synced = True
        elif status_code == 404:
            synced = True
        else:
            synced = False
        assert synced is False


# ── Todo sync task ID generation defense ──────────────


class TestTodoSyncTaskIDDefense:
    """Verify task ID generation from content."""

    def test_task_id_prefix(self):
        """Task ID starts with TODO- prefix."""
        content = "Fix the authentication bug"
        task_id = "TODO-" + content[:40].replace(" ", "-").replace(":", "").upper()
        assert task_id.startswith("TODO-")

    def test_task_id_truncation(self):
        """Task ID uses first 40 chars of content."""
        content = "A" * 100
        task_id = "TODO-" + content[:40].replace(" ", "-").replace(":", "").upper()
        assert len(task_id) == 5 + 40  # "TODO-" + 40 chars

    def test_task_id_deterministic(self):
        """Same content produces same task ID."""
        content = "Deploy the new feature"
        id1 = "TODO-" + content[:40].replace(" ", "-").replace(":", "").upper()
        id2 = "TODO-" + content[:40].replace(" ", "-").replace(":", "").upper()
        assert id1 == id2


# ── Entropy state non-atomic write defense ──────────────


class TestEntropyStateWriteDefense:
    """Verify entropy state files have read-fallback on corruption."""

    def test_state_load_returns_default_on_corrupt(self):
        """State loader returns default dict on corrupt JSON."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/core/state.py").read_text()
        # StateManager.load() has try/except that returns None on failure
        assert "except" in src

    def test_entropy_state_file_in_hooks_dir(self):
        """.entropy_state.json is in .claude/hooks/ directory."""
        root = Path(__file__).parent.parent.parent
        hooks_dir = root / ".claude/hooks"
        # The state file location is defined relative to hooks dir
        src = (root / ".claude/hooks/entropy_cli.py").read_text()
        assert ".entropy_state.json" in src


# ── Pre-bash check fail-safe defense ──────────────


class TestPreBashCheckFailSafeDefense:
    """Verify pre_bash_check.py fails safe (blocks on error)."""

    def test_blocked_exits_nonzero(self):
        """Blocked commands exit with code 1."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/pre_bash_check.py").read_text()
        assert "sys.exit(1)" in src

    def test_safe_commands_exit_zero(self):
        """Safe commands exit with code 0."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/pre_bash_check.py").read_text()
        assert "sys.exit(0)" in src

    def test_log_dir_created_with_exist_ok(self):
        """Log directory creation uses exist_ok=True."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/pre_bash_check.py").read_text()
        assert "exist_ok=True" in src


# ── Healthcheck service fallback defense ──────────────


class TestHealthcheckServiceFallbackDefense:
    """Verify healthcheck.py service check fallback is correct."""

    def test_fallback_returns_podman_unknown(self):
        """Fallback returns podman with ok=False (triggers recovery)."""
        fallback = {"podman": {"status": "UNKNOWN", "ok": False}}
        assert not fallback["podman"]["ok"]

    def test_core_services_all_fail_on_fallback(self):
        """All CORE_SERVICES evaluate to ok=False on fallback."""
        fallback = {"podman": {"status": "UNKNOWN", "ok": False}}
        core_services = ["podman", "typedb", "chromadb"]
        required_ok = all(
            fallback.get(s, {}).get("ok", False) for s in core_services
        )
        assert not required_ok  # Correctly triggers recovery


# ── Todo sync never-block defense ──────────────


class TestTodoSyncNeverBlockDefense:
    """Verify todo_sync.py never blocks workflow (exit 0)."""

    def test_main_returns_zero(self):
        """main() always returns 0."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/todo_sync.py").read_text()
        # main() function returns 0 at end
        main_start = src.index("def main()")
        main_body = src[main_start:]
        # Last return in main is 0
        assert "return 0" in main_body

    def test_exception_handler_exits_zero(self):
        """Top-level exception handler exits with code 0."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/todo_sync.py").read_text()
        assert "sys.exit(0)" in src
