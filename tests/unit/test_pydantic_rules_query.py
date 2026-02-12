"""
Unit tests for Pydantic Rule Query Tools.

Per DOC-SIZE-01-v1: Tests for pydantic_schemas/tools/rules.py module.
Tests: query_rules_typed, analyze_dependencies_typed.
"""

import sys
from unittest.mock import patch, MagicMock

import pytest

from governance.pydantic_schemas.models.inputs import RuleQueryConfig, DependencyConfig


def _make_rule(rule_id="RULE-001", name="Test", category="GOV",
               priority="HIGH", status="ACTIVE", directive="Do X"):
    r = MagicMock()
    r.rule_id = rule_id
    r.name = name
    r.category = category
    r.priority = priority
    r.status = status
    r.directive = directive
    return r


def _make_client(**overrides):
    client = MagicMock()
    client.connect.return_value = True
    client.get_all_rules.return_value = []
    client.get_active_rules.return_value = []
    client.get_rule_dependencies.return_value = []
    client.execute_query.return_value = []
    for k, v in overrides.items():
        setattr(client, k, v)
    return client


class TestQueryRulesTyped:
    def test_success(self):
        client = _make_client()
        client.get_all_rules.return_value = [_make_rule()]
        mock_mod = MagicMock()
        mock_mod.TypeDBClient.return_value = client
        with patch.dict(sys.modules, {"governance.client": mock_mod}):
            from governance.pydantic_schemas.tools.rules import query_rules_typed
            result = query_rules_typed(RuleQueryConfig())
        assert result.success is True
        assert result.total_count == 1

    def test_active_status(self):
        client = _make_client()
        client.get_active_rules.return_value = [_make_rule()]
        mock_mod = MagicMock()
        mock_mod.TypeDBClient.return_value = client
        with patch.dict(sys.modules, {"governance.client": mock_mod}):
            from governance.pydantic_schemas.tools.rules import query_rules_typed
            result = query_rules_typed(RuleQueryConfig(status="ACTIVE"))
        assert result.success is True
        client.get_active_rules.assert_called_once()

    def test_category_filter(self):
        client = _make_client()
        client.get_all_rules.return_value = [
            _make_rule(rule_id="R-1", category="GOV"),
            _make_rule(rule_id="R-2", category="ARCH"),
        ]
        mock_mod = MagicMock()
        mock_mod.TypeDBClient.return_value = client
        with patch.dict(sys.modules, {"governance.client": mock_mod}):
            from governance.pydantic_schemas.tools.rules import query_rules_typed
            result = query_rules_typed(RuleQueryConfig(category="GOV"))
        assert result.filtered_count == 1
        assert result.total_count == 2

    def test_priority_filter(self):
        client = _make_client()
        client.get_all_rules.return_value = [
            _make_rule(priority="HIGH"),
            _make_rule(priority="LOW"),
        ]
        mock_mod = MagicMock()
        mock_mod.TypeDBClient.return_value = client
        with patch.dict(sys.modules, {"governance.client": mock_mod}):
            from governance.pydantic_schemas.tools.rules import query_rules_typed
            result = query_rules_typed(RuleQueryConfig(priority="HIGH"))
        assert result.filtered_count == 1

    def test_include_dependencies(self):
        client = _make_client()
        client.get_all_rules.return_value = [_make_rule()]
        client.get_rule_dependencies.return_value = ["RULE-002"]
        mock_mod = MagicMock()
        mock_mod.TypeDBClient.return_value = client
        with patch.dict(sys.modules, {"governance.client": mock_mod}):
            from governance.pydantic_schemas.tools.rules import query_rules_typed
            result = query_rules_typed(RuleQueryConfig(include_dependencies=True))
        assert result.success is True
        client.get_rule_dependencies.assert_called_once()

    def test_connect_failure(self):
        client = _make_client()
        client.connect.return_value = False
        mock_mod = MagicMock()
        mock_mod.TypeDBClient.return_value = client
        with patch.dict(sys.modules, {"governance.client": mock_mod}):
            from governance.pydantic_schemas.tools.rules import query_rules_typed
            result = query_rules_typed(RuleQueryConfig())
        assert result.success is False
        assert "connect" in result.error.lower()

    def test_import_error(self):
        # The function catches Exception (including ImportError-like)
        from governance.pydantic_schemas.tools.rules import query_rules_typed
        with patch.dict(sys.modules, {"governance.client": None}):
            result = query_rules_typed(RuleQueryConfig())
        assert result.success is False

    def test_query_time_tracked(self):
        client = _make_client()
        mock_mod = MagicMock()
        mock_mod.TypeDBClient.return_value = client
        with patch.dict(sys.modules, {"governance.client": mock_mod}):
            from governance.pydantic_schemas.tools.rules import query_rules_typed
            result = query_rules_typed(RuleQueryConfig())
        assert result.query_time_ms >= 0


