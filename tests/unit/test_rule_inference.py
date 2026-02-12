"""
Unit tests for TypeDB Rule Inference Queries.

Per DOC-SIZE-01-v1: Tests for governance/typedb/queries/rules/inference.py module.
Tests: RuleInferenceQueries — get_rule_dependencies, get_rules_depending_on,
       find_conflicts, create_rule_dependency, get_decision_impacts.
"""

from unittest.mock import MagicMock, patch

from governance.typedb.queries.rules.inference import RuleInferenceQueries


class _TestClient(RuleInferenceQueries):
    """Concrete class for testing the mixin."""

    def __init__(self, query_results=None):
        self._query_results = query_results or []
        self._driver = MagicMock()
        self.database = "test-db"

    def _execute_query(self, query, infer=False):
        return self._query_results


# ── get_rule_dependencies ──────────────────────────────────


class TestGetRuleDependencies:
    def test_returns_dep_ids(self):
        client = _TestClient([
            {"dep_id": "RULE-002"},
            {"dep_id": "RULE-003"},
        ])
        result = client.get_rule_dependencies("RULE-001")
        assert result == ["RULE-002", "RULE-003"]

    def test_no_dependencies(self):
        client = _TestClient([])
        result = client.get_rule_dependencies("RULE-001")
        assert result == []

    def test_single_dependency(self):
        client = _TestClient([{"dep_id": "RULE-X"}])
        result = client.get_rule_dependencies("RULE-Y")
        assert result == ["RULE-X"]


# ── get_rules_depending_on ────────────────────────────────


class TestGetRulesDependingOn:
    def test_returns_dependents(self):
        client = _TestClient([
            {"id": "RULE-A"},
            {"id": "RULE-B"},
        ])
        result = client.get_rules_depending_on("RULE-001")
        assert result == ["RULE-A", "RULE-B"]

    def test_no_dependents(self):
        client = _TestClient([])
        result = client.get_rules_depending_on("RULE-001")
        assert result == []


# ── find_conflicts ─────────────────────────────────────────


class TestFindConflicts:
    def test_returns_conflict_pairs(self):
        client = _TestClient([
            {"id1": "RULE-A", "id2": "RULE-B"},
            {"id1": "RULE-C", "id2": "RULE-D"},
        ])
        result = client.find_conflicts()
        assert len(result) == 2
        assert result[0] == {"rule1": "RULE-A", "rule2": "RULE-B"}
        assert result[1] == {"rule1": "RULE-C", "rule2": "RULE-D"}

    def test_no_conflicts(self):
        client = _TestClient([])
        result = client.find_conflicts()
        assert result == []


# ── create_rule_dependency ─────────────────────────────────


class TestCreateRuleDependency:
    def test_success(self):
        client = _TestClient()
        mock_tx = MagicMock()
        mock_tx.query.return_value.resolve.return_value = None
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        result = client.create_rule_dependency("RULE-A", "RULE-B")
        assert result is True
        mock_tx.commit.assert_called_once()

    def test_failure(self):
        client = _TestClient()
        client._driver.transaction.side_effect = Exception("TypeDB error")

        result = client.create_rule_dependency("RULE-A", "RULE-B")
        assert result is False


# ── get_decision_impacts ──────────────────────────────────


class TestGetDecisionImpacts:
    def test_returns_affected_rules(self):
        client = _TestClient([
            {"rid": "RULE-001"},
            {"rid": "RULE-002"},
        ])
        result = client.get_decision_impacts("DEC-001")
        assert result == ["RULE-001", "RULE-002"]

    def test_no_impacts(self):
        client = _TestClient([])
        result = client.get_decision_impacts("DEC-001")
        assert result == []
