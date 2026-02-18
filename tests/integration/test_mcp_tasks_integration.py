"""MCP Tasks Integration Tests — Gov-Tasks tools against real TypeDB.

Tests task CRUD, listing, pagination, and taxonomy MCP tools
with a live TypeDB instance.

Run: .venv/bin/python3 -m pytest tests/integration/test_mcp_tasks_integration.py -v
Requires: TypeDB on localhost:1729
"""

import json
import pytest

from tests.integration.conftest import MockMCP, parse_mcp_result, make_test_id

pytestmark = [pytest.mark.integration, pytest.mark.typedb, pytest.mark.mcp]


# ---------------------------------------------------------------------------
# Fixture: register gov-tasks CRUD tools
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def task_tools(typedb_available):
    """Register and return task CRUD MCP tool functions."""
    from governance.mcp_tools.tasks_crud import register_task_crud_tools
    mcp = MockMCP()
    register_task_crud_tools(mcp)
    return mcp.tools


@pytest.fixture(scope="module")
def task_link_tools(typedb_available):
    """Register and return task linking MCP tool functions."""
    from governance.mcp_tools.tasks_linking import register_task_linking_tools
    mcp = MockMCP()
    register_task_linking_tools(mcp)
    return mcp.tools


# ---------------------------------------------------------------------------
# Cleanup: delete any test tasks created during this module
# ---------------------------------------------------------------------------

_created_task_ids = []


@pytest.fixture(scope="module", autouse=True)
def cleanup_tasks(typedb_available):
    """Delete any tasks created during this test module."""
    yield
    if not _created_task_ids:
        return
    try:
        from governance.mcp_tools.common import get_typedb_client
        client = get_typedb_client()
        if client.connect():
            for tid in _created_task_ids:
                try:
                    client.delete_task(tid)
                except Exception:
                    pass
            client.close()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# List tests
# ---------------------------------------------------------------------------

class TestTasksList:
    """Test tasks_list with real TypeDB data."""

    def test_list_returns_structure(self, task_tools):
        """tasks_list() returns tasks array with pagination."""
        result = parse_mcp_result(task_tools["tasks_list"]())
        assert "tasks" in result
        assert isinstance(result["tasks"], list)
        assert "count" in result
        assert "total" in result
        assert "has_more" in result
        assert result.get("source") == "typedb"

    def test_list_respects_limit(self, task_tools):
        """tasks_list(limit=2) returns at most 2 tasks."""
        result = parse_mcp_result(task_tools["tasks_list"](limit=2))
        assert len(result["tasks"]) <= 2

    def test_list_pagination(self, task_tools):
        """tasks_list with offset returns different tasks."""
        page1 = parse_mcp_result(task_tools["tasks_list"](limit=2, offset=0))
        page2 = parse_mcp_result(task_tools["tasks_list"](limit=2, offset=2))
        if len(page1["tasks"]) == 2 and len(page2["tasks"]) > 0:
            # Task dataclass uses 'id' field, not 'task_id'
            ids1 = {t.get("id") or t.get("task_id") for t in page1["tasks"]}
            ids2 = {t.get("id") or t.get("task_id") for t in page2["tasks"]}
            assert ids1.isdisjoint(ids2), "Pages should not overlap"

    def test_list_filter_by_status(self, task_tools):
        """tasks_list(status='OPEN') filters correctly."""
        result = parse_mcp_result(task_tools["tasks_list"](status="OPEN"))
        for task in result["tasks"]:
            assert task["status"] == "OPEN"


# ---------------------------------------------------------------------------
# Single task get tests
# ---------------------------------------------------------------------------

