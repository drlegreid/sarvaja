"""
Unit tests for Task-Workspace Bidirectional Linking.

Phase 4 of EPIC-GOV-TASKS-V2: Task-Workspace Bidirectional Linking.

BDD Scenarios:
  Feature: Task-Workspace Bidirectional Linking
    # Schema
    Scenario: workspace-has-task relation exists in 3x schema
    Scenario: Task entity plays workspace-has-task:assigned-task role
    Scenario: Workspace entity plays workspace-has-task:task-workspace role
    Scenario: Monolithic schema includes workspace-has-task relation

    # Entity
    Scenario: Task dataclass has workspace_id field

    # Workspace Linking Operations (TypeDB layer)
    Scenario: link_task_to_workspace creates relation
    Scenario: link_task_to_workspace handles missing workspace
    Scenario: link_task_to_workspace handles missing task
    Scenario: unlink_task_from_workspace deletes relation
    Scenario: unlink_task_from_workspace handles missing relation
    Scenario: get_tasks_for_workspace returns task IDs
    Scenario: get_tasks_for_workspace returns empty for no tasks
    Scenario: get_workspace_for_task returns workspace ID
    Scenario: get_workspace_for_task returns None for unlinked task

    # Task Read (TypeDB layer)
    Scenario: _batch_fetch_task_relationships includes workspace
    Scenario: _build_task_from_id fetches workspace_id

    # Task CRUD (TypeDB layer)
    Scenario: insert_task accepts workspace_id and creates relation

    # Response Model
    Scenario: TaskResponse includes workspace_id field
    Scenario: task_to_response maps workspace_id

    # Service Layer
    Scenario: create_task accepts workspace_id and links
    Scenario: create_task without workspace_id works unchanged
    Scenario: update_task persists workspace_id to TypeDB
    Scenario: link_task_to_workspace service function works

    # MCP Tools
    Scenario: task_create MCP tool accepts workspace_id
    Scenario: task_update MCP tool accepts workspace_id
"""

import logging
from unittest.mock import MagicMock, patch, call

import pytest


# ── Mock helpers ──────────────────────────────────────────────

def _make_mock_client():
    """Create a mock client with _driver, database, _execute_query."""
    client = MagicMock()
    client.database = "test-db"
    client._driver = MagicMock()
    client._execute_query = MagicMock(return_value=[])
    return client


def _make_tx():
    """Create a mock transaction context manager."""
    tx = MagicMock()
    tx.query.return_value.resolve.return_value = None
    return tx


# =============================================================================
# SCHEMA TESTS
# =============================================================================


class TestSchemaWorkspaceHasTask:
    """Schema includes workspace-has-task relation with correct roles."""

    def test_3x_workspace_relations_has_task_relation(self):
        """26_workspace_relations_3x.tql defines workspace-has-task."""
        import os
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "governance", "schema_3x", "26_workspace_relations_3x.tql"
        )
        with open(schema_path) as f:
            content = f.read()
        assert "workspace-has-task" in content
        assert "task-workspace" in content
        assert "assigned-task" in content

    def test_3x_task_entity_plays_workspace_role(self):
        """01_core_entities_3x.tql: task plays workspace-has-task:assigned-task."""
        import os
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "governance", "schema_3x", "01_core_entities_3x.tql"
        )
        with open(schema_path) as f:
            content = f.read()
        assert "workspace-has-task:assigned-task" in content

    def test_3x_workspace_entity_plays_task_role(self):
        """07_workspace_entities_3x.tql: workspace plays workspace-has-task:task-workspace."""
        import os
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "governance", "schema_3x", "07_workspace_entities_3x.tql"
        )
        with open(schema_path) as f:
            content = f.read()
        assert "workspace-has-task:task-workspace" in content

    def test_monolithic_schema_has_workspace_has_task(self):
        """schema.tql includes workspace-has-task relation."""
        import os
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "governance", "schema.tql"
        )
        with open(schema_path) as f:
            content = f.read()
        assert "workspace-has-task" in content


# =============================================================================
# ENTITY TESTS
# =============================================================================


