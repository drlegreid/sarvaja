"""
Unit tests for Project Service.

Per DOC-SIZE-01-v1: Tests for governance/services/projects.py module.
Tests: create_project, get_project, list_projects, delete_project,
       link_session_to_project.
"""

from unittest.mock import MagicMock, patch

import pytest

_P = "governance.services.projects"


@pytest.fixture(autouse=True)
def _reset_store():
    with patch(f"{_P}._projects_store", {}) as store:
        yield store


# ── create_project ──────────────────────────────────────────────


class TestCreateProject:
    def test_fallback_success(self, _reset_store):
        from governance.services.projects import create_project
        with patch(f"{_P}._get_client", return_value=None):
            result = create_project(project_id="PROJ-TEST", name="Test")
        assert result["project_id"] == "PROJ-TEST"
        assert result["name"] == "Test"
        assert _reset_store["PROJ-TEST"]["name"] == "Test"

    def test_auto_generates_id(self):
        from governance.services.projects import create_project
        with patch(f"{_P}._get_client", return_value=None):
            result = create_project(name="My Project")
        assert result["project_id"].startswith("PROJ-")
        assert "MY" in result["project_id"]

    def test_auto_id_truncates(self):
        from governance.services.projects import create_project
        with patch(f"{_P}._get_client", return_value=None):
            result = create_project(name="Very Long Project Name That Exceeds Limit")
        assert len(result["project_id"]) <= len("PROJ-") + 20

    def test_with_path(self):
        from governance.services.projects import create_project
        with patch(f"{_P}._get_client", return_value=None):
            result = create_project(project_id="PROJ-X", name="X", path="/home/test")
        assert result["path"] == "/home/test"

    def test_typedb_success(self):
        from governance.services.projects import create_project
        client = MagicMock()
        client.insert_project.return_value = {"project_id": "PROJ-DB", "name": "DB"}
        with patch(f"{_P}._get_client", return_value=client):
            result = create_project(project_id="PROJ-DB", name="DB")
        assert result["project_id"] == "PROJ-DB"
        client.insert_project.assert_called_once()

    def test_typedb_failure_fallback(self, _reset_store):
        from governance.services.projects import create_project
        client = MagicMock()
        client.insert_project.side_effect = Exception("db error")
        with patch(f"{_P}._get_client", return_value=client):
            result = create_project(project_id="PROJ-FB", name="Fallback")
        assert result["project_id"] == "PROJ-FB"
        assert "PROJ-FB" in _reset_store

    def test_typedb_returns_none_fallback(self, _reset_store):
        from governance.services.projects import create_project
        client = MagicMock()
        client.insert_project.return_value = None
        with patch(f"{_P}._get_client", return_value=client):
            result = create_project(project_id="PROJ-NONE", name="None")
        assert result["project_id"] == "PROJ-NONE"
        assert "PROJ-NONE" in _reset_store

    def test_defaults(self):
        from governance.services.projects import create_project
        with patch(f"{_P}._get_client", return_value=None):
            result = create_project(project_id="PROJ-D", name="D")
        assert result["plan_count"] == 0
        assert result["session_count"] == 0
        assert result["path"] is None


# ── get_project ─────────────────────────────────────────────────


class TestGetProject:
    def test_typedb_success(self):
        from governance.services.projects import get_project
        client = MagicMock()
        client.get_project.return_value = {"project_id": "PROJ-1"}
        with patch(f"{_P}._get_client", return_value=client):
            result = get_project("PROJ-1")
        assert result["project_id"] == "PROJ-1"

    def test_typedb_not_found(self):
        from governance.services.projects import get_project
        client = MagicMock()
        client.get_project.return_value = None
        with patch(f"{_P}._get_client", return_value=client):
            result = get_project("PROJ-MISSING")
        assert result is None

    def test_typedb_failure_fallback(self, _reset_store):
        from governance.services.projects import get_project
        _reset_store["PROJ-FB"] = {"project_id": "PROJ-FB"}
        client = MagicMock()
        client.get_project.side_effect = Exception("db error")
        with patch(f"{_P}._get_client", return_value=client):
            result = get_project("PROJ-FB")
        assert result["project_id"] == "PROJ-FB"

    def test_fallback_found(self, _reset_store):
        from governance.services.projects import get_project
        _reset_store["PROJ-MEM"] = {"project_id": "PROJ-MEM", "name": "Memory"}
        with patch(f"{_P}._get_client", return_value=None):
            result = get_project("PROJ-MEM")
        assert result["name"] == "Memory"

    def test_fallback_not_found(self):
        from governance.services.projects import get_project
        with patch(f"{_P}._get_client", return_value=None):
            result = get_project("PROJ-MISSING")
        assert result is None


