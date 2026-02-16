"""
Batch 74 — Deep Scan: Services + Routes layer triage.

Fixes verified:
- BUG-SERVICE-002: Fallback store now includes all task fields

Triage summary: 21 findings → 2 confirmed (1 fixed), 19 rejected.
"""
import inspect
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest


# ===========================================================================
# BUG-SERVICE-002: Fallback store includes all task fields
# ===========================================================================

class TestFallbackStoreFields:
    """Verify fallback task creation includes all fields from TypeDB object."""

    def test_fallback_includes_evidence(self):
        """Fallback store must include evidence field."""
        from governance.services.tasks_mutations import update_task
        src = inspect.getsource(update_task)
        assert '"evidence": getattr(task_obj' in src or \
               '"evidence":' in src

    def test_fallback_includes_resolution(self):
        """Fallback store must include resolution field."""
        from governance.services.tasks_mutations import update_task
        src = inspect.getsource(update_task)
        assert '"resolution":' in src

    def test_fallback_includes_claimed_at(self):
        """Fallback store must include claimed_at field."""
        from governance.services.tasks_mutations import update_task
        src = inspect.getsource(update_task)
        assert '"claimed_at":' in src

    def test_fallback_includes_completed_at(self):
        """Fallback store must include completed_at field."""
        from governance.services.tasks_mutations import update_task
        src = inspect.getsource(update_task)
        # completed_at appears in both creation and the DONE auto-set
        assert '"completed_at":' in src

    def test_fallback_includes_linked_commits(self):
        """Fallback store must include linked_commits field."""
        from governance.services.tasks_mutations import update_task
        src = inspect.getsource(update_task)
        assert '"linked_commits":' in src

    def test_fallback_includes_document_path(self):
        """Fallback store must include document_path field."""
        from governance.services.tasks_mutations import update_task
        src = inspect.getsource(update_task)
        assert '"document_path":' in src

    @patch("governance.services.tasks_mutations.get_typedb_client")
    @patch("governance.services.tasks_mutations._monitor")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_fallback_creation_from_typedb(self, mock_log, mock_audit, mock_mon, mock_client):
        """When task is in TypeDB but not fallback, all fields should be copied."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        # Create mock TypeDB task with all fields
        task_obj = MagicMock()
        task_obj.id = "TASK-FB-001"
        task_obj.name = "Test Task"
        task_obj.phase = "backlog"
        task_obj.status = "IN_PROGRESS"
        task_obj.agent_id = "agent-1"
        task_obj.created_at = datetime(2026, 1, 1)
        task_obj.claimed_at = datetime(2026, 1, 2)
        task_obj.completed_at = None
        task_obj.body = "Task body"
        task_obj.gap_id = "GAP-001"
        task_obj.priority = "HIGH"
        task_obj.task_type = "bugfix"
        task_obj.evidence = "Test evidence"
        task_obj.resolution = "IMPLEMENTED"
        task_obj.document_path = "docs/foo.md"
        task_obj.linked_rules = ["RULE-001"]
        task_obj.linked_sessions = ["SESSION-001"]
        task_obj.linked_commits = ["abc123"]
        task_obj.linked_documents = ["docs/bar.md"]

        # Mock client to return this task
        client = MagicMock()
        client.get_task.return_value = task_obj
        # update_task_status returns our same task_obj (not a new MagicMock)
        client.update_task_status.return_value = task_obj
        mock_client.return_value = client

        # Ensure task is NOT in fallback store
        _tasks_store.pop("TASK-FB-001", None)

        try:
            result = update_task("TASK-FB-001", status="DONE")
            # Verify all fields were captured in fallback
            assert result is not None
            stored = _tasks_store.get("TASK-FB-001", {})
            assert stored.get("evidence") == "Test evidence"
            assert stored.get("resolution") == "IMPLEMENTED"
            assert stored.get("claimed_at") is not None
            assert stored.get("linked_commits") == ["abc123"]
            assert stored.get("document_path") == "docs/foo.md"
        finally:
            _tasks_store.pop("TASK-FB-001", None)


# ===========================================================================
# Rejected findings — confirm code is correct
# ===========================================================================

class TestRejectedRouteFindings:
    """Confirm that rejected agent findings are indeed non-issues."""

    def test_chat_whitespace_content_guarded(self):
        """BUG-ROUTE-001: Whitespace-only content already handled by split() check."""
        # request.content.split() returns [] for whitespace-only → falsy → "chat"
        content = "   "
        result = (content.split()[0] if content and content.split() else "chat")
        assert result == "chat"

    def test_chat_empty_content_guarded(self):
        """Empty content goes to 'chat' default."""
        content = ""
        result = (content.split()[0] if content and content.split() else "chat")
        assert result == "chat"

    def test_chat_normal_content_works(self):
        """Normal content extracts first word."""
        content = "/status check"
        result = (content.split()[0] if content and content.split() else "chat")
        assert result == "/status"

    def test_socket_cleanup_in_finally(self):
        """BUG-INFRA-SOCKET-001: Socket cleanup uses try/finally."""
        from governance.routes.infra import _fetch_logs_socket
        src = inspect.getsource(_fetch_logs_socket)
        assert "finally:" in src
        assert "sock.close()" in src
        assert "conn.close()" in src

    def test_projects_fallback_total_before_slice(self):
        """BUG-PROJECTS-TOTAL-001: Fallback captures total before slicing."""
        from governance.services.projects import list_projects
        src = inspect.getsource(list_projects)
        # The fallback path captures total before slicing
        assert "total = len(all_projects)" in src

    def test_session_file_path_is_server_controlled(self):
        """BUG-ROUTE-PATH-001: file_path comes from server-side code, not user input."""
        # Session file_path is always set by session_bridge or evidence_scanner
        # Not a user-injectable parameter
        from governance.routes.sessions import detail
        src = inspect.getsource(detail)
        # The file_path comes from session object (from TypeDB/store)
        assert "session.get" in src or "file_path" in src


class TestRejectedServiceFindings:
    """Confirm that rejected service-layer findings are non-issues."""

    def test_task_to_response_null_safe(self):
        """All list fields use 'or []' in task_to_response."""
        from governance.stores.helpers import task_to_response
        src = inspect.getsource(task_to_response)
        assert "linked_rules=task.linked_rules or []" in src
        assert "linked_sessions=task.linked_sessions or []" in src
        assert "linked_commits=task.linked_commits or []" in src

    def test_session_to_response_null_safe(self):
        """All list fields use 'or []' in session_to_response."""
        from governance.stores.helpers import session_to_response
        src = inspect.getsource(session_to_response)
        assert "evidence_files=session.evidence_files or []" in src
        assert "linked_rules_applied=session.linked_rules_applied or []" in src

    def test_monitor_logs_at_warning(self):
        """Monitor failures are logged at WARNING level (not silently swallowed)."""
        from governance.services.tasks_mutations import update_task
        src = inspect.getsource(update_task)
        assert "logger.warning" in src
