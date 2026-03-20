"""
Unit tests for Workspace Service TypeDB Integration.

Phase 3 of EPIC-GOV-TASKS-V2: Workspace TypeDB Promotion.

BDD Scenarios:
  - Service dual-writes (TypeDB + disk) on create
  - Service dual-writes on update
  - Service dual-writes on delete
  - Fallback to disk when TypeDB unavailable on create
  - Fallback to disk when TypeDB unavailable on update
  - Fallback to disk when TypeDB unavailable on delete
  - Get workspace prefers TypeDB, falls back to disk
  - List workspaces merges TypeDB + disk
  - Project linking propagates to TypeDB
  - Agent assignment propagates to TypeDB
"""

from unittest.mock import MagicMock, patch

import pytest

_P = "governance.services.workspaces"


@pytest.fixture(autouse=True)
def _reset_store():
    """Reset in-memory store and loaded flag for each test."""
    with patch(f"{_P}._workspaces_store", {}) as store, \
         patch(f"{_P}._loaded", True), \
         patch(f"{_P}._save"), \
         patch(f"{_P}.record_audit"):
        yield store


def _mock_typedb_client(connected=True):
    """Create a mock TypeDB client with workspace methods."""
    client = MagicMock()
    client.is_connected.return_value = connected
    client.insert_workspace = MagicMock(return_value={"workspace_id": "WS-TDB"})
    client.get_workspace = MagicMock(return_value=None)
    client.update_workspace_attrs = MagicMock(return_value=True)
    client.delete_workspace = MagicMock(return_value=True)
    client.link_workspace_to_project = MagicMock(return_value=True)
    client.link_workspace_to_agent = MagicMock(return_value=True)
    client.unlink_agent_from_workspace = MagicMock(return_value=True)
    return client


# ── Create Workspace TypeDB Dual-Write ────────────────────────


class TestCreateWorkspaceTypeDB:
    """Service dual-writes to TypeDB + disk on create."""

    @patch(f"{_P}.get_workspace_type")
    @patch(f"{_P}._get_typedb_client")
    def test_create_writes_to_typedb(self, mock_get_client, mock_wt):
        from governance.services.workspaces import create_workspace

        client = _mock_typedb_client()
        mock_get_client.return_value = client
        mock_wt.return_value = MagicMock(
            description="desc", default_rules=[], capabilities=[],
            icon="mdi-folder", color="#ccc"
        )

        ws = create_workspace("TypeDB WS", "governance", project_id="PROJ-1")

        assert ws is not None
        assert ws["workspace_id"].startswith("WS-")
        client.insert_workspace.assert_called_once()
        call_kwargs = client.insert_workspace.call_args
        assert call_kwargs[1]["name"] == "TypeDB WS"
        assert call_kwargs[1]["workspace_type"] == "governance"

    @patch(f"{_P}.get_workspace_type")
    @patch(f"{_P}._get_typedb_client")
    def test_create_writes_to_typedb_with_project_link(self, mock_get_client, mock_wt):
        from governance.services.workspaces import create_workspace

        client = _mock_typedb_client()
        mock_get_client.return_value = client
        mock_wt.return_value = MagicMock(
            description="desc", default_rules=[], capabilities=[],
            icon="mdi-folder", color="#ccc"
        )

        ws = create_workspace("WS", "governance", project_id="PROJ-99")

        client.link_workspace_to_project.assert_called_once_with(
            workspace_id=ws["workspace_id"], project_id="PROJ-99"
        )

    @patch(f"{_P}.get_workspace_type")
    @patch(f"{_P}._get_typedb_client")
    def test_create_falls_back_on_typedb_failure(self, mock_get_client, mock_wt):
        from governance.services.workspaces import create_workspace

        client = _mock_typedb_client()
        client.insert_workspace.side_effect = Exception("TypeDB down")
        mock_get_client.return_value = client
        mock_wt.return_value = MagicMock(
            description="desc", default_rules=[], capabilities=[],
            icon="mdi-folder", color="#ccc"
        )

        # Should still succeed via disk path
        ws = create_workspace("Fallback WS", "governance")
        assert ws is not None
        assert ws["workspace_id"].startswith("WS-")

    @patch(f"{_P}.get_workspace_type")
    @patch(f"{_P}._get_typedb_client")
    def test_create_no_typedb_client_still_works(self, mock_get_client, mock_wt):
        from governance.services.workspaces import create_workspace

        mock_get_client.return_value = None
        mock_wt.return_value = MagicMock(
            description="desc", default_rules=[], capabilities=[],
            icon="mdi-folder", color="#ccc"
        )

        ws = create_workspace("No TypeDB WS", "governance")
        assert ws is not None


# ── Update Workspace TypeDB Dual-Write ────────────────────────


class TestUpdateWorkspaceTypeDB:
    """Service dual-writes on update."""

    @patch(f"{_P}._get_typedb_client")
    def test_update_writes_to_typedb(self, mock_get_client, _reset_store):
        from governance.services.workspaces import update_workspace

        _reset_store["WS-UPD"] = {
            "workspace_id": "WS-UPD", "name": "Old", "workspace_type": "generic",
            "description": "", "status": "active", "agent_ids": [],
        }
        client = _mock_typedb_client()
        mock_get_client.return_value = client

        ws = update_workspace("WS-UPD", name="New Name")

        assert ws["name"] == "New Name"
        client.update_workspace_attrs.assert_called_once()

    @patch(f"{_P}._get_typedb_client")
    def test_update_falls_back_on_typedb_failure(self, mock_get_client, _reset_store):
        from governance.services.workspaces import update_workspace

        _reset_store["WS-UPD"] = {
            "workspace_id": "WS-UPD", "name": "Old", "workspace_type": "generic",
            "description": "", "status": "active", "agent_ids": [],
        }
        client = _mock_typedb_client()
        client.update_workspace_attrs.side_effect = Exception("TypeDB down")
        mock_get_client.return_value = client

        ws = update_workspace("WS-UPD", name="Updated Anyway")
        assert ws["name"] == "Updated Anyway"

    @patch(f"{_P}._get_typedb_client")
    def test_update_nonexistent_returns_none(self, mock_get_client, _reset_store):
        from governance.services.workspaces import update_workspace

        mock_get_client.return_value = _mock_typedb_client()

        result = update_workspace("WS-NONE", name="X")
        assert result is None