# ── list_projects ───────────────────────────────────────────────


class TestListProjects:
    def test_typedb_success(self):
        from governance.services.projects import list_projects
        client = MagicMock()
        client.list_projects.return_value = [
            {"project_id": "P-1"}, {"project_id": "P-2"},
        ]
        with patch(f"{_P}._get_client", return_value=client):
            result = list_projects()
        assert len(result["items"]) == 2
        assert result["pagination"]["total"] == 2

    def test_fallback(self, _reset_store):
        from governance.services.projects import list_projects
        _reset_store["P-A"] = {"project_id": "P-A"}
        _reset_store["P-B"] = {"project_id": "P-B"}
        with patch(f"{_P}._get_client", return_value=None):
            result = list_projects()
        assert len(result["items"]) == 2

    def test_pagination(self, _reset_store):
        from governance.services.projects import list_projects
        for i in range(5):
            _reset_store[f"P-{i}"] = {"project_id": f"P-{i}"}
        with patch(f"{_P}._get_client", return_value=None):
            result = list_projects(limit=2, offset=0)
        assert len(result["items"]) == 2
        assert result["pagination"]["has_more"] is True

    def test_typedb_failure_fallback(self, _reset_store):
        from governance.services.projects import list_projects
        _reset_store["P-FB"] = {"project_id": "P-FB"}
        client = MagicMock()
        client.list_projects.side_effect = Exception("db error")
        with patch(f"{_P}._get_client", return_value=client):
            result = list_projects()
        assert len(result["items"]) == 1

    def test_empty(self):
        from governance.services.projects import list_projects
        with patch(f"{_P}._get_client", return_value=None):
            result = list_projects()
        assert result["items"] == []
        assert result["pagination"]["total"] == 0


# ── delete_project ──────────────────────────────────────────────


class TestDeleteProject:
    def test_typedb_success(self):
        from governance.services.projects import delete_project
        client = MagicMock()
        client.delete_project.return_value = True
        with patch(f"{_P}._get_client", return_value=client):
            result = delete_project("PROJ-DEL")
        assert result is True

    def test_fallback_success(self, _reset_store):
        from governance.services.projects import delete_project
        _reset_store["PROJ-DEL"] = {"project_id": "PROJ-DEL"}
        with patch(f"{_P}._get_client", return_value=None):
            result = delete_project("PROJ-DEL")
        assert result is True
        assert "PROJ-DEL" not in _reset_store

    def test_fallback_not_found(self):
        from governance.services.projects import delete_project
        with patch(f"{_P}._get_client", return_value=None):
            result = delete_project("PROJ-MISSING")
        assert result is False

    def test_typedb_failure_fallback(self, _reset_store):
        from governance.services.projects import delete_project
        _reset_store["PROJ-FB"] = {"project_id": "PROJ-FB"}
        client = MagicMock()
        client.delete_project.side_effect = Exception("db error")
        with patch(f"{_P}._get_client", return_value=client):
            result = delete_project("PROJ-FB")
        assert result is True


# ── link_session_to_project ─────────────────────────────────────


class TestLinkSessionToProject:
    def test_typedb_success(self):
        from governance.services.projects import link_session_to_project
        client = MagicMock()
        client.link_project_to_session.return_value = True
        with patch(f"{_P}._get_client", return_value=client):
            result = link_session_to_project("PROJ-1", "SESSION-1")
        assert result is True

    def test_typedb_failure(self):
        from governance.services.projects import link_session_to_project
        client = MagicMock()
        client.link_project_to_session.side_effect = Exception("db error")
        with patch(f"{_P}._get_client", return_value=client):
            result = link_session_to_project("PROJ-1", "SESSION-1")
        assert result is False

    def test_no_client(self):
        from governance.services.projects import link_session_to_project
        with patch(f"{_P}._get_client", return_value=None):
            result = link_session_to_project("PROJ-1", "SESSION-1")
        assert result is False
