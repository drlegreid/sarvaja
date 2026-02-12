"""
Unit tests for TypeDB Rule Read Queries.

Per DOC-SIZE-01-v1: Tests for typedb/queries/rules/read.py module.
Tests: RuleReadQueries — _fetch_optional_rule_attrs, get_all_rules,
       get_active_rules, get_rule_by_id, get_rules_by_category,
       get_tasks_for_rule.
"""

from unittest.mock import MagicMock

import pytest

from governance.typedb.queries.rules.read import RuleReadQueries


class _ConcreteReader(RuleReadQueries):
    """Concrete class for testing the mixin."""

    def __init__(self):
        self._query_results = []
        self._call_index = 0
        self._results_list = None

    def _execute_query(self, query):
        if self._results_list is not None:
            if self._call_index < len(self._results_list):
                result = self._results_list[self._call_index]
                self._call_index += 1
                return result
            return []
        return self._query_results

    def _set_sequential_results(self, results_list):
        self._results_list = results_list
        self._call_index = 0


class TestFetchOptionalRuleAttrs:
    def test_all_found(self):
        reader = _ConcreteReader()
        reader._set_sequential_results([
            [{"type": "governance"}],   # rule-type
            [{"sid": "GOV-01-v1"}],     # semantic-id
            [{"app": "all agents"}],    # applicability
        ])
        rt, sid, app = reader._fetch_optional_rule_attrs("RULE-001")
        assert rt == "governance"
        assert sid == "GOV-01-v1"
        assert app == "all agents"

    def test_none_found(self):
        reader = _ConcreteReader()
        reader._set_sequential_results([[], [], []])
        rt, sid, app = reader._fetch_optional_rule_attrs("RULE-001")
        assert rt is None
        assert sid is None
        assert app is None

    def test_exception_handled(self):
        reader = _ConcreteReader()
        original = reader._execute_query
        call_count = [0]
        def failing_query(q):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("query error")
            return []
        reader._execute_query = failing_query
        rt, sid, app = reader._fetch_optional_rule_attrs("RULE-001")
        assert rt is None  # All should be None (graceful)


class TestGetAllRules:
    def test_with_rules(self):
        reader = _ConcreteReader()
        reader._set_sequential_results([
            # Main query
            [{"id": "R-1", "name": "Rule 1", "cat": "GOV", "pri": "HIGH",
              "stat": "ACTIVE", "dir": "Do X"}],
            # Optional attr queries (3 per rule)
            [], [], [],
        ])
        rules = reader.get_all_rules()
        assert len(rules) == 1
        assert rules[0].id == "R-1"
        assert rules[0].name == "Rule 1"

    def test_empty(self):
        reader = _ConcreteReader()
        reader._query_results = []
        rules = reader.get_all_rules()
        assert rules == []


class TestGetActiveRules:
    def test_returns_active_only(self):
        reader = _ConcreteReader()
        reader._set_sequential_results([
            [{"id": "R-1", "name": "Active Rule", "cat": "GOV", "pri": "HIGH",
              "dir": "Do X"}],
            [], [], [],  # optional attrs
        ])
        rules = reader.get_active_rules()
        assert len(rules) == 1
        assert rules[0].status == "ACTIVE"


class TestGetRuleById:
    def test_found(self):
        reader = _ConcreteReader()
        reader._set_sequential_results([
            [{"name": "Rule 1", "cat": "GOV", "pri": "HIGH",
              "stat": "ACTIVE", "dir": "Do X"}],
            [], [], [],  # optional attrs
        ])
        rule = reader.get_rule_by_id("R-1")
        assert rule is not None
        assert rule.id == "R-1"

    def test_not_found(self):
        reader = _ConcreteReader()
        reader._query_results = []
        rule = reader.get_rule_by_id("NONEXISTENT")
        assert rule is None


class TestGetRulesByCategory:
    def test_with_results(self):
        reader = _ConcreteReader()
        reader._query_results = [
            {"id": "R-1", "name": "Rule 1", "pri": "HIGH",
             "stat": "ACTIVE", "dir": "Do X"},
        ]
        rules = reader.get_rules_by_category("GOV")
        assert len(rules) == 1
        assert rules[0].category == "GOV"

    def test_empty(self):
        reader = _ConcreteReader()
        reader._query_results = []
        rules = reader.get_rules_by_category("NONEXISTENT")
        assert rules == []


class TestGetTasksForRule:
    def test_with_tasks(self):
        reader = _ConcreteReader()
        reader._set_sequential_results([
            [{"tid": "T-1", "tname": "Task 1", "tstat": "DONE"}],
            [{"p": "HIGH"}],  # priority query
        ])
        tasks = reader.get_tasks_for_rule("RULE-001")
        assert len(tasks) == 1
        assert tasks[0]["task_id"] == "T-1"
        assert tasks[0]["priority"] == "HIGH"

    def test_priority_error_defaults_medium(self):
        reader = _ConcreteReader()
        call_count = [0]
        def query_fn(q):
            call_count[0] += 1
            if call_count[0] == 1:
                return [{"tid": "T-1", "tname": "Task", "tstat": "OPEN"}]
            raise Exception("priority query failed")
        reader._execute_query = query_fn
        tasks = reader.get_tasks_for_rule("RULE-001")
        assert tasks[0]["priority"] == "MEDIUM"

    def test_empty(self):
        reader = _ConcreteReader()
        reader._query_results = []
        tasks = reader.get_tasks_for_rule("RULE-999")
        assert tasks == []
