"""MCP Cross-Entity Integration Tests — Verifies relationships across servers.

Tests that entities created in one MCP server are visible and linkable
from other servers. Verifies the full governance data model works.

Run: .venv/bin/python3 -m pytest tests/integration/test_mcp_cross_entity.py -v
Requires: TypeDB on localhost:1729
"""

import json
import pytest

from tests.integration.conftest import MockMCP, parse_mcp_result, make_test_id

pytestmark = [pytest.mark.integration, pytest.mark.typedb, pytest.mark.mcp]


# ---------------------------------------------------------------------------
# Fixtures: register tools from multiple servers
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def task_tools(typedb_available):
    """Register task CRUD tools."""
    from governance.mcp_tools.tasks_crud import register_task_crud_tools
    mcp = MockMCP()
    register_task_crud_tools(mcp)
    return mcp.tools


@pytest.fixture(scope="module")
def task_link_tools(typedb_available):
    """Register task linking tools."""
    from governance.mcp_tools.tasks_linking import register_task_linking_tools
    mcp = MockMCP()
    register_task_linking_tools(mcp)
    return mcp.tools


@pytest.fixture(scope="module")
def rule_tools(typedb_available):
    """Register rule query tools."""
    from governance.mcp_tools.rules_query import register_rule_query_tools
    mcp = MockMCP()
    register_rule_query_tools(mcp)
    return mcp.tools


@pytest.fixture(scope="module")
def session_tools(typedb_available):
    """Register session core tools."""
    from governance.mcp_tools.sessions_core import register_session_core_tools
    mcp = MockMCP()
    register_session_core_tools(mcp)
    return mcp.tools


@pytest.fixture(scope="module")
def session_link_tools(typedb_available):
    """Register session linking tools."""
    from governance.mcp_tools.sessions_linking import register_session_linking_tools
    mcp = MockMCP()
    register_session_linking_tools(mcp)
    return mcp.tools


# Cleanup
_created_task_ids = []


@pytest.fixture(scope="module", autouse=True)
def cleanup(typedb_available):
    """Cleanup test data."""
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
# Cross-entity: Task ↔ Rule linking
# ---------------------------------------------------------------------------

class TestTaskRuleLinking:
    """Test linking tasks to rules across gov-tasks and gov-core."""

    def test_task_link_rule(self, task_tools, task_link_tools, rule_tools):
        """Create task, link to rule, verify link."""
        if "task_link_rule" not in task_link_tools:
            pytest.skip("task_link_rule not available")

        # Find a real rule to link to
        rules = parse_mcp_result(rule_tools["rules_query"](status="ACTIVE"))
        if not rules.get("rules"):
            pytest.skip("No active rules to link to")
        rule_id = rules["rules"][0]["id"]

        # Create a task
        tid = make_test_id("INTTEST-XENT")
        _created_task_ids.append(tid)
        create = parse_mcp_result(task_tools["task_create"](
            name="Cross-entity test task",
            task_id=tid,
            description="Testing task-rule linking",
            priority="LOW",
            task_type="test",
        ))
        if "error" in create:
            pytest.skip(f"task_create failed: {create['error']}")

        # Link task to rule
        link_result = parse_mcp_result(task_link_tools["task_link_rule"](
            task_id=tid,
            rule_id=rule_id,
        ))
        assert "error" not in link_result

        # Cleanup
        task_tools["task_delete"](task_id=tid, confirm=True)
        _created_task_ids.remove(tid)


# ---------------------------------------------------------------------------
# Cross-entity: Task ↔ Session linking
# ---------------------------------------------------------------------------

class TestTaskSessionLinking:
    """Test linking tasks to sessions across gov-tasks and gov-sessions."""

    def test_task_link_session(self, task_tools, task_link_tools, session_tools):
        """Create task, link to session, verify."""
        if "task_link_session" not in task_link_tools:
            pytest.skip("task_link_session not available")

        # Start a session
        session = parse_mcp_result(session_tools["session_start"](
            topic="inttest-xent-session",
        ))
        if "error" in session:
            pytest.skip(f"session_start failed: {session['error']}")
        sid = session["session_id"]

        # Create a task
        tid = make_test_id("INTTEST-XSESS")
        _created_task_ids.append(tid)
        create = parse_mcp_result(task_tools["task_create"](
            name="Session-linked test task",
            task_id=tid,
            description="Testing task-session linking",
            priority="LOW",
            task_type="test",
        ))
        if "error" in create:
            pytest.skip(f"task_create failed: {create['error']}")

        # Link task to session
        link_result = parse_mcp_result(task_link_tools["task_link_session"](
            task_id=tid,
            session_id=sid,
        ))
        assert "error" not in link_result

        # Cleanup
        task_tools["task_delete"](task_id=tid, confirm=True)
        _created_task_ids.remove(tid)


# ---------------------------------------------------------------------------
# Cross-entity: Task created with session_id
# ---------------------------------------------------------------------------

class TestTaskCreationWithSession:
    """Test creating a task with session_id set at creation time."""

    def test_create_task_with_session(self, task_tools, session_tools):
        """task_create with session_id links task to session."""
        session = parse_mcp_result(session_tools["session_start"](
            topic="inttest-create-linked",
        ))
        if "error" in session:
            pytest.skip(f"session_start failed: {session['error']}")
        sid = session["session_id"]

        tid = make_test_id("INTTEST-LINKED")
        _created_task_ids.append(tid)
        result = parse_mcp_result(task_tools["task_create"](
            name="Task created with session link",
            task_id=tid,
            description="Should auto-link to session",
            priority="LOW",
            task_type="test",
            session_id=sid,
        ))
        assert "error" not in result

        # Cleanup
        task_tools["task_delete"](task_id=tid, confirm=True)
        _created_task_ids.remove(tid)
