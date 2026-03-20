"""
Unit tests for Workspace TypeDB CRUD Operations.

Phase 3 of EPIC-GOV-TASKS-V2: Workspace TypeDB Promotion.

BDD Scenarios:
  - Insert workspace into TypeDB with required fields
  - Insert workspace with all optional fields
  - Get workspace by ID returns Workspace entity
  - Get nonexistent workspace returns None
  - List all workspaces
  - List workspaces with filters (status, workspace_type)
  - Update workspace attributes
  - Update nonexistent workspace returns False
  - Delete workspace
  - Delete nonexistent workspace returns False
  - Delete cleans up relations before entity
  - Insert duplicate workspace returns None (idempotent)
  - Link workspace to project
  - Link workspace to agent
  - Get workspaces for project
  - Get agents for workspace
  - Unlink agent from workspace
"""

import logging
from unittest.mock import MagicMock, patch, call

import pytest


# ── Mock TypeDB driver ──────────────────────────────────────

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


# ── WorkspaceCRUDOperations Tests ────────────────────────────


class TestInsertWorkspace:
    """Insert workspace into TypeDB."""

    def test_insert_workspace_basic(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        # get_workspace returns None (no duplicate)
        client.get_workspace = MagicMock(return_value=None)
        tx = _make_tx()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        # Bind method to mock client
        op = WorkspaceCRUDOperations.insert_workspace
        # After insert, get_workspace returns the entity
        ws_result = {"workspace_id": "WS-001", "name": "Test WS", "workspace_type": "governance"}
        client.get_workspace = MagicMock(side_effect=[None, ws_result])

        result = op(client, workspace_id="WS-001", name="Test WS", workspace_type="governance")

        assert result is not None
        assert result["workspace_id"] == "WS-001"
        # Verify query was called
        tx.query.assert_called()
        tx.commit.assert_called_once()

    def test_insert_workspace_all_fields(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        tx = _make_tx()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        ws_result = {
            "workspace_id": "WS-002", "name": "Full WS",
            "workspace_type": "gamedev", "description": "A gamedev workspace",
            "status": "active",
        }
        client.get_workspace = MagicMock(side_effect=[None, ws_result])

        result = WorkspaceCRUDOperations.insert_workspace(
            client,
            workspace_id="WS-002",
            name="Full WS",
            workspace_type="gamedev",
            description="A gamedev workspace",
            status="active",
        )

        assert result is not None
        assert result["workspace_type"] == "gamedev"
        query_str = tx.query.call_args_list[0][0][0]
        assert "workspace-description" in query_str
        assert "workspace-status" in query_str

    def test_insert_duplicate_returns_none(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        # Already exists
        client.get_workspace = MagicMock(return_value={"workspace_id": "WS-DUP"})

        result = WorkspaceCRUDOperations.insert_workspace(
            client, workspace_id="WS-DUP", name="Dup", workspace_type="generic"
        )
        assert result is None

    def test_insert_escapes_special_chars(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        tx = _make_tx()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        client.get_workspace = MagicMock(side_effect=[None, {"workspace_id": "WS-ESC"}])

        WorkspaceCRUDOperations.insert_workspace(
            client, workspace_id='WS-"ESC"', name='Test "quotes"', workspace_type="generic"
        )
        query_str = tx.query.call_args_list[0][0][0]
        assert '\\"' in query_str

    def test_insert_handles_exception(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        client.get_workspace = MagicMock(return_value=None)
        client._driver.transaction.side_effect = Exception("DB error")

        result = WorkspaceCRUDOperations.insert_workspace(
            client, workspace_id="WS-ERR", name="Err", workspace_type="generic"
        )
        assert result is None


class TestGetWorkspace:
    """Get workspace by ID."""

    def test_get_existing_workspace(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        # First call: existence check returns result
        # Subsequent calls: attribute fetches
        client._execute_query = MagicMock(side_effect=[
            [{"w": "exists"}],                         # existence
            [{"v": "Test WS"}],                        # name
            [{"v": "governance"}],                     # type
            [{"v": "A workspace"}],                    # description
            [{"v": "active"}],                         # status
        ])

        result = WorkspaceCRUDOperations.get_workspace(client, "WS-001")
        assert result is not None
        assert result["workspace_id"] == "WS-001"
        assert result["name"] == "Test WS"

    def test_get_nonexistent_workspace(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        client._execute_query = MagicMock(return_value=[])

        result = WorkspaceCRUDOperations.get_workspace(client, "WS-NONE")
        assert result is None

    def test_get_handles_exception(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        client._execute_query = MagicMock(side_effect=Exception("DB error"))

        result = WorkspaceCRUDOperations.get_workspace(client, "WS-ERR")
        assert result is None


class TestListWorkspaces:
    """List all workspaces."""

    def test_list_workspaces_returns_all(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        client._execute_query = MagicMock(return_value=[
            {"id": "WS-001"},
            {"id": "WS-002"},
        ])
        client.get_workspace = MagicMock(side_effect=[
            {"workspace_id": "WS-001", "name": "A"},
            {"workspace_id": "WS-002", "name": "B"},
        ])

        result = WorkspaceCRUDOperations.list_workspaces(client)
        assert len(result) == 2

    def test_list_workspaces_pagination(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        client._execute_query = MagicMock(return_value=[
            {"id": "WS-001"}, {"id": "WS-002"}, {"id": "WS-003"},
        ])
        client.get_workspace = MagicMock(return_value={"workspace_id": "WS-002"})

        result = WorkspaceCRUDOperations.list_workspaces(client, limit=1, offset=1)
        assert len(result) == 1

    def test_list_workspaces_empty(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        client._execute_query = MagicMock(return_value=[])

        result = WorkspaceCRUDOperations.list_workspaces(client)
        assert result == []


class TestUpdateWorkspace:
    """Update workspace attributes."""

    def test_update_name(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        client.get_workspace = MagicMock(return_value={
            "workspace_id": "WS-001", "name": "Old", "workspace_type": "generic",
            "description": "", "status": "active",
        })
        tx = _make_tx()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        result = WorkspaceCRUDOperations.update_workspace_attrs(
            client, workspace_id="WS-001", name="New Name"
        )
        assert result is True
        tx.commit.assert_called_once()

    def test_update_status(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        client.get_workspace = MagicMock(return_value={
            "workspace_id": "WS-001", "name": "WS", "workspace_type": "generic",
            "description": "", "status": "active",
        })
        tx = _make_tx()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        result = WorkspaceCRUDOperations.update_workspace_attrs(
            client, workspace_id="WS-001", status="archived"
        )
        assert result is True

    def test_update_nonexistent_returns_false(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        client.get_workspace = MagicMock(return_value=None)

        result = WorkspaceCRUDOperations.update_workspace_attrs(
            client, workspace_id="WS-NONE", name="X"
        )
        assert result is False

    def test_update_handles_exception(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        client.get_workspace = MagicMock(return_value={
            "workspace_id": "WS-001", "name": "WS", "workspace_type": "generic",
            "description": "", "status": "active",
        })
        client._driver.transaction.side_effect = Exception("DB error")

        result = WorkspaceCRUDOperations.update_workspace_attrs(
            client, workspace_id="WS-001", name="X"
        )
        assert result is False


class TestDeleteWorkspace:
    """Delete workspace from TypeDB."""

    def test_delete_existing(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        client.get_workspace = MagicMock(return_value={"workspace_id": "WS-DEL"})
        tx = _make_tx()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        result = WorkspaceCRUDOperations.delete_workspace(client, "WS-DEL")
        assert result is True

    def test_delete_nonexistent_returns_false(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        client.get_workspace = MagicMock(return_value=None)

        result = WorkspaceCRUDOperations.delete_workspace(client, "WS-NONE")
        assert result is False

    def test_delete_cleans_up_relations(self):
        from governance.typedb.queries.workspaces.crud import WorkspaceCRUDOperations

        client = _make_mock_client()
        client.get_workspace = MagicMock(return_value={"workspace_id": "WS-REL"})
        tx = _make_tx()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        WorkspaceCRUDOperations.delete_workspace(client, "WS-REL")

        # Should have multiple transaction calls (relations + entity)
        assert client._driver.transaction.call_count >= 2


# ── WorkspaceLinkingOperations Tests ──────────────────────────


class TestWorkspaceLinking:
    """Link workspace to project and agents."""

    def test_link_workspace_to_project(self):
        from governance.typedb.queries.workspaces.linking import WorkspaceLinkingOperations

        client = _make_mock_client()
        tx = _make_tx()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        result = WorkspaceLinkingOperations.link_workspace_to_project(
            client, workspace_id="WS-001", project_id="PROJ-001"
        )
        assert result is True
        query_str = tx.query.call_args[0][0]
        assert "project-has-workspace" in query_str
        assert "owning-project" in query_str
        assert "workspace-member" in query_str

    def test_link_workspace_to_agent(self):
        from governance.typedb.queries.workspaces.linking import WorkspaceLinkingOperations

        client = _make_mock_client()
        tx = _make_tx()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        result = WorkspaceLinkingOperations.link_workspace_to_agent(
            client, workspace_id="WS-001", agent_id="agent-governance"
        )
        assert result is True
        query_str = tx.query.call_args[0][0]
        assert "workspace-has-agent" in query_str

    def test_unlink_agent_from_workspace(self):
        from governance.typedb.queries.workspaces.linking import WorkspaceLinkingOperations

        client = _make_mock_client()
        tx = _make_tx()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        result = WorkspaceLinkingOperations.unlink_agent_from_workspace(
            client, workspace_id="WS-001", agent_id="agent-governance"
        )
        assert result is True

    def test_get_workspaces_for_project(self):
        from governance.typedb.queries.workspaces.linking import WorkspaceLinkingOperations

        client = _make_mock_client()
        client._execute_query = MagicMock(return_value=[
            {"wid": "WS-001"},
            {"wid": "WS-002"},
        ])

        result = WorkspaceLinkingOperations.get_workspaces_for_project(client, "PROJ-001")
        assert result == ["WS-001", "WS-002"]

    def test_get_agents_for_workspace(self):
        from governance.typedb.queries.workspaces.linking import WorkspaceLinkingOperations

        client = _make_mock_client()
        client._execute_query = MagicMock(return_value=[
            {"aid": "agent-governance"},
            {"aid": "agent-coding"},
        ])

        result = WorkspaceLinkingOperations.get_agents_for_workspace(client, "WS-001")
        assert result == ["agent-governance", "agent-coding"]

    def test_link_handles_exception(self):
        from governance.typedb.queries.workspaces.linking import WorkspaceLinkingOperations

        client = _make_mock_client()
        client._driver.transaction.side_effect = Exception("DB error")

        result = WorkspaceLinkingOperations.link_workspace_to_project(
            client, workspace_id="WS-ERR", project_id="P-ERR"
        )
        assert result is False

    def test_get_workspaces_empty(self):
        from governance.typedb.queries.workspaces.linking import WorkspaceLinkingOperations

        client = _make_mock_client()
        client._execute_query = MagicMock(return_value=[])

        result = WorkspaceLinkingOperations.get_workspaces_for_project(client, "PROJ-EMPTY")
        assert result == []


# ── WorkspaceReadQueries Tests ────────────────────────────────


class TestWorkspaceReadQueries:
    """Batch fetch and filtered reads."""

    def test_get_all_workspaces_returns_list(self):
        from governance.typedb.queries.workspaces.read import WorkspaceReadQueries

        client = _make_mock_client()
        client._execute_query = MagicMock(return_value=[
            {"id": "WS-001", "name": "A", "wtype": "governance", "wstatus": "active"},
            {"id": "WS-002", "name": "B", "wtype": "gamedev", "wstatus": "active"},
        ])

        result = WorkspaceReadQueries.get_all_workspaces(client)
        assert len(result) == 2
        assert result[0].id == "WS-001"
        assert result[0].workspace_type == "governance"

    def test_get_all_workspaces_filtered_by_status(self):
        from governance.typedb.queries.workspaces.read import WorkspaceReadQueries

        client = _make_mock_client()
        client._execute_query = MagicMock(return_value=[
            {"id": "WS-003", "name": "Archived", "wtype": "generic", "wstatus": "archived"},
        ])

        result = WorkspaceReadQueries.get_all_workspaces(client, status="archived")
        assert len(result) == 1

    def test_get_all_workspaces_empty(self):
        from governance.typedb.queries.workspaces.read import WorkspaceReadQueries

        client = _make_mock_client()
        client._execute_query = MagicMock(return_value=[])

        result = WorkspaceReadQueries.get_all_workspaces(client)
        assert result == []

    def test_get_all_workspaces_handles_exception(self):
        from governance.typedb.queries.workspaces.read import WorkspaceReadQueries

        client = _make_mock_client()
        client._execute_query = MagicMock(side_effect=Exception("DB error"))

        result = WorkspaceReadQueries.get_all_workspaces(client)
        assert result == []


# ── WorkspaceQueries Composite Mixin Tests ────────────────────


class TestWorkspaceQueriesComposite:
    """WorkspaceQueries combines all mixin classes."""

    def test_workspace_queries_has_crud_methods(self):
        from governance.typedb.queries.workspaces import WorkspaceQueries

        assert hasattr(WorkspaceQueries, 'insert_workspace')
        assert hasattr(WorkspaceQueries, 'get_workspace')
        assert hasattr(WorkspaceQueries, 'list_workspaces')
        assert hasattr(WorkspaceQueries, 'update_workspace_attrs')
        assert hasattr(WorkspaceQueries, 'delete_workspace')

    def test_workspace_queries_has_linking_methods(self):
        from governance.typedb.queries.workspaces import WorkspaceQueries

        assert hasattr(WorkspaceQueries, 'link_workspace_to_project')
        assert hasattr(WorkspaceQueries, 'link_workspace_to_agent')
        assert hasattr(WorkspaceQueries, 'unlink_agent_from_workspace')
        assert hasattr(WorkspaceQueries, 'get_workspaces_for_project')
        assert hasattr(WorkspaceQueries, 'get_agents_for_workspace')

    def test_workspace_queries_has_read_methods(self):
        from governance.typedb.queries.workspaces import WorkspaceQueries

        assert hasattr(WorkspaceQueries, 'get_all_workspaces')
