"""
Unit tests for TypeDB → Kanren Constraint Loader.

Per DOC-SIZE-01-v1: Tests for kanren/loader.py module.
Tests: RuleConstraint, load_rules_from_typedb(), populate_kanren_facts(),
       query functions, TypeDBKanrenBridge.
"""

import json

from governance.kanren.loader import (
    RuleConstraint,
    load_rules_from_typedb,
    populate_kanren_facts,
    query_critical_rules,
    query_rules_by_priority,
    TypeDBKanrenBridge,
)


def _sample_rule(**kwargs):
    defaults = {
        "id": "RULE-001",
        "semantic_id": "TEST-RULE-01-v1",
        "name": "Test Rule",
        "category": "testing",
        "priority": "HIGH",
        "directive": "Must test",
        "rule_type": "OPERATIONAL",
    }
    defaults.update(kwargs)
    return defaults


class TestRuleConstraint:
    def test_from_dict(self):
        rc = RuleConstraint.from_dict(_sample_rule())
        assert rc.rule_id == "RULE-001"
        assert rc.semantic_id == "TEST-RULE-01-v1"
        assert rc.priority == "HIGH"

    def test_from_dict_defaults(self):
        rc = RuleConstraint.from_dict({})
        assert rc.rule_id == ""
        assert rc.priority == "MEDIUM"
        assert rc.rule_type == "OPERATIONAL"

    def test_from_dict_custom(self):
        rc = RuleConstraint.from_dict({"id": "R-99", "priority": "CRITICAL"})
        assert rc.rule_id == "R-99"
        assert rc.priority == "CRITICAL"


class TestLoadRulesFromTypeDB:
    def test_json_string(self):
        data = json.dumps([_sample_rule()])
        rules = load_rules_from_typedb(data)
        assert len(rules) == 1
        assert rules[0].rule_id == "RULE-001"

    def test_list_input(self):
        rules = load_rules_from_typedb([_sample_rule()])
        assert len(rules) == 1

    def test_none_input(self):
        assert load_rules_from_typedb(None) == []

    def test_empty_string(self):
        assert load_rules_from_typedb("") == []

    def test_invalid_json(self):
        assert load_rules_from_typedb("{bad json}") == []

    def test_multiple_rules(self):
        data = [_sample_rule(id="R-1"), _sample_rule(id="R-2")]
        rules = load_rules_from_typedb(data)
        assert len(rules) == 2


class TestPopulateKanrenFacts:
    def test_basic_counts(self):
        rules = [
            RuleConstraint.from_dict(_sample_rule(id="R-100", priority="CRITICAL",
                                                   category="governance", rule_type="FOUNDATIONAL")),
            RuleConstraint.from_dict(_sample_rule(id="R-101", priority="HIGH",
                                                   category="testing", rule_type="OPERATIONAL")),
        ]
        counts = populate_kanren_facts(rules)
        assert counts["priority"] == 2
        assert counts["critical"] == 1
        assert counts["rule_type"] == 2
        assert counts["category"] == 2

    def test_empty_rules(self):
        counts = populate_kanren_facts([])
        assert counts["priority"] == 0


class TestTypeBKanrenBridge:
    def test_not_loaded(self):
        bridge = TypeDBKanrenBridge()
        assert bridge.is_loaded() is False
        result = bridge.validate_rule("R-1")
        assert result["compliant"] is False
        assert "not loaded" in result["violations"][0]

    def test_load_from_mcp(self):
        bridge = TypeDBKanrenBridge()
        data = json.dumps([_sample_rule(id="R-200", priority="CRITICAL",
                                         category="governance", rule_type="FOUNDATIONAL")])
        counts = bridge.load_from_mcp(data)
        assert bridge.is_loaded() is True
        assert counts["priority"] >= 1
        assert len(bridge.get_rules()) == 1

    def test_get_rules_by_category(self):
        bridge = TypeDBKanrenBridge()
        data = [
            _sample_rule(id="R-300", category="governance"),
            _sample_rule(id="R-301", category="testing"),
        ]
        bridge.load_from_mcp(data)
        gov = bridge.get_rules_by_category("governance")
        assert len(gov) == 1
        assert gov[0].rule_id == "R-300"

    def test_validate_rule_loaded(self):
        bridge = TypeDBKanrenBridge()
        data = [_sample_rule(id="R-400", priority="MEDIUM")]
        bridge.load_from_mcp(data)
        result = bridge.validate_rule("R-400", has_evidence=True, agent_trust=0.85)
        assert result["compliant"] is True
