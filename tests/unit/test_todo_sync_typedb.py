"""
Tests for TypeDB → TODO.md One-Way Sync Service (Phase 8).

Per GOV-MCP-FIRST-01-v1: TypeDB is source of truth. TODO.md is
fallback visibility only. This service syncs TypeDB tasks → TODO.md
for human-readable reference, and imports fallback tasks back when
MCP recovers.

BDD Scenarios:
  - Task creation via MCP syncs to TODO.md
  - Fallback tasks imported on MCP recovery
  - Session start loads tasks from TypeDB
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

import sys
import os

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestFormatTaskLine:
    """Tests for _format_task_line() — single task → markdown."""

    def test_format_todo_task(self):
        """TODO status renders as unchecked checkbox."""
        from governance.services.todo_sync import _format_task_line
        task = {"task_id": "BUG-001", "name": "Fix login", "status": "TODO"}
        line = _format_task_line(task)
        assert "- [ ]" in line
        assert "BUG-001" in line
        assert "Fix login" in line

    def test_format_in_progress_task(self):
        """IN_PROGRESS renders with progress indicator."""
        from governance.services.todo_sync import _format_task_line
        task = {"task_id": "FEAT-002", "name": "Add search", "status": "IN_PROGRESS"}
        line = _format_task_line(task)
        assert "- [~]" in line or "IN_PROGRESS" in line
        assert "FEAT-002" in line

    def test_format_done_task(self):
        """DONE status renders as checked checkbox."""
        from governance.services.todo_sync import _format_task_line
        task = {"task_id": "TASK-003", "name": "Write tests", "status": "DONE"}
        line = _format_task_line(task)
        assert "- [x]" in line
        assert "TASK-003" in line

    def test_format_includes_priority_when_present(self):
        """Priority is shown when available."""
        from governance.services.todo_sync import _format_task_line
        task = {
            "task_id": "BUG-004", "name": "Critical bug",
            "status": "TODO", "priority": "CRITICAL",
        }
        line = _format_task_line(task)
        assert "CRITICAL" in line

    def test_format_handles_missing_fields(self):
        """Minimal task dict doesn't crash."""
        from governance.services.todo_sync import _format_task_line
        task = {"task_id": "X-001", "status": "TODO"}
        line = _format_task_line(task)
        assert "X-001" in line


class TestSyncTypedbToTodomd:
    """Tests for sync_typedb_to_todomd() — TypeDB → TODO.md."""

    def test_fetches_tasks_from_api(self):
        """Calls GET /api/tasks to fetch TypeDB tasks."""
        from governance.services.todo_sync import sync_typedb_to_todomd

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "tasks": [
                {"task_id": "T-001", "name": "Task 1", "status": "TODO"},
                {"task_id": "T-002", "name": "Task 2", "status": "DONE"},
            ],
            "total": 2,
        }

        with patch("httpx.get", return_value=mock_resp) as mock_get:
            result = sync_typedb_to_todomd(
                todo_md_path="/tmp/test_todo.md",
                api_base="http://localhost:8082",
            )
        mock_get.assert_called_once()
        assert "api/tasks" in mock_get.call_args[0][0]
        assert result.fetched == 2

    def test_writes_formatted_output(self, tmp_path):
        """Writes task lines to TODO.md file."""
        from governance.services.todo_sync import sync_typedb_to_todomd

        todo_file = tmp_path / "TODO.md"
        todo_file.write_text("# TODO Index\n\n---\n\n## Synced Tasks\n")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "tasks": [
                {"task_id": "T-001", "name": "Fix bug", "status": "TODO"},
            ],
            "total": 1,
        }

        with patch("httpx.get", return_value=mock_resp):
            sync_typedb_to_todomd(
                todo_md_path=str(todo_file),
                api_base="http://localhost:8082",
            )
        content = todo_file.read_text()
        assert "T-001" in content
        assert "Fix bug" in content

    def test_preserves_header(self, tmp_path):
        """Keeps TODO.md header and metadata intact."""
        from governance.services.todo_sync import sync_typedb_to_todomd

        header = "# TODO Index - Sarvaja\n\n**Last Updated:** 2026-01-20\n\n---\n"
        todo_file = tmp_path / "TODO.md"
        todo_file.write_text(header)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"tasks": [], "total": 0}

        with patch("httpx.get", return_value=mock_resp):
            sync_typedb_to_todomd(
                todo_md_path=str(todo_file),
                api_base="http://localhost:8082",
            )
        content = todo_file.read_text()
        assert "# TODO Index - Sarvaja" in content

    def test_handles_api_down_gracefully(self, tmp_path):
        """Returns zero count when API is unreachable."""
        from governance.services.todo_sync import sync_typedb_to_todomd
        import httpx

        todo_file = tmp_path / "TODO.md"
        todo_file.write_text("# TODO\n")

        with patch("httpx.get", side_effect=httpx.ConnectError("refused")):
            result = sync_typedb_to_todomd(
                todo_md_path=str(todo_file),
                api_base="http://localhost:8082",
            )
        assert result.fetched == 0
        assert result.error is not None

    def test_maps_statuses_correctly(self, tmp_path):
        """TypeDB statuses map to correct markdown checkboxes."""
        from governance.services.todo_sync import sync_typedb_to_todomd

        todo_file = tmp_path / "TODO.md"
        todo_file.write_text("# TODO\n")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "tasks": [
                {"task_id": "A", "name": "Open", "status": "TODO"},
                {"task_id": "B", "name": "Working", "status": "IN_PROGRESS"},
                {"task_id": "C", "name": "Done", "status": "DONE"},
            ],
            "total": 3,
        }

        with patch("httpx.get", return_value=mock_resp):
            sync_typedb_to_todomd(
                todo_md_path=str(todo_file),
                api_base="http://localhost:8082",
            )
        content = todo_file.read_text()
        assert "- [ ]" in content  # TODO
        assert "- [x]" in content  # DONE


