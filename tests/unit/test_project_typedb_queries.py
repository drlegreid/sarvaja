"""
Unit tests for Project TypeDB query operations.

Per GOV-PROJECT-01-v1: Tests CRUD + linking query classes.
"""

import pytest
from unittest.mock import MagicMock, patch

from governance.typedb.queries.projects.crud import ProjectCRUDOperations
from governance.typedb.queries.projects.linking import ProjectLinkingOperations


class TestProjectCRUDMixin:
    """Tests for ProjectCRUDOperations mixin methods."""

    def _make_mixin(self):
        """Create a mixin instance with mocked TypeDB driver and base methods."""
        obj = ProjectCRUDOperations.__new__(ProjectCRUDOperations)
        obj._driver = MagicMock()
        obj.database = "test_db"
        obj._connected = True
        obj._execute_query = MagicMock(return_value=[])
        return obj

    def test_insert_checks_existing(self):
        obj = self._make_mixin()
        with patch.object(obj, "get_project", return_value={"project_id": "PROJ-1"}):
            result = obj.insert_project("PROJ-1", "Test")
        assert result is None

    def test_get_project_no_results(self):
        obj = self._make_mixin()
        obj._execute_query.return_value = []
        result = obj.get_project("PROJ-NOPE")
        assert result is None

    def test_get_project_with_results(self):
        obj = self._make_mixin()
        obj._execute_query.side_effect = [
            [{"p": "iid-123"}],  # existence
            [{"v": "My Project"}],  # name
            [{"v": "/some/path"}],  # path
        ]
        result = obj.get_project("PROJ-1")
        assert result == {
            "project_id": "PROJ-1",
            "name": "My Project",
            "path": "/some/path",
        }

    def test_get_project_partial_attrs(self):
        obj = self._make_mixin()
        obj._execute_query.side_effect = [
            [{"p": "iid-123"}],  # existence
            [{"v": "Project X"}],  # name
            [],  # no path
        ]
        result = obj.get_project("PROJ-2")
        assert result["name"] == "Project X"
        assert result["path"] is None

    def test_get_project_error(self):
        obj = self._make_mixin()
        obj._execute_query.side_effect = Exception("fail")
        result = obj.get_project("PROJ-ERR")
        assert result is None

    def test_delete_nonexistent(self):
        obj = self._make_mixin()
        with patch.object(obj, "get_project", return_value=None):
            result = obj.delete_project("PROJ-NOPE")
        assert result is False

    def test_list_projects_error_returns_empty(self):
        obj = self._make_mixin()
        obj._execute_query.side_effect = Exception("connection refused")
        result = obj.list_projects()
        assert result == []

    def test_list_projects_returns_projects(self):
        obj = self._make_mixin()
        obj._execute_query.return_value = [
            {"id": "PROJ-A"},
            {"id": "PROJ-B"},
        ]
        with patch.object(obj, "get_project", side_effect=[
            {"project_id": "PROJ-A", "name": "A", "path": None},
            {"project_id": "PROJ-B", "name": "B", "path": None},
        ]):
            result = obj.list_projects()
        assert len(result) == 2
        assert result[0]["project_id"] == "PROJ-A"


class TestProjectLinkingMixin:
    """Tests for ProjectLinkingOperations mixin methods."""

    def _make_mixin(self):
        obj = ProjectLinkingOperations.__new__(ProjectLinkingOperations)
        obj._driver = MagicMock()
        obj.database = "test_db"
        obj._connected = True
        obj._execute_query = MagicMock(return_value=[])
        return obj

    def test_link_project_to_plan_error(self):
        obj = self._make_mixin()
        obj._driver.transaction.side_effect = Exception("fail")
        result = obj.link_project_to_plan("PROJ-1", "PLAN-1")
        assert result is False

    def test_link_plan_to_epic_error(self):
        obj = self._make_mixin()
        obj._driver.transaction.side_effect = Exception("fail")
        result = obj.link_plan_to_epic("PLAN-1", "EPIC-1")
        assert result is False

    def test_link_epic_to_task_error(self):
        obj = self._make_mixin()
        obj._driver.transaction.side_effect = Exception("fail")
        result = obj.link_epic_to_task("EPIC-1", "TASK-1")
        assert result is False

    def test_link_project_to_session_error(self):
        obj = self._make_mixin()
        obj._driver.transaction.side_effect = Exception("fail")
        result = obj.link_project_to_session("PROJ-1", "SESSION-1")
        assert result is False

    def test_get_project_sessions_error(self):
        obj = self._make_mixin()
        obj._execute_query.side_effect = Exception("fail")
        result = obj.get_project_sessions("PROJ-1")
        assert result == []

    def test_get_project_sessions_returns_ids(self):
        obj = self._make_mixin()
        obj._execute_query.return_value = [
            {"sid": "SESSION-1"},
            {"sid": "SESSION-2"},
        ]
        result = obj.get_project_sessions("PROJ-1")
        assert result == ["SESSION-1", "SESSION-2"]

    def test_get_project_plans_error(self):
        obj = self._make_mixin()
        obj._execute_query.side_effect = Exception("fail")
        result = obj.get_project_plans("PROJ-1")
        assert result == []

    def test_get_project_plans_returns_ids(self):
        obj = self._make_mixin()
        obj._execute_query.return_value = [
            {"plid": "PLAN-1"},
        ]
        result = obj.get_project_plans("PROJ-1")
        assert result == ["PLAN-1"]