class TestTaskWorkspaceIdField:
    """Task dataclass has workspace_id field."""

    def test_task_has_workspace_id(self):
        from governance.typedb.entities import Task
        task = Task(id="T-001", name="Test", status="OPEN", phase="P10")
        assert hasattr(task, "workspace_id")
        assert task.workspace_id is None

    def test_task_workspace_id_settable(self):
        from governance.typedb.entities import Task
        task = Task(
            id="T-001", name="Test", status="OPEN",
            phase="P10", workspace_id="WS-001"
        )
        assert task.workspace_id == "WS-001"


# =============================================================================
# WORKSPACE LINKING OPERATIONS (TypeDB layer)
# =============================================================================


class TestLinkTaskToWorkspace:
    """link_task_to_workspace creates workspace-has-task relation."""

    def test_link_task_to_workspace_success(self):
        from governance.typedb.queries.workspaces.linking import (
            WorkspaceLinkingOperations,
        )
        client = _make_mock_client()
        tx = _make_tx()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        op = WorkspaceLinkingOperations.link_task_to_workspace
        result = op(client, workspace_id="WS-001", task_id="TASK-001")

        assert result is True
        tx.query.assert_called_once()
        query = tx.query.call_args[0][0]
        assert "workspace-has-task" in query
        assert "WS-001" in query
        assert "TASK-001" in query
        tx.commit.assert_called_once()

    def test_link_task_to_workspace_failure(self):
        from governance.typedb.queries.workspaces.linking import (
            WorkspaceLinkingOperations,
        )
        client = _make_mock_client()
        tx = _make_tx()
        tx.query.side_effect = Exception("TypeDB error")
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        op = WorkspaceLinkingOperations.link_task_to_workspace
        result = op(client, workspace_id="WS-001", task_id="TASK-001")

        assert result is False

    def test_link_task_to_workspace_escapes_input(self):
        from governance.typedb.queries.workspaces.linking import (
            WorkspaceLinkingOperations,
        )
        client = _make_mock_client()
        tx = _make_tx()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        op = WorkspaceLinkingOperations.link_task_to_workspace
        result = op(client, workspace_id='WS-"001', task_id='TASK-"001')

        assert result is True
        query = tx.query.call_args[0][0]
        assert 'WS-\\"001' in query
        assert 'TASK-\\"001' in query


class TestUnlinkTaskFromWorkspace:
    """unlink_task_from_workspace deletes workspace-has-task relation."""

    def test_unlink_success(self):
        from governance.typedb.queries.workspaces.linking import (
            WorkspaceLinkingOperations,
        )
        client = _make_mock_client()
        tx = _make_tx()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        op = WorkspaceLinkingOperations.unlink_task_from_workspace
        result = op(client, workspace_id="WS-001", task_id="TASK-001")

        assert result is True
        query = tx.query.call_args[0][0]
        assert "delete" in query.lower()
        assert "workspace-has-task" in query
        tx.commit.assert_called_once()

    def test_unlink_failure(self):
        from governance.typedb.queries.workspaces.linking import (
            WorkspaceLinkingOperations,
        )
        client = _make_mock_client()
        tx = _make_tx()
        tx.query.side_effect = Exception("Not found")
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        op = WorkspaceLinkingOperations.unlink_task_from_workspace
        result = op(client, workspace_id="WS-001", task_id="TASK-001")

        assert result is False


class TestGetTasksForWorkspace:
    """get_tasks_for_workspace queries tasks linked to a workspace."""

    def test_returns_task_ids(self):
        from governance.typedb.queries.workspaces.linking import (
            WorkspaceLinkingOperations,
        )
        client = _make_mock_client()
        client._execute_query.return_value = [
            {"tid": "TASK-001"}, {"tid": "TASK-002"},
        ]

        op = WorkspaceLinkingOperations.get_tasks_for_workspace
        result = op(client, workspace_id="WS-001")

        assert result == ["TASK-001", "TASK-002"]

    def test_returns_empty_for_no_tasks(self):
        from governance.typedb.queries.workspaces.linking import (
            WorkspaceLinkingOperations,
        )
        client = _make_mock_client()
        client._execute_query.return_value = []

        op = WorkspaceLinkingOperations.get_tasks_for_workspace
        result = op(client, workspace_id="WS-001")

        assert result == []

    def test_handles_error_gracefully(self):
        from governance.typedb.queries.workspaces.linking import (
            WorkspaceLinkingOperations,
        )
        client = _make_mock_client()
        client._execute_query.side_effect = Exception("DB error")

        op = WorkspaceLinkingOperations.get_tasks_for_workspace
        result = op(client, workspace_id="WS-001")

        assert result == []


