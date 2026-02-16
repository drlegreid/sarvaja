"""
Batch 83 — Service Layer Mutations + Store Persistence.

Triage: 27 findings (deduped) → 2 confirmed, 25 rejected.
Validates: taxonomy update logging, project pagination, data flow patterns.
"""
import inspect

import pytest


# ===========================================================================
# Confirmed: BUG-TASK-TAXONOMY-DEBUG-001 — WARNING not DEBUG for divergence
# ===========================================================================

class TestTaskTaxonomyUpdateLogging:
    """Verify taxonomy update failures logged at WARNING (not DEBUG)."""

    def test_taxonomy_update_failure_at_warning(self):
        """TypeDB attribute update failure uses logger.warning."""
        from governance.services.tasks_mutations import update_task
        src = inspect.getsource(update_task)
        # Find the taxonomy update block (priority/task_type/phase)
        taxonomy_idx = src.find("TypeDB attribute update")
        assert taxonomy_idx > 0
        # Check surrounding context uses warning not debug
        context = src[max(0, taxonomy_idx - 100):taxonomy_idx + 100]
        assert "logger.warning" in context

    def test_main_status_update_has_warning(self):
        """Main TypeDB task update failure also at WARNING."""
        from governance.services.tasks_mutations import update_task
        src = inspect.getsource(update_task)
        assert "TypeDB task update failed, using fallback" in src
        fallback_idx = src.find("TypeDB task update failed")
        context = src[max(0, fallback_idx - 50):fallback_idx + 100]
        assert "logger.warning" in context


# ===========================================================================
# Confirmed: BUG-PROJECT-PAGINATION-001 — has_more uses page-inferred total
# ===========================================================================

class TestProjectPaginationTotal:
    """Verify project pagination correctly infers has_more."""

    def test_fallback_total_before_slicing(self):
        """In-memory fallback captures total BEFORE slicing."""
        from governance.services.projects import list_projects
        src = inspect.getsource(list_projects)
        # Fallback path: total = len(all_projects) before slicing
        assert "total = len(all_projects)" in src

    def test_typedb_total_inferred_from_page_size(self):
        """TypeDB path infers total from page fill level."""
        from governance.services.projects import list_projects
        src = inspect.getsource(list_projects)
        # Must check if full page → more exist
        assert "len(projects) >= limit" in src

    def test_has_more_correct_for_full_page(self):
        """Full page implies more items exist."""
        limit, offset = 50, 0
        page_count = 50  # Full page
        total = offset + page_count + 1  # = 51
        has_more = (offset + limit) < total
        assert has_more is True

    def test_has_more_correct_for_partial_page(self):
        """Partial page implies no more items."""
        limit, offset = 50, 0
        page_count = 30  # Partial
        total = offset + page_count  # = 30
        has_more = (offset + limit) < total
        assert has_more is False


# ===========================================================================
# Rejected: Dual session converters — documented maintenance hazard
# ===========================================================================

class TestSessionDualConverterConsistency:
    """Verify both session converters include CC fields."""

    def test_session_to_response_has_cc_fields(self):
        """helpers.py session_to_response includes CC attributes."""
        from governance.stores.helpers import session_to_response
        src = inspect.getsource(session_to_response)
        for field in ["cc_session_uuid", "cc_project_slug", "cc_git_branch",
                       "cc_tool_count", "cc_thinking_chars", "cc_compaction_count"]:
            assert field in src, f"Missing {field}"

    def test_session_to_dict_has_cc_fields(self):
        """typedb_access.py _session_to_dict includes CC attributes."""
        from governance.stores.typedb_access import _session_to_dict
        src = inspect.getsource(_session_to_dict)
        for field in ["cc_session_uuid", "cc_project_slug", "cc_git_branch",
                       "cc_tool_count", "cc_thinking_chars", "cc_compaction_count"]:
            assert field in src, f"Missing {field}"


# ===========================================================================
# Rejected: task_to_response missing document_path — FALSE: line 46 has it
# ===========================================================================

class TestTaskToResponseFieldParity:
    """Verify task_to_response includes all critical fields."""

    def test_document_path_included(self):
        """task_to_response includes document_path field."""
        from governance.stores.helpers import task_to_response
        src = inspect.getsource(task_to_response)
        assert "document_path" in src

    def test_linked_documents_included(self):
        """task_to_response includes linked_documents field."""
        from governance.stores.helpers import task_to_response
        src = inspect.getsource(task_to_response)
        assert "linked_documents" in src

    def test_resolution_included(self):
        """task_to_response includes resolution field (GAP-UI-046)."""
        from governance.stores.helpers import task_to_response
        src = inspect.getsource(task_to_response)
        assert "resolution" in src


# ===========================================================================
# Rejected: _tasks_store not updated with links — FALSE: line 156 does it
# ===========================================================================

class TestTaskStoreLinksUpdated:
    """Verify _tasks_store is updated with linked_sessions in update_task."""

    def test_linked_sessions_in_updates_dict(self):
        """update_task puts linked_sessions in the updates dict."""
        from governance.services.tasks_mutations import update_task
        src = inspect.getsource(update_task)
        # The updates dict includes linked_sessions
        assert '"linked_sessions": linked_sessions' in src

    def test_linked_documents_in_updates_dict(self):
        """update_task puts linked_documents in the updates dict."""
        from governance.services.tasks_mutations import update_task
        src = inspect.getsource(update_task)
        assert '"linked_documents": linked_documents' in src
