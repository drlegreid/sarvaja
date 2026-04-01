"""
Unit tests for Rule Relations Service.

Per DOC-SIZE-01-v1: Tests for extracted rules_relations.py module.
Tests: get_rule_document_paths, get_rule_linkage_counts, get_rule_tasks,
       get_rule_dependencies, create_rule_dependency, dependency_overview.
"""

import pytest
from unittest.mock import patch, MagicMock

from governance.services.rules_relations import (
    get_rule_document_paths,
    get_rule_linkage_counts,
    get_rule_tasks,
    get_rule_dependencies,
    create_rule_dependency,
    dependency_overview,
    _get_client_or_raise,
)


class TestGetClientOrRaise:
    """Tests for _get_client_or_raise() helper."""

    @patch("governance.services.rules_relations.get_client", return_value=None)
    def test_raises_when_no_client(self, mock_get):
        with pytest.raises(ConnectionError, match="TypeDB not connected"):
            _get_client_or_raise()

    @patch("governance.services.rules_relations.get_client")
    def test_returns_client(self, mock_get):
        mock_client = MagicMock()
        mock_get.return_value = mock_client
        assert _get_client_or_raise() is mock_client


class TestGetRuleDocumentPaths:
    """Tests for get_rule_document_paths()."""

    def test_empty_ids_returns_empty(self):
        mock_client = MagicMock()
        assert get_rule_document_paths(mock_client, []) == {}

    def test_returns_paths(self):
        mock_client = MagicMock()
        mock_client.execute_query.return_value = [
            {"rid": "RULE-01", "path": "/docs/rule01.md"},
            {"rid": "RULE-02", "path": "/docs/rule02.md"},
        ]
        result = get_rule_document_paths(mock_client, ["RULE-01", "RULE-02"])
        assert result == {"RULE-01": "/docs/rule01.md", "RULE-02": "/docs/rule02.md"}

    def test_skips_missing_fields(self):
        mock_client = MagicMock()
        mock_client.execute_query.return_value = [
            {"rid": "RULE-01", "path": "/docs/rule01.md"},
            {"rid": None, "path": "/docs/orphan.md"},
            {"rid": "RULE-02"},
        ]
        result = get_rule_document_paths(mock_client, ["RULE-01", "RULE-02"])
        assert len(result) == 1
        assert result["RULE-01"] == "/docs/rule01.md"

    def test_query_error_returns_empty(self):
        mock_client = MagicMock()
        mock_client.execute_query.side_effect = Exception("TypeDB down")
        result = get_rule_document_paths(mock_client, ["RULE-01"])
        assert result == {}


class TestGetRuleLinkageCounts:
    """Tests for get_rule_linkage_counts()."""

    def test_empty_ids_returns_empty(self):
        mock_client = MagicMock()
        assert get_rule_linkage_counts(mock_client, []) == {}

    def test_counts_tasks_and_sessions(self):
        mock_client = MagicMock()
        # First call returns task links, second returns session links
        mock_client.execute_query.side_effect = [
            [{"rid": "R-01"}, {"rid": "R-01"}, {"rid": "R-02"}],
            [{"rid": "R-01"}, {"rid": "R-03"}],
        ]
        result = get_rule_linkage_counts(mock_client, ["R-01", "R-02", "R-03"])
        assert result["R-01"]["tasks"] == 2
        assert result["R-01"]["sessions"] == 1
        assert result["R-02"]["tasks"] == 1
        assert result["R-03"]["sessions"] == 1

    def test_task_query_error_still_counts_sessions(self):
        mock_client = MagicMock()
        mock_client.execute_query.side_effect = [
            Exception("task query fail"),
            [{"rid": "R-01"}],
        ]
        result = get_rule_linkage_counts(mock_client, ["R-01"])
        assert result["R-01"]["sessions"] == 1


