"""
Unit tests for Project TypeDB query operations.

Per GOV-PROJECT-01-v1: Tests CRUD + linking query classes.
"""

import pytest
from unittest.mock import MagicMock, patch

from governance.typedb.queries.projects.crud import (
    ProjectCRUDOperations,
    _extract_attr,
)
from governance.typedb.queries.projects.linking import ProjectLinkingOperations


class TestExtractAttr:
    """Tests for _extract_attr() helper."""

    def test_list_format(self):
        data = {"project-id": [{"value": "PROJ-1"}]}
        assert _extract_attr(data, "project-id") == "PROJ-1"

    def test_dict_format(self):
        data = {"project-id": {"value": "PROJ-2"}}
        assert _extract_attr(data, "project-id") == "PROJ-2"

    def test_none(self):
        data = {}
        assert _extract_attr(data, "project-id") is None

    def test_empty_list(self):
        data = {"project-id": []}
        assert _extract_attr(data, "project-id") is None

    def test_string_fallback(self):
        data = {"project-id": "PROJ-3"}
        assert _extract_attr(data, "project-id") == "PROJ-3"


class TestProjectCRUDMixin:
    """Tests for ProjectCRUDOperations mixin methods."""

    def _make_mixin(self):
        """Create a mixin instance with mocked TypeDB driver."""
        obj = ProjectCRUDOperations.__new__(ProjectCRUDOperations)
        obj._driver = MagicMock()
        obj.database = "test_db"
        return obj

    def test_insert_checks_existing(self):
        obj = self._make_mixin()
        with patch.object(obj, "get_project", return_value={"project_id": "PROJ-1"}):
            result = obj.insert_project("PROJ-1", "Test")
        assert result is None

    def test_get_project_no_results(self):
        obj = self._make_mixin()
        mock_tx = MagicMock()
        mock_query_result = MagicMock()
        mock_query_result.resolve.return_value = []
        mock_tx.query.return_value = mock_query_result
        obj._driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        obj._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        result = obj.get_project("PROJ-NOPE")
        assert result is None

    def test_delete_nonexistent(self):
        obj = self._make_mixin()
        with patch.object(obj, "get_project", return_value=None):
            result = obj.delete_project("PROJ-NOPE")
        assert result is False

    def test_list_projects_error_returns_empty(self):
        obj = self._make_mixin()
        obj._driver.transaction.side_effect = Exception("connection refused")
        result = obj.list_projects()
        assert result == []


class TestProjectLinkingMixin:
    """Tests for ProjectLinkingOperations mixin methods."""

    def _make_mixin(self):
        obj = ProjectLinkingOperations.__new__(ProjectLinkingOperations)
        obj._driver = MagicMock()
        obj.database = "test_db"
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
        obj._driver.transaction.side_effect = Exception("fail")
        result = obj.get_project_sessions("PROJ-1")
        assert result == []

    def test_get_project_plans_error(self):
        obj = self._make_mixin()
        obj._driver.transaction.side_effect = Exception("fail")
        result = obj.get_project_plans("PROJ-1")
        assert result == []
