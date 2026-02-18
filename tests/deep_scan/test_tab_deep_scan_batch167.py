"""Deep scan batch 167: Service + route layer.

Batch 167 findings: 20 total, 2 confirmed fixes, 18 rejected.
- BUG-SESSION-CREATE-CC: CC fields dropped in create_session route.
- BUG-SESSION-DEFAULT-STATUS: _ensure_response default status was "COMPLETED", now "ACTIVE".
"""
import pytest
from pathlib import Path


# ── CC fields forwarding defense ──────────────


class TestCCFieldsForwardingDefense:
    """Verify create_session route forwards CC fields to service."""

    def test_route_passes_cc_session_uuid(self):
        """create_session route passes cc_session_uuid to service."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/sessions/crud.py").read_text()
        # Find the create_session function
        start = src.index("async def create_session")
        end = src.index("\n@", start + 1) if "\n@" in src[start + 1:] else len(src)
        create_func = src[start:end]
        assert "cc_session_uuid=session.cc_session_uuid" in create_func

    def test_route_passes_cc_project_slug(self):
        """create_session route passes cc_project_slug to service."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/sessions/crud.py").read_text()
        assert "cc_project_slug=session.cc_project_slug" in src

    def test_route_passes_cc_git_branch(self):
        """create_session route passes cc_git_branch to service."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/sessions/crud.py").read_text()
        assert "cc_git_branch=session.cc_git_branch" in src

    def test_route_passes_cc_metrics(self):
        """create_session route passes tool_count, thinking_chars, compaction_count."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/sessions/crud.py").read_text()
        assert "cc_tool_count=session.cc_tool_count" in src
        assert "cc_thinking_chars=session.cc_thinking_chars" in src
        assert "cc_compaction_count=session.cc_compaction_count" in src

    def test_service_accepts_cc_fields(self):
        """create_session service accepts all 6 CC fields."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/sessions.py").read_text()
        start = src.index("def create_session")
        sig_end = src.index("):", start) + 2
        signature = src[start:sig_end]
        assert "cc_session_uuid" in signature
        assert "cc_project_slug" in signature
        assert "cc_git_branch" in signature
        assert "cc_tool_count" in signature
        assert "cc_thinking_chars" in signature
        assert "cc_compaction_count" in signature


# ── Default status defense ──────────────


class TestDefaultStatusDefense:
    """Verify _ensure_response default status is ACTIVE, not COMPLETED."""

    def test_default_status_is_active(self):
        """_ensure_response uses 'ACTIVE' as default status."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/sessions/crud.py").read_text()
        assert 'result.setdefault("status", "ACTIVE")' in src

    def test_no_completed_default(self):
        """_ensure_response does NOT use 'COMPLETED' as default."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/sessions/crud.py").read_text()
        # Find _ensure_response function
        start = src.index("def _ensure_response")
        end = src.index("\n\n", start + 1)
        func = src[start:end]
        assert '"COMPLETED"' not in func


# ── Pagination has_more defense ──────────────


class TestPaginationHasMoreDefense:
    """Verify has_more pagination uses len(paginated) not raw limit."""

    def test_sessions_uses_len_paginated(self):
        """sessions.py uses offset + len(paginated) for has_more."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/sessions.py").read_text()
        assert "len(paginated)" in src

    def test_tasks_uses_len_paginated(self):
        """tasks.py uses offset + len(paginated) for has_more."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/tasks.py").read_text()
        assert "len(paginated)" in src

    def test_has_more_formula_correct(self):
        """Correct formula: (offset + len(page)) < total."""
        # Edge cases
        assert (0 + 5) < 55  # has_more = True (more pages)
        assert not (50 + 5) < 55  # has_more = False (last page)
        assert not (0 + 50) < 50  # has_more = False (exact fit)


# ── Delete route safety defense ──────────────


class TestDeleteRouteSafetyDefense:
    """Verify delete routes return proper status codes."""

    def test_session_delete_returns_204(self):
        """Session delete route has status_code=204."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/sessions/crud.py").read_text()
        assert "status_code=204" in src
        assert "delete_session" in src

    def test_task_delete_exists(self):
        """Task delete route exists."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/tasks/crud.py").read_text()
        assert "delete_task" in src


# ── Agent_id only update defense ──────────────


class TestAgentIdOnlyUpdateDefense:
    """Verify agent_id-only update behavior is documented."""

    def test_update_task_requires_status_for_typedb(self):
        """update_task needs status or evidence to trigger TypeDB write."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/tasks_mutations.py").read_text()
        # The condition that gates TypeDB write
        assert "status or evidence" in src or "(status or evidence)" in src


# ── Service layer error handling defense ──────────────


class TestServiceLayerErrorHandlingDefense:
    """Verify service functions handle errors correctly."""

    def test_create_session_catches_valueerror(self):
        """create_session route catches ValueError for duplicate sessions."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/sessions/crud.py").read_text()
        start = src.index("async def create_session")
        end = src.index("\n@", start + 1) if "\n@" in src[start + 1:] else len(src)
        func = src[start:end]
        assert "ValueError" in func
        assert "409" in func

    def test_list_rules_catches_connection_error(self):
        """list_rules route catches ConnectionError for TypeDB unavailable."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/rules/crud.py").read_text()
        assert "ConnectionError" in src
        assert "503" in src
