"""MCP Tasks E2E Integration Tests — CRUD lifecycle + workspace.

Per EPIC-GOV-TASKS-V2 Phase 5: End-to-end tests for Phases 1-4.
Per DOC-SIZE-01-v1: Linking/detail/intent tests in test_mcp_tasks_e2e_linking.py.

Run: .venv/bin/python3 -m pytest tests/integration/test_mcp_tasks_e2e.py -v
Requires: TypeDB on localhost:1729
"""

import pytest

from tests.integration.conftest import MockMCP, parse_mcp_result, make_test_id

pytestmark = [pytest.mark.integration, pytest.mark.typedb, pytest.mark.mcp]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def crud_tools(typedb_available):
    """Register task CRUD MCP tools."""
    from governance.mcp_tools.tasks_crud import register_task_crud_tools
    mcp = MockMCP()
    register_task_crud_tools(mcp)
    return mcp.tools


# ---------------------------------------------------------------------------
# Cleanup: delete test tasks created during this module
# ---------------------------------------------------------------------------

_created_task_ids = []


@pytest.fixture(scope="module", autouse=True)
def cleanup_tasks(typedb_available):
    """Delete test tasks after module completes."""
    yield
    if not _created_task_ids:
        return
    try:
        from governance.mcp_tools.common import get_typedb_client
        client = get_typedb_client()
        if client.connect():
            for tid in list(_created_task_ids):
                try:
                    client.delete_task(tid)
                except Exception:
                    pass
            client.close()
    except Exception:
        pass


def _create_test_task(crud_tools, prefix="E2E", **overrides):
    """Helper: create a task and track for cleanup. Returns (task_id, result)."""
    tid = make_test_id(prefix)
    _created_task_ids.append(tid)
    defaults = dict(
        name=f"E2E Test Task {tid}",
        task_id=tid,
        description="Created by E2E integration test",
        status="OPEN",
        priority="LOW",
        task_type="test",
        phase="P10",
    )
    defaults.update(overrides)
    result = parse_mcp_result(crud_tools["task_create"](**defaults))
    return tid, result


# ===========================================================================
# Test Class: Full CRUD Lifecycle via MCP
# ===========================================================================

class TestFullCRUDLifecycle:
    """BDD: Full CRUD lifecycle via MCP — create, read, update, delete."""

    def test_create_returns_success(self, crud_tools):
        """task_create returns success message with task_id."""
        tid, result = _create_test_task(crud_tools)
        assert "error" not in result
        assert "message" in result

    def test_get_returns_created_task(self, crud_tools):
        """task_get returns the task we just created."""
        tid, _ = _create_test_task(crud_tools)
        get_result = parse_mcp_result(crud_tools["task_get"](task_id=tid))
        actual_id = get_result.get("id") or get_result.get("task_id")
        assert actual_id == tid

    def test_update_status_persists(self, crud_tools):
        """task_update status change is visible via task_get."""
        tid, _ = _create_test_task(crud_tools)
        update = parse_mcp_result(
            crud_tools["task_update"](task_id=tid, status="IN_PROGRESS")
        )
        assert "error" not in update
        fetched = parse_mcp_result(crud_tools["task_get"](task_id=tid))
        assert fetched.get("status") == "IN_PROGRESS"

    def test_update_priority_persists(self, crud_tools):
        """task_update priority change is visible via task_get."""
        tid, _ = _create_test_task(crud_tools)
        parse_mcp_result(
            crud_tools["task_update"](task_id=tid, priority="CRITICAL")
        )
        fetched = parse_mcp_result(crud_tools["task_get"](task_id=tid))
        assert fetched.get("priority") == "CRITICAL"

    def test_delete_with_confirm_removes_task(self, crud_tools):
        """task_delete with confirm=True removes the task."""
        tid, _ = _create_test_task(crud_tools)
        delete = parse_mcp_result(
            crud_tools["task_delete"](task_id=tid, confirm=True)
        )
        assert delete.get("deleted") is True
        verify = parse_mcp_result(crud_tools["task_get"](task_id=tid))
        assert "error" in verify
        _created_task_ids.remove(tid)

    def test_create_with_workspace_id(self, crud_tools):
        """task_create with workspace_id assigns it (Phase 4)."""
        tid, result = _create_test_task(crud_tools, workspace_id="WS-E2E-TEST")
        assert "error" not in result

    def test_update_workspace_id(self, crud_tools):
        """task_update can assign workspace_id (Phase 4)."""
        tid, _ = _create_test_task(crud_tools)
        update = parse_mcp_result(
            crud_tools["task_update"](task_id=tid, workspace_id="WS-E2E-ASSIGN")
        )
        assert "error" not in update

    def test_create_with_session_id(self, crud_tools):
        """task_create with session_id auto-links (DATA-LINK-01-v1)."""
        tid, result = _create_test_task(
            crud_tools, session_id="SESSION-E2E-AUTOLINK"
        )
        assert "error" not in result


# ===========================================================================
# Test Class: Error Handling for Nonexistent Entities
# ===========================================================================

class TestErrorHandling:
    """BDD: Error handling for nonexistent entities."""

    def test_get_nonexistent_task(self, crud_tools):
        """task_get for missing task returns error."""
        result = parse_mcp_result(
            crud_tools["task_get"](task_id="NONEXISTENT-E2E-TASK-999")
        )
        assert "error" in result

    def test_update_nonexistent_task(self, crud_tools):
        """task_update for missing task returns error or empty."""
        result = parse_mcp_result(
            crud_tools["task_update"](
                task_id="NONEXISTENT-E2E-TASK-999", status="DONE"
            )
        )
        assert "error" in result or result.get("task_id") is None

    def test_delete_without_confirm_rejected(self, crud_tools):
        """task_delete without confirm=True is rejected."""
        result = parse_mcp_result(
            crud_tools["task_delete"](task_id="ANY", confirm=False)
        )
        assert "error" in result

    def test_update_no_fields_rejected(self, crud_tools):
        """task_update with no update fields returns error."""
        result = parse_mcp_result(
            crud_tools["task_update"](task_id="ANY")
        )
        assert "error" in result