# ── Delete Workspace TypeDB Dual-Write ────────────────────────


class TestDeleteWorkspaceTypeDB:
    """Service dual-writes on delete."""

    @patch(f"{_P}._get_typedb_client")
    def test_delete_writes_to_typedb(self, mock_get_client, _reset_store):
        from governance.services.workspaces import delete_workspace

        _reset_store["WS-DEL"] = {"workspace_id": "WS-DEL"}
        client = _mock_typedb_client()
        mock_get_client.return_value = client

        result = delete_workspace("WS-DEL")
        assert result is True
        client.delete_workspace.assert_called_once_with("WS-DEL")

    @patch(f"{_P}._get_typedb_client")
    def test_delete_falls_back_on_typedb_failure(self, mock_get_client, _reset_store):
        from governance.services.workspaces import delete_workspace

        _reset_store["WS-DEL"] = {"workspace_id": "WS-DEL"}
        client = _mock_typedb_client()
        client.delete_workspace.side_effect = Exception("TypeDB down")
        mock_get_client.return_value = client

        result = delete_workspace("WS-DEL")
        assert result is True
        assert "WS-DEL" not in _reset_store


# ── Get Workspace TypeDB Preference ──────────────────────────


class TestGetWorkspaceTypeDB:
    """Get prefers TypeDB, falls back to disk."""

    @patch(f"{_P}._get_typedb_client")
    def test_get_from_typedb_when_available(self, mock_get_client, _reset_store):
        from governance.services.workspaces import get_workspace

        # Disk has old data
        _reset_store["WS-GET"] = {"workspace_id": "WS-GET", "name": "Disk Version"}

        client = _mock_typedb_client()
        client.get_workspace.return_value = {
            "workspace_id": "WS-GET", "name": "TypeDB Version",
            "workspace_type": "governance", "status": "active",
        }
        mock_get_client.return_value = client

        result = get_workspace("WS-GET")
        assert result is not None
        # Should prefer TypeDB data
        assert result["name"] == "TypeDB Version"

    @patch(f"{_P}._get_typedb_client")
    def test_get_falls_back_to_disk(self, mock_get_client, _reset_store):
        from governance.services.workspaces import get_workspace

        _reset_store["WS-DISK"] = {"workspace_id": "WS-DISK", "name": "Disk Only"}
        client = _mock_typedb_client()
        client.get_workspace.return_value = None
        mock_get_client.return_value = client

        result = get_workspace("WS-DISK")
        assert result is not None
        assert result["name"] == "Disk Only"

    @patch(f"{_P}._get_typedb_client")
    def test_get_disk_when_no_client(self, mock_get_client, _reset_store):
        from governance.services.workspaces import get_workspace

        _reset_store["WS-NC"] = {"workspace_id": "WS-NC", "name": "No Client"}
        mock_get_client.return_value = None

        result = get_workspace("WS-NC")
        assert result["name"] == "No Client"


# ── Agent Assignment TypeDB Propagation ──────────────────────


class TestAgentAssignmentTypeDB:
    """Agent assignment propagates to TypeDB."""

    @patch(f"{_P}._get_typedb_client")
    def test_assign_agent_writes_to_typedb(self, mock_get_client, _reset_store):
        from governance.services.workspaces import assign_agent_to_workspace

        _reset_store["WS-AGT"] = {
            "workspace_id": "WS-AGT", "agent_ids": [],
        }
        client = _mock_typedb_client()
        mock_get_client.return_value = client

        assign_agent_to_workspace("WS-AGT", "agent-governance")

        client.link_workspace_to_agent.assert_called_once_with(
            workspace_id="WS-AGT", agent_id="agent-governance"
        )

    @patch(f"{_P}._get_typedb_client")
    def test_remove_agent_writes_to_typedb(self, mock_get_client, _reset_store):
        from governance.services.workspaces import remove_agent_from_workspace

        _reset_store["WS-AGT"] = {
            "workspace_id": "WS-AGT", "agent_ids": ["agent-governance"],
        }
        client = _mock_typedb_client()
        mock_get_client.return_value = client

        remove_agent_from_workspace("WS-AGT", "agent-governance")

        client.unlink_agent_from_workspace.assert_called_once_with(
            workspace_id="WS-AGT", agent_id="agent-governance"
        )

    @patch(f"{_P}._get_typedb_client")
    def test_assign_agent_survives_typedb_failure(self, mock_get_client, _reset_store):
        from governance.services.workspaces import assign_agent_to_workspace

        _reset_store["WS-AGT"] = {
            "workspace_id": "WS-AGT", "agent_ids": [],
        }
        client = _mock_typedb_client()
        client.link_workspace_to_agent.side_effect = Exception("TypeDB down")
        mock_get_client.return_value = client

        result = assign_agent_to_workspace("WS-AGT", "agent-governance")
        assert result is not None
        assert "agent-governance" in result["agent_ids"]