class TestGetRuleTasks:
    """Tests for get_rule_tasks()."""

    @patch("governance.services.rules_relations.get_client")
    def test_returns_tasks(self, mock_get):
        mock_client = MagicMock()
        mock_client.get_tasks_for_rule.return_value = [
            {"task_id": "T-1"}, {"task_id": "T-2"}
        ]
        mock_get.return_value = mock_client
        result = get_rule_tasks("RULE-01")
        assert result["rule_id"] == "RULE-01"
        assert result["count"] == 2

    @patch("governance.services.rules_relations.get_client")
    @patch("governance.services.rules_relations.normalize_rule_id")
    def test_falls_back_to_legacy_id(self, mock_norm, mock_get):
        mock_client = MagicMock()
        mock_client.get_tasks_for_rule.side_effect = [[], [{"task_id": "T-1"}]]
        mock_get.return_value = mock_client
        mock_norm.return_value = "LEGACY-01"
        result = get_rule_tasks("RULE-01")
        assert result["count"] == 1

    @patch("governance.services.rules_relations.get_client", return_value=None)
    def test_no_client_raises(self, mock_get):
        with pytest.raises(ConnectionError):
            get_rule_tasks("RULE-01")


class TestGetRuleDependencies:
    """Tests for get_rule_dependencies()."""

    @patch("governance.services.rules_relations.get_client")
    def test_returns_deps_and_dependents(self, mock_get):
        mock_client = MagicMock()
        mock_client.get_rule_dependencies.return_value = ["R-DEP"]
        mock_client.get_rules_depending_on.return_value = ["R-BY"]
        mock_get.return_value = mock_client
        with patch("governance.services.rules.resolve_rule", return_value=("R-01", None)):
            result = get_rule_dependencies("R-01")
        assert result["depends_on"] == ["R-DEP"]
        assert result["depended_by"] == ["R-BY"]


class TestCreateRuleDependency:
    """Tests for create_rule_dependency()."""

    @patch("governance.services.rules_relations.get_client")
    def test_creates_dependency(self, mock_get):
        mock_client = MagicMock()
        mock_client.create_rule_dependency.return_value = True
        mock_get.return_value = mock_client
        with patch("governance.services.rules.resolve_rule", side_effect=[("R-01", None), ("R-02", None)]):
            assert create_rule_dependency("R-01", "R-02") is True
        mock_client.create_rule_dependency.assert_called_once_with("R-01", "R-02")

    @patch("governance.services.rules_relations.get_client")
    def test_returns_false_on_failure(self, mock_get):
        mock_client = MagicMock()
        mock_client.create_rule_dependency.return_value = False
        mock_get.return_value = mock_client
        with patch("governance.services.rules.resolve_rule", side_effect=[("R-01", None), ("R-02", None)]):
            assert create_rule_dependency("R-01", "R-02") is False


class TestDependencyOverview:
    """Tests for dependency_overview()."""

    @patch("governance.services.rules_relations.get_client")
    def test_overview_structure(self, mock_get):
        mock_rule = MagicMock()
        mock_rule.id = "R-01"
        mock_client = MagicMock()
        mock_client.get_all_rules.return_value = [mock_rule]
        mock_client.get_all_dependencies.return_value = {}
        mock_get.return_value = mock_client
        result = dependency_overview()
        assert result["total_rules"] == 1
        assert result["orphan_count"] == 1
        assert "R-01" in result["orphan_rules"]
        assert result["circular_count"] == 0

    @patch("governance.services.rules_relations.get_client")
    def test_non_orphan_with_deps(self, mock_get):
        r1 = MagicMock(); r1.id = "R-01"
        r2 = MagicMock(); r2.id = "R-02"
        mock_client = MagicMock()
        mock_client.get_all_rules.return_value = [r1, r2]
        mock_client.get_all_dependencies.return_value = {"R-01": ["R-02"]}
        mock_get.return_value = mock_client
        result = dependency_overview()
        assert result["total_dependencies"] == 1
        assert result["orphan_count"] == 0