class TestTaskGet:
    """Test task_get with real TypeDB data."""

    def test_get_existing_task(self, task_tools):
        """task_get for an existing task returns task data."""
        all_result = parse_mcp_result(task_tools["tasks_list"](limit=1))
        if not all_result["tasks"]:
            pytest.skip("No tasks in TypeDB")

        # Task dataclass uses 'id' field
        tid = all_result["tasks"][0].get("id") or all_result["tasks"][0].get("task_id")
        result = parse_mcp_result(task_tools["task_get"](task_id=tid))
        actual_id = result.get("id") or result.get("task_id")
        assert actual_id == tid

    def test_get_nonexistent_returns_error(self, task_tools):
        """task_get for missing task returns error."""
        result = parse_mcp_result(
            task_tools["task_get"](task_id="NONEXISTENT-TASK-XYZ-999")
        )
        assert "error" in result


# ---------------------------------------------------------------------------
# CRUD lifecycle test
# ---------------------------------------------------------------------------

class TestTaskCRUDLifecycle:
    """Test task create → get → update → delete lifecycle."""

    def test_lifecycle(self, task_tools):
        """Full CRUD lifecycle with real TypeDB."""
        tid = make_test_id("INTTEST-TASK")
        _created_task_ids.append(tid)

        # CREATE
        create_result = parse_mcp_result(task_tools["task_create"](
            name="Integration Test Task",
            task_id=tid,
            description="Created by MCP integration test",
            status="OPEN",
            priority="LOW",
            task_type="test",
            phase="P10",
        ))
        assert "error" not in create_result
        assert "message" in create_result

        # GET — verify created
        get_result = parse_mcp_result(task_tools["task_get"](task_id=tid))
        actual_id = get_result.get("id") or get_result.get("task_id")
        assert actual_id == tid

        # UPDATE — change status
        update_result = parse_mcp_result(task_tools["task_update"](
            task_id=tid,
            status="IN_PROGRESS",
        ))
        assert "error" not in update_result

        # GET — verify updated
        updated = parse_mcp_result(task_tools["task_get"](task_id=tid))
        assert updated.get("status") == "IN_PROGRESS"

        # DELETE (with confirm)
        delete_result = parse_mcp_result(task_tools["task_delete"](
            task_id=tid,
            confirm=True,
        ))
        assert delete_result.get("deleted") is True

        # VERIFY DELETED
        verify = parse_mcp_result(task_tools["task_get"](task_id=tid))
        assert "error" in verify

        # Remove from cleanup list since already deleted
        _created_task_ids.remove(tid)


class TestTaskDeleteGuard:
    """Test that task_delete requires confirm=True."""

    def test_delete_without_confirm_rejected(self, task_tools):
        """task_delete without confirm=True is rejected."""
        result = parse_mcp_result(task_tools["task_delete"](
            task_id="ANY-TASK-ID",
            confirm=False,
        ))
        assert "error" in result


class TestTaskUpdateValidation:
    """Test task_update edge cases."""

    def test_update_no_fields_returns_error(self, task_tools):
        """task_update with no update fields returns error."""
        result = parse_mcp_result(task_tools["task_update"](task_id="ANY-TASK-ID"))
        assert "error" in result


# ---------------------------------------------------------------------------
# Taxonomy test
# ---------------------------------------------------------------------------

class TestTaxonomy:
    """Test taxonomy_get returns valid enum values."""

    def test_taxonomy_returns_all_enums(self, task_tools):
        """taxonomy_get returns all required enum collections."""
        result = parse_mcp_result(task_tools["taxonomy_get"]())
        assert "task_types" in result
        assert "task_priorities" in result
        assert "task_statuses" in result
        assert "task_phases" in result
        assert "rule_categories" in result
        assert "rule_priorities" in result
        assert "rule_statuses" in result

    def test_taxonomy_types_are_lists(self, task_tools):
        """taxonomy_get enum values are lists."""
        result = parse_mcp_result(task_tools["taxonomy_get"]())
        assert isinstance(result["task_types"], list)
        assert isinstance(result["task_priorities"], list)
        assert len(result["task_types"]) > 0
        assert len(result["task_priorities"]) > 0