class TestGetWorkspaceForTask:
    """get_workspace_for_task returns workspace ID for a task."""

    def test_returns_workspace_id(self):
        from governance.typedb.queries.workspaces.linking import (
            WorkspaceLinkingOperations,
        )
        client = _make_mock_client()
        client._execute_query.return_value = [{"wid": "WS-001"}]

        op = WorkspaceLinkingOperations.get_workspace_for_task
        result = op(client, task_id="TASK-001")

        assert result == "WS-001"

    def test_returns_none_for_unlinked_task(self):
        from governance.typedb.queries.workspaces.linking import (
            WorkspaceLinkingOperations,
        )
        client = _make_mock_client()
        client._execute_query.return_value = []

        op = WorkspaceLinkingOperations.get_workspace_for_task
        result = op(client, task_id="TASK-001")

        assert result is None


# =============================================================================
# TASK READ TESTS
# =============================================================================


class TestBatchFetchWorkspaceRelationship:
    """_batch_fetch_task_relationships includes workspace."""

    def test_workspace_populated_in_batch_fetch(self):
        from governance.typedb.queries.tasks.read import TaskReadQueries
        from governance.typedb.entities import Task

        client = _make_mock_client()
        task = Task(id="TASK-001", name="Test", status="OPEN", phase="P10")
        task_map = {"TASK-001": task}

        # Return workspace result for the workspace query
        def mock_execute_query(query):
            if "workspace-has-task" in query:
                return [{"tid": "TASK-001", "wid": "WS-001"}]
            return []

        client._execute_query.side_effect = mock_execute_query

        op = TaskReadQueries._batch_fetch_task_relationships
        op(client, task_map)

        assert task.workspace_id == "WS-001"

    def test_workspace_not_populated_when_no_relation(self):
        from governance.typedb.queries.tasks.read import TaskReadQueries
        from governance.typedb.entities import Task

        client = _make_mock_client()
        task = Task(id="TASK-001", name="Test", status="OPEN", phase="P10")
        task_map = {"TASK-001": task}
        client._execute_query.return_value = []

        op = TaskReadQueries._batch_fetch_task_relationships
        op(client, task_map)

        assert task.workspace_id is None


class TestBuildTaskWorkspaceId:
    """_build_task_from_id fetches workspace_id."""

    def test_workspace_id_fetched_in_build(self):
        from governance.typedb.queries.tasks.read import TaskReadQueries

        client = _make_mock_client()

        # Base task query
        def mock_execute_query(query):
            if "task-name" in query and "task-status" in query:
                return [{"name": "Test", "status": "OPEN", "phase": "P10"}]
            return []

        client._execute_query.side_effect = mock_execute_query

        # Mock _safe_query for optional attrs + relations
        def mock_safe_query(query):
            if "workspace-has-task" in query:
                return [{"wid": "WS-001"}]
            return []

        client._safe_query = mock_safe_query

        # _fetch_task_attr needs to work
        def mock_fetch_attr(task_id, attr_name, var_name):
            return None

        client._fetch_task_attr = mock_fetch_attr

        # _fetch_task_relation needs to return workspace
        def mock_fetch_relation(task_id, query, var_name):
            if "workspace-has-task" in query:
                return ["WS-001"]
            return []

        client._fetch_task_relation = mock_fetch_relation

        op = TaskReadQueries._build_task_from_id
        task = op(client, "TASK-001")

        assert task is not None
        assert task.workspace_id == "WS-001"


# =============================================================================
# TASK CRUD TESTS
# =============================================================================