class TestSyncFallbackToTypedb:
    """Tests for sync_fallback_to_typedb() — TODO.md → TypeDB recovery."""

    def test_posts_fallback_tasks_to_api(self, tmp_path):
        """Reads TODO.md tasks and POSTs them to TypeDB API."""
        from governance.services.todo_sync import sync_fallback_to_typedb

        state_file = tmp_path / ".todo_sync_state.json"
        state = {
            "synced_todos": {
                "TODO-FIX-LOGIN-BUG": {
                    "status": "TODO",
                    "content": "Fix login bug",
                    "synced_at": "2026-03-21T10:00:00",
                    "source": "fallback",
                },
            },
            "last_sync": "2026-03-21T10:00:00",
        }
        state_file.write_text(json.dumps(state))

        mock_resp = MagicMock()
        mock_resp.status_code = 404  # Task doesn't exist in TypeDB
        mock_post = MagicMock()
        mock_post.is_success = True

        with patch("httpx.Client") as mock_client_cls:
            client = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=client)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            client.get.return_value = mock_resp
            client.post.return_value = mock_post

            result = sync_fallback_to_typedb(
                state_path=str(state_file),
                api_base="http://localhost:8082",
            )
        assert result.synced >= 1

    def test_skips_already_synced_non_fallback(self, tmp_path):
        """Tasks not marked as 'fallback' source are skipped."""
        from governance.services.todo_sync import sync_fallback_to_typedb

        state_file = tmp_path / ".todo_sync_state.json"
        state = {
            "synced_todos": {
                "TODO-NORMAL-TASK": {
                    "status": "DONE",
                    "content": "Normal task",
                    "synced_at": "2026-03-21T10:00:00",
                    # No "source": "fallback" — was synced normally
                },
            },
        }
        state_file.write_text(json.dumps(state))

        result = sync_fallback_to_typedb(
            state_path=str(state_file),
            api_base="http://localhost:8082",
        )
        assert result.synced == 0

    def test_marks_synced_after_import(self, tmp_path):
        """Successfully imported tasks get source updated to 'synced'."""
        from governance.services.todo_sync import sync_fallback_to_typedb

        state_file = tmp_path / ".todo_sync_state.json"
        state = {
            "synced_todos": {
                "TODO-RECOVER-TASK": {
                    "status": "TODO",
                    "content": "Recover task",
                    "synced_at": "2026-03-21T10:00:00",
                    "source": "fallback",
                },
            },
        }
        state_file.write_text(json.dumps(state))

        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_post = MagicMock()
        mock_post.is_success = True

        with patch("httpx.Client") as mock_client_cls:
            client = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=client)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            client.get.return_value = mock_resp
            client.post.return_value = mock_post

            sync_fallback_to_typedb(
                state_path=str(state_file),
                api_base="http://localhost:8082",
            )

        updated_state = json.loads(state_file.read_text())
        todo = updated_state["synced_todos"]["TODO-RECOVER-TASK"]
        assert todo["source"] == "synced"

    def test_handles_api_error_gracefully(self, tmp_path):
        """API errors don't crash — returns error in result."""
        from governance.services.todo_sync import sync_fallback_to_typedb
        import httpx

        state_file = tmp_path / ".todo_sync_state.json"
        state = {
            "synced_todos": {
                "TODO-FAIL-TASK": {
                    "status": "TODO",
                    "content": "Fail task",
                    "source": "fallback",
                },
            },
        }
        state_file.write_text(json.dumps(state))

        with patch("httpx.Client", side_effect=httpx.ConnectError("refused")):
            result = sync_fallback_to_typedb(
                state_path=str(state_file),
                api_base="http://localhost:8082",
            )
        assert result.failed >= 1


class TestSyncResult:
    """Tests for SyncResult dataclass."""

    def test_sync_result_has_expected_fields(self):
        """SyncResult has fetched, synced, failed, error."""
        from governance.services.todo_sync import SyncResult
        r = SyncResult(fetched=10, synced=8, failed=2, error=None)
        assert r.fetched == 10
        assert r.synced == 8
        assert r.failed == 2
        assert r.error is None

    def test_sync_result_with_error(self):
        """SyncResult can carry an error message."""
        from governance.services.todo_sync import SyncResult
        r = SyncResult(fetched=0, synced=0, failed=0, error="Connection refused")
        assert r.error == "Connection refused"