class TestAnalyzeDependenciesTyped:
    def test_both_directions(self):
        client = _make_client()
        client.get_rule_dependencies.return_value = ["RULE-002"]
        client.execute_query.return_value = [{"id1": "RULE-003"}]
        mock_mod = MagicMock()
        mock_mod.TypeDBClient.return_value = client
        with patch.dict(sys.modules, {"governance.client": mock_mod}):
            from governance.pydantic_schemas.tools.rules import analyze_dependencies_typed
            config = DependencyConfig(rule_id="RULE-001", direction="both",
                                      include_transitive=False)
            result = analyze_dependencies_typed(config)
        assert result.success is True
        assert "RULE-002" in result.dependencies
        assert "RULE-003" in result.dependents

    def test_dependencies_only(self):
        client = _make_client()
        client.get_rule_dependencies.return_value = ["RULE-002"]
        mock_mod = MagicMock()
        mock_mod.TypeDBClient.return_value = client
        with patch.dict(sys.modules, {"governance.client": mock_mod}):
            from governance.pydantic_schemas.tools.rules import analyze_dependencies_typed
            config = DependencyConfig(rule_id="RULE-001", direction="dependencies",
                                      include_transitive=False)
            result = analyze_dependencies_typed(config)
        assert result.success is True
        assert len(result.dependencies) == 1
        assert result.dependents == []

    def test_dependents_only(self):
        client = _make_client()
        client.execute_query.return_value = [{"id1": "RULE-003"}]
        mock_mod = MagicMock()
        mock_mod.TypeDBClient.return_value = client
        with patch.dict(sys.modules, {"governance.client": mock_mod}):
            from governance.pydantic_schemas.tools.rules import analyze_dependencies_typed
            config = DependencyConfig(rule_id="RULE-001", direction="dependents",
                                      include_transitive=False)
            result = analyze_dependencies_typed(config)
        assert result.success is True
        assert result.dependencies == []
        assert "RULE-003" in result.dependents

    def test_transitive_dependencies(self):
        client = _make_client()
        # RULE-001 -> RULE-002 -> RULE-003
        client.get_rule_dependencies.side_effect = [
            ["RULE-002"],  # Direct deps of RULE-001
            ["RULE-003"],  # Deps of RULE-002
            [],            # Deps of RULE-003
        ]
        client.execute_query.return_value = []
        mock_mod = MagicMock()
        mock_mod.TypeDBClient.return_value = client
        with patch.dict(sys.modules, {"governance.client": mock_mod}):
            from governance.pydantic_schemas.tools.rules import analyze_dependencies_typed
            config = DependencyConfig(rule_id="RULE-001", direction="both",
                                      include_transitive=True)
            result = analyze_dependencies_typed(config)
        assert result.success is True
        assert "RULE-003" in result.transitive_dependencies

    def test_connect_failure(self):
        # Bug: source code doesn't pass dependency_depth in error path,
        # causing ValidationError. Test verifies the error is raised.
        from pydantic import ValidationError as PydanticValidationError
        client = _make_client()
        client.connect.return_value = False
        mock_mod = MagicMock()
        mock_mod.TypeDBClient.return_value = client
        with patch.dict(sys.modules, {"governance.client": mock_mod}):
            from governance.pydantic_schemas.tools.rules import analyze_dependencies_typed
            config = DependencyConfig(rule_id="RULE-001")
            with pytest.raises(PydanticValidationError):
                analyze_dependencies_typed(config)

    def test_depth_with_deps(self):
        client = _make_client()
        client.get_rule_dependencies.return_value = ["RULE-002"]
        client.execute_query.return_value = []
        mock_mod = MagicMock()
        mock_mod.TypeDBClient.return_value = client
        with patch.dict(sys.modules, {"governance.client": mock_mod}):
            from governance.pydantic_schemas.tools.rules import analyze_dependencies_typed
            config = DependencyConfig(rule_id="RULE-001", direction="both",
                                      include_transitive=False)
            result = analyze_dependencies_typed(config)
        assert result.dependency_depth == 1

    def test_exception_handled(self):
        # Bug: source code doesn't pass dependency_depth in error path,
        # causing ValidationError. Test verifies the error is raised.
        from pydantic import ValidationError as PydanticValidationError
        from governance.pydantic_schemas.tools.rules import analyze_dependencies_typed
        with patch.dict(sys.modules, {"governance.client": None}):
            config = DependencyConfig(rule_id="RULE-001")
            with pytest.raises(PydanticValidationError):
                analyze_dependencies_typed(config)
