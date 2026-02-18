"""
Unit tests for Project Service.

Per GOV-PROJECT-01-v1: Project hierarchy management.
Tests: CRUD operations + session linking + in-memory fallback.
"""

import pytest
from unittest.mock import patch, MagicMock

from governance.services.projects import (
    create_project,
    get_project,
    list_projects,
    delete_project,
    link_session_to_project,
    _projects_store,
)


@pytest.fixture(autouse=True)
def clear_store():
    """Clear in-memory store between tests."""
    _projects_store.clear()
    yield
    _projects_store.clear()


@pytest.fixture
def mock_no_client():
    """Mock _get_client to return None (in-memory fallback)."""
    with patch("governance.services.projects._get_client", return_value=None):
        yield


class TestCreateProject:
    """Tests for create_project()."""

    def test_create_with_explicit_id(self, mock_no_client):
        result = create_project(project_id="PROJ-TEST", name="Test Project")
        assert result is not None
        assert result["project_id"] == "PROJ-TEST"
        assert result["name"] == "Test Project"

    def test_create_auto_generates_id(self, mock_no_client):
        result = create_project(name="My Cool Project")
        assert result is not None
        assert result["project_id"].startswith("PROJ-")
        assert "MY" in result["project_id"]

    def test_create_with_path(self, mock_no_client):
        result = create_project(
            project_id="PROJ-P", name="P", path="/tmp/project",
        )
        assert result["path"] == "/tmp/project"

    def test_create_stores_in_memory(self, mock_no_client):
        create_project(project_id="PROJ-MEM", name="Memory Test")
        assert "PROJ-MEM" in _projects_store
        assert _projects_store["PROJ-MEM"]["name"] == "Memory Test"

    def test_create_initializes_counts(self, mock_no_client):
        result = create_project(project_id="PROJ-C", name="Counts")
        assert result["plan_count"] == 0
        assert result["session_count"] == 0

    def test_create_with_typedb_success(self):
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        # get_project returns None (no duplicate), then insert succeeds
        mock_client.get_project.return_value = None
        mock_client.insert_project.return_value = {
            "project_id": "PROJ-DB", "name": "DB Project",
        }
        with patch("governance.services.projects._get_client", return_value=mock_client):
            result = create_project(project_id="PROJ-DB", name="DB Project")
        assert result["project_id"] == "PROJ-DB"
        mock_client.insert_project.assert_called_once()

    def test_create_typedb_failure_falls_back(self):
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        # get_project returns None (no duplicate), then insert fails
        mock_client.get_project.return_value = None
        mock_client.insert_project.side_effect = Exception("TypeDB down")
        with patch("governance.services.projects._get_client", return_value=mock_client):
            result = create_project(project_id="PROJ-FALL", name="Fallback")
        assert result["project_id"] == "PROJ-FALL"
        assert "PROJ-FALL" in _projects_store


class TestGetProject:
    """Tests for get_project()."""

    def test_get_existing(self, mock_no_client):
        create_project(project_id="PROJ-G1", name="Get Test")
        result = get_project("PROJ-G1")
        assert result is not None
        assert result["project_id"] == "PROJ-G1"

    def test_get_nonexistent(self, mock_no_client):
        result = get_project("PROJ-NOPE")
        assert result is None

    def test_get_from_typedb(self):
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.get_project.return_value = {
            "project_id": "PROJ-TDB", "name": "TypeDB",
        }
        with patch("governance.services.projects._get_client", return_value=mock_client):
            result = get_project("PROJ-TDB")
        assert result["project_id"] == "PROJ-TDB"


class TestListProjects:
    """Tests for list_projects()."""

    def test_list_empty(self, mock_no_client):
        result = list_projects()
        assert result["items"] == []
        assert result["pagination"]["total"] == 0

    def test_list_with_items(self, mock_no_client):
        create_project(project_id="PROJ-A", name="A")
        create_project(project_id="PROJ-B", name="B")
        result = list_projects()
        assert len(result["items"]) == 2
        assert result["pagination"]["total"] == 2

    def test_list_pagination_limit(self, mock_no_client):
        for i in range(5):
            create_project(project_id=f"PROJ-{i}", name=f"Project {i}")
        result = list_projects(limit=3)
        assert len(result["items"]) == 3
        assert result["pagination"]["limit"] == 3

    def test_list_pagination_offset(self, mock_no_client):
        for i in range(5):
            create_project(project_id=f"PROJ-{i}", name=f"Project {i}")
        result = list_projects(limit=3, offset=3)
        assert len(result["items"]) == 2

    def test_list_sorted_by_id(self, mock_no_client):
        create_project(project_id="PROJ-Z", name="Z")
        create_project(project_id="PROJ-A", name="A")
        result = list_projects()
        ids = [p["project_id"] for p in result["items"]]
        assert ids == sorted(ids)

    def test_list_pagination_metadata(self, mock_no_client):
        create_project(project_id="PROJ-1", name="One")
        result = list_projects(limit=50, offset=0)
        pag = result["pagination"]
        assert pag["offset"] == 0
        assert pag["limit"] == 50
        assert "returned" in pag


class TestDeleteProject:
    """Tests for delete_project()."""

    def test_delete_existing(self, mock_no_client):
        create_project(project_id="PROJ-DEL", name="Delete Me")
        assert delete_project("PROJ-DEL") is True
        assert "PROJ-DEL" not in _projects_store

    def test_delete_nonexistent(self, mock_no_client):
        assert delete_project("PROJ-NOPE") is False


class TestLinkSessionToProject:
    """Tests for link_session_to_project()."""

    def test_link_without_client(self, mock_no_client):
        result = link_session_to_project("PROJ-1", "SESSION-123")
        assert result is False

    def test_link_with_typedb(self):
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.link_project_to_session.return_value = True
        with patch("governance.services.projects._get_client", return_value=mock_client):
            result = link_session_to_project("PROJ-1", "SESSION-123")
        assert result is True
        mock_client.link_project_to_session.assert_called_once_with("PROJ-1", "SESSION-123")

    def test_link_typedb_failure(self):
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.link_project_to_session.side_effect = Exception("fail")
        with patch("governance.services.projects._get_client", return_value=mock_client):
            result = link_session_to_project("PROJ-1", "SESSION-123")
        assert result is False