class TestInsertTaskWorkspaceId:
    """insert_task accepts workspace_id and creates relation."""

    def test_insert_with_workspace_id_creates_relation(self):
        """BUG-WS-CREATE-001: Workspace link now called as separate method after commit."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations

        client = _make_mock_client()
        tx = _make_tx()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        from governance.typedb.entities import Task
        created = Task(id="TASK-001", name="Test", status="OPEN", phase="P10", workspace_id="WS-001")
        client.get_task = MagicMock(return_value=created)
        client.link_task_to_workspace = MagicMock(return_value=True)

        op = TaskCRUDOperations.insert_task
        result = op(
            client, task_id="TASK-001", name="Test Task",
            status="OPEN", phase="P10", workspace_id="WS-001"
        )

        assert result is not None
        # BUG-WS-CREATE-001: link_task_to_workspace called separately (not in main TX)
        client.link_task_to_workspace.assert_called_once_with("WS-001", "TASK-001")

    def test_insert_without_workspace_id_no_relation(self):
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations

        client = _make_mock_client()
        tx = _make_tx()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        from governance.typedb.entities import Task
        created = Task(id="TASK-002", name="Test", status="OPEN", phase="P10")
        client.get_task = MagicMock(return_value=created)

        op = TaskCRUDOperations.insert_task
        result = op(
            client, task_id="TASK-002", name="Test Task",
            status="OPEN", phase="P10"
        )

        assert result is not None
        queries = [c[0][0] for c in tx.query.call_args_list]
        ws_queries = [q for q in queries if "workspace-has-task" in q]
        assert len(ws_queries) == 0


# =============================================================================
# RESPONSE MODEL TESTS
# =============================================================================


class TestTaskResponseWorkspaceId:
    """TaskResponse includes workspace_id field."""

    def test_task_response_has_workspace_id_field(self):
        from governance.models import TaskResponse
        resp = TaskResponse(
            task_id="T-001", description="Test", phase="P10", status="OPEN",
            workspace_id="WS-001"
        )
        assert resp.workspace_id == "WS-001"

    def test_task_response_workspace_id_defaults_none(self):
        from governance.models import TaskResponse
        resp = TaskResponse(
            task_id="T-001", description="Test", phase="P10", status="OPEN"
        )
        assert resp.workspace_id is None


class TestTaskToResponseWorkspaceId:
    """task_to_response maps workspace_id from Task entity."""

    def test_maps_workspace_id(self):
        from governance.stores.helpers import task_to_response
        from governance.typedb.entities import Task
        task = Task(
            id="T-001", name="Test", status="OPEN",
            phase="P10", workspace_id="WS-001"
        )
        resp = task_to_response(task)
        assert resp.workspace_id == "WS-001"

    def test_maps_none_workspace_id(self):
        from governance.stores.helpers import task_to_response
        from governance.typedb.entities import Task
        task = Task(id="T-001", name="Test", status="OPEN", phase="P10")
        resp = task_to_response(task)
        assert resp.workspace_id is None


# =============================================================================
# SERVICE LAYER TESTS
# =============================================================================


class TestCreateTaskWorkspaceId:
    """create_task accepts workspace_id and links."""

    @patch("governance.services.tasks.get_typedb_client")
    @patch("governance.services.tasks._get_active_session_id", return_value=None)
    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks.log_event")
    def test_create_task_with_workspace_id(
        self, mock_log, mock_audit, mock_session, mock_client
    ):
        from governance.services.tasks import create_task
        from governance.typedb.entities import Task

        client = MagicMock()
        mock_client.return_value = client
        client.get_task.side_effect = [None, None]  # Not exists check, then re-fetch

        created_task = Task(
            id="FEAT-001", name="Test", status="OPEN",
            phase="P10", workspace_id="WS-001"
        )
        client.insert_task.return_value = created_task

        result = create_task(
            task_id="FEAT-001", description="Test task",
            workspace_id="WS-001"
        )

        # insert_task called with workspace_id
        client.insert_task.assert_called_once()
        call_kwargs = client.insert_task.call_args
        assert call_kwargs.kwargs.get("workspace_id") == "WS-001" or \
               (len(call_kwargs.args) > 0 and "WS-001" in str(call_kwargs))

    @patch("governance.services.tasks.get_typedb_client")
    @patch("governance.services.tasks._get_active_session_id", return_value=None)
    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks.log_event")
    def test_create_task_without_workspace_id(
        self, mock_log, mock_audit, mock_session, mock_client
    ):
        from governance.services.tasks import create_task
        from governance.typedb.entities import Task

        client = MagicMock()
        mock_client.return_value = client
        client.get_task.return_value = None

        created_task = Task(
            id="FEAT-002", name="Test", status="OPEN", phase="P10"
        )
        client.insert_task.return_value = created_task

        result = create_task(
            task_id="FEAT-002", description="Test task"
        )

        # No workspace linking
        client.link_task_to_workspace.assert_not_called()


class TestUpdateTaskWorkspaceId:
    """update_task persists workspace_id to TypeDB."""

    @patch("governance.services.tasks_mutations.get_typedb_client")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_update_with_workspace_id_links(
        self, mock_log, mock_audit, mock_client
    ):
        from governance.services.tasks_mutations import update_task
        from governance.typedb.entities import Task

        client = MagicMock()
        mock_client.return_value = client
        task_obj = Task(
            id="TASK-001", name="Test", status="OPEN", phase="P10"
        )
        client.get_task.return_value = task_obj

        result = update_task(
            task_id="TASK-001", status="IN_PROGRESS",
            workspace_id="WS-001"
        )

        client.link_task_to_workspace.assert_called_once_with("WS-001", "TASK-001")  # BUG-WS-CREATE-001: correct arg order

    @patch("governance.services.tasks_mutations.get_typedb_client")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_update_without_workspace_id_no_link(
        self, mock_log, mock_audit, mock_client
    ):
        from governance.services.tasks_mutations import update_task
        from governance.typedb.entities import Task

        client = MagicMock()
        mock_client.return_value = client
        task_obj = Task(
            id="TASK-001", name="Test", status="OPEN", phase="P10"
        )
        client.get_task.return_value = task_obj

        result = update_task(task_id="TASK-001", status="IN_PROGRESS")

        client.link_task_to_workspace.assert_not_called()


class TestServiceLinkTaskToWorkspace:
    """Service-level link_task_to_workspace function."""

    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_link_task_to_workspace_service(self, mock_client):
        from governance.services.tasks_mutations import link_task_to_workspace

        client = MagicMock()
        mock_client.return_value = client
        client.get_task.return_value = MagicMock()
        client.link_task_to_workspace.return_value = True

        result = link_task_to_workspace("TASK-001", "WS-001")

        assert result is True
        client.link_task_to_workspace.assert_called_once_with("WS-001", "TASK-001")  # BUG-WS-CREATE-001: correct arg order

    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_link_task_to_workspace_no_client(self, mock_client):
        from governance.services.tasks_mutations import link_task_to_workspace

        mock_client.return_value = None
        result = link_task_to_workspace("TASK-001", "WS-001")
        assert result is False

    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_link_task_to_workspace_task_not_found(self, mock_client):
        from governance.services.tasks_mutations import link_task_to_workspace

        client = MagicMock()
        mock_client.return_value = client
        client.get_task.return_value = None

        result = link_task_to_workspace("TASK-MISSING", "WS-001")
        assert result is False


# =============================================================================
# MCP TOOL TESTS
# =============================================================================


class TestMCPTaskCreateWorkspaceId:
    """task_create MCP tool accepts workspace_id."""

    def test_task_create_with_workspace_id(self):
        from governance.mcp_tools.tasks_crud import register_task_crud_tools

        mcp = MagicMock()
        tools = {}

        def capture_tool():
            def decorator(func):
                tools[func.__name__] = func
                return func
            return decorator

        mcp.tool = capture_tool
        register_task_crud_tools(mcp)

        assert "task_create" in tools
        # Check workspace_id is in the function signature
        import inspect
        sig = inspect.signature(tools["task_create"])
        assert "workspace_id" in sig.parameters


class TestMCPTaskUpdateWorkspaceId:
    """task_update MCP tool accepts workspace_id."""

    def test_task_update_with_workspace_id(self):
        from governance.mcp_tools.tasks_crud import register_task_crud_tools

        mcp = MagicMock()
        tools = {}

        def capture_tool():
            def decorator(func):
                tools[func.__name__] = func
                return func
            return decorator

        mcp.tool = capture_tool
        register_task_crud_tools(mcp)

        assert "task_update" in tools
        import inspect
        sig = inspect.signature(tools["task_update"])
        assert "workspace_id" in sig.parameters
