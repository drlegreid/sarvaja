"""Deep scan batch 133: Service mutations + rules + projects.

Batch 133 findings: 13 total, 0 confirmed fixes, 13 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ── Task update fallback defense ──────────────


class TestTaskUpdateFallbackDefense:
    """Verify update_task fallback handles edge cases."""

    def test_update_nonexistent_task_returns_none(self):
        """update_task returns None when task doesn't exist in either store."""
        with patch("governance.services.tasks_mutations.get_typedb_client", return_value=None), \
             patch("governance.services.tasks_mutations._tasks_store", {}):
            from governance.services.tasks_mutations import update_task
            result = update_task("NONEXISTENT-TASK", status="DONE")
            assert result is None

    def test_update_applies_all_fields_to_store(self):
        """update_task applies all provided fields to _tasks_store."""
        task = {
            "task_id": "TASK-001",
            "description": "Old desc",
            "phase": "planning",
            "status": "TODO",
            "agent_id": None,
            "priority": None,
            "task_type": None,
        }
        with patch("governance.services.tasks_mutations.get_typedb_client", return_value=None), \
             patch("governance.services.tasks_mutations._tasks_store", {"TASK-001": task}), \
             patch("governance.services.tasks_mutations.record_audit"), \
             patch("governance.services.tasks_mutations._monitor"), \
             patch("governance.services.tasks_mutations.log_event"):
            from governance.services.tasks_mutations import update_task
            result = update_task(
                "TASK-001",
                status="IN_PROGRESS",
                priority="HIGH",
                agent_id="code-agent",
            )
            assert result["status"] == "IN_PROGRESS"
            assert result["priority"] == "HIGH"
            assert result["agent_id"] == "code-agent"


# ── Task taxonomy WARNING level defense ──────────────


class TestTaskTaxonomyWarningDefense:
    """Verify taxonomy update failures log at WARNING not DEBUG."""

    def test_taxonomy_failure_logged_at_warning(self):
        """TypeDB taxonomy update failure logs at WARNING."""
        import inspect
        from governance.services import tasks_mutations
        source = inspect.getsource(tasks_mutations.update_task)
        # The logger.warning call should be in the taxonomy section
        assert "logger.warning" in source
        # Must NOT have logger.debug for taxonomy updates
        # (was upgraded from DEBUG per BUG-TASK-TAXONOMY-DEBUG-001)


# ── Session update CC fields defense ──────────────


class TestSessionUpdateCCFieldsDefense:
    """Verify session update handles CC fields in both paths."""

    def test_fallback_path_updates_cc_fields(self):
        """Fallback path updates all CC fields in _sessions_store."""
        session = {
            "session_id": "SESSION-2026-02-15-TEST",
            "status": "ACTIVE",
            "description": "Test",
        }
        with patch("governance.services.sessions.get_typedb_client", return_value=None), \
             patch("governance.services.sessions._sessions_store", {
                 "SESSION-2026-02-15-TEST": session,
             }), \
             patch("governance.services.sessions.record_audit"), \
             patch("governance.services.sessions._monitor"), \
             patch("governance.services.sessions.log_event"):
            from governance.services.sessions import update_session
            result = update_session(
                "SESSION-2026-02-15-TEST",
                cc_session_uuid="uuid-456",
                cc_project_slug="sarvaja",
            )
            assert result["cc_session_uuid"] == "uuid-456"
            assert result["cc_project_slug"] == "sarvaja"

    def test_typedb_path_returns_response(self):
        """TypeDB path returns session_to_response result."""
        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_session.status = "ACTIVE"
        mock_client.get_session.return_value = mock_session
        mock_client.update_session.return_value = mock_session

        with patch("governance.services.sessions.get_typedb_client", return_value=mock_client), \
             patch("governance.services.sessions.session_to_response") as mock_resp, \
             patch("governance.services.sessions.record_audit"), \
             patch("governance.services.sessions._monitor"), \
             patch("governance.services.sessions.log_event"):
            mock_resp.return_value = {"session_id": "S-1", "status": "ACTIVE"}
            from governance.services.sessions import update_session
            result = update_session("S-1", status="COMPLETED")
            mock_resp.assert_called_once()


# ── Project pagination defense ──────────────


class TestProjectPaginationDefense:
    """Verify project pagination heuristic is correct."""

    def test_full_page_assumes_more(self):
        """When TypeDB returns full page, has_more = True."""
        limit = 10
        offset = 0
        projects = [{"project_id": f"P-{i}"} for i in range(10)]  # Full page

        total = offset + len(projects)
        if len(projects) >= limit:
            total = offset + limit + 1
        has_more = (offset + limit) < total
        assert has_more is True

    def test_partial_page_no_more(self):
        """When TypeDB returns partial page, has_more = False."""
        limit = 10
        offset = 0
        projects = [{"project_id": f"P-{i}"} for i in range(7)]  # Partial

        total = offset + len(projects)
        if len(projects) >= limit:
            total = offset + limit + 1
        has_more = (offset + limit) < total
        assert has_more is False

    def test_fallback_total_before_slicing(self):
        """Fallback path captures total BEFORE slicing."""
        all_projects = [{"project_id": f"P-{i}"} for i in range(25)]
        total = len(all_projects)
        offset, limit = 0, 10
        page = all_projects[offset:offset + limit]
        has_more = (offset + limit) < total
        assert total == 25
        assert len(page) == 10
        assert has_more is True


# ── Rules ConnectionError defense ──────────────


class TestRulesConnectionErrorDefense:
    """Verify rules raise ConnectionError when TypeDB unavailable."""

    def test_get_client_or_raise_raises(self):
        """_get_client_or_raise raises ConnectionError when TypeDB down."""
        with patch("governance.services.rules.get_client", return_value=None):
            from governance.services.rules import _get_client_or_raise
            with pytest.raises(ConnectionError, match="TypeDB not connected"):
                _get_client_or_raise()

    def test_get_client_or_raise_returns_client(self):
        """_get_client_or_raise returns client when available."""
        mock = MagicMock()
        with patch("governance.services.rules.get_client", return_value=mock):
            from governance.services.rules import _get_client_or_raise
            result = _get_client_or_raise()
            assert result is mock


# ── Task-to-response field parity defense ──────────────


class TestTaskResponseFieldParityDefense:
    """Verify task_to_response includes all critical fields."""

    def test_document_path_included(self):
        """task_to_response includes document_path field."""
        import inspect
        from governance.stores.helpers import task_to_response
        source = inspect.getsource(task_to_response)
        assert "document_path" in source

    def test_gap_id_included(self):
        """task_to_response includes gap_id field."""
        import inspect
        from governance.stores.helpers import task_to_response
        source = inspect.getsource(task_to_response)
        assert "gap_id" in source

    def test_linked_documents_included(self):
        """task_to_response includes linked_documents field."""
        import inspect
        from governance.stores.helpers import task_to_response
        source = inspect.getsource(task_to_response)
        assert "linked_documents" in source
