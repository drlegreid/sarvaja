"""
Unit tests for Kanren TypeDB Loader.

Per DOC-SIZE-01-v1: Tests for kanren/loader.py module.
Tests: RuleConstraint, load_rules_from_typedb, populate_kanren_facts,
       TypeDBKanrenBridge.
"""

import json
import pytest

from governance.kanren.loader import (
    RuleConstraint,
    load_rules_from_typedb,
    populate_kanren_facts,
    TypeDBKanrenBridge,
    query_rules_by_priority,
)


def _sample_rule_data():
    return {
        "id": "RULE-001",
        "semantic_id": "GOV-RULE-01-v1",
        "name": "Test Rule",
        "category": "governance",
        "priority": "CRITICAL",
        "directive": "Do X",
        "rule_type": "FOUNDATIONAL",
    }


class TestRuleConstraint:
    """Tests for RuleConstraint dataclass."""

    def test_basic(self):
        rc = RuleConstraint(
            rule_id="R-1", semantic_id="S-1", name="N",
            category="governance", priority="HIGH", directive="D",
            rule_type="OPERATIONAL",
        )
        assert rc.rule_id == "R-1"
        assert rc.priority == "HIGH"

    def test_from_dict(self):
        rc = RuleConstraint.from_dict(_sample_rule_data())
        assert rc.rule_id == "RULE-001"
        assert rc.semantic_id == "GOV-RULE-01-v1"
        assert rc.category == "governance"
        assert rc.priority == "CRITICAL"

    def test_from_dict_defaults(self):
        rc = RuleConstraint.from_dict({})
        assert rc.rule_id == ""
        assert rc.priority == "MEDIUM"
        assert rc.rule_type == "OPERATIONAL"


class TestLoadRulesFromTypeDB:
    """Tests for load_rules_from_typedb()."""

    def test_none_input(self):
        assert load_rules_from_typedb(None) == []

    def test_empty_string(self):
        assert load_rules_from_typedb("") == []

    def test_invalid_json(self):
        assert load_rules_from_typedb("not json") == []

    def test_valid_json(self):
        data = json.dumps([_sample_rule_data()])
        rules = load_rules_from_typedb(data)
        assert len(rules) == 1
        assert rules[0].rule_id == "RULE-001"

    def test_list_input(self):
        rules = load_rules_from_typedb([_sample_rule_data()])
        assert len(rules) == 1

    def test_multiple_rules(self):
        data = json.dumps([_sample_rule_data(), {"id": "RULE-002", "name": "R2"}])
        rules = load_rules_from_typedb(data)
        assert len(rules) == 2


class TestPopulateKanrenFacts:
    """Tests for populate_kanren_facts()."""

    def test_empty(self):
        counts = populate_kanren_facts([])
        assert counts["priority"] == 0
        assert counts["critical"] == 0

    def test_critical_rule(self):
        rule = RuleConstraint.from_dict(_sample_rule_data())
        counts = populate_kanren_facts([rule])
        assert counts["priority"] == 1
        assert counts["critical"] == 1

    def test_non_critical_rule(self):
        data = _sample_rule_data()
        data["priority"] = "LOW"
        rule = RuleConstraint.from_dict(data)
        counts = populate_kanren_facts([rule])
        assert counts["priority"] == 1
        assert counts["critical"] == 0

    def test_category_counts(self):
        rule = RuleConstraint.from_dict(_sample_rule_data())
        counts = populate_kanren_facts([rule])
        assert counts["category"] == 1

    def test_rule_type_counts(self):
        rule = RuleConstraint.from_dict(_sample_rule_data())
        counts = populate_kanren_facts([rule])
        assert counts["rule_type"] == 1


class TestTypeDBKanrenBridge:
    """Tests for TypeDBKanrenBridge class."""

    def test_init(self):
        bridge = TypeDBKanrenBridge()
        assert bridge.is_loaded() is False
        assert bridge.get_rules() == []

    def test_load_from_mcp(self):
        bridge = TypeDBKanrenBridge()
        data = json.dumps([_sample_rule_data()])
        counts = bridge.load_from_mcp(data)
        assert bridge.is_loaded() is True
        assert len(bridge.get_rules()) == 1
        assert counts["priority"] == 1

    def test_validate_not_loaded(self):
        bridge = TypeDBKanrenBridge()
        result = bridge.validate_rule("RULE-001")
        assert result["compliant"] is False
        assert "not loaded" in result["violations"][0]

    def test_validate_loaded(self):
        bridge = TypeDBKanrenBridge()
        data = json.dumps([_sample_rule_data()])
        bridge.load_from_mcp(data)
        result = bridge.validate_rule("RULE-001", has_evidence=True, agent_trust=0.95)
        assert isinstance(result, dict)
        assert "compliant" in result

    def test_get_rules_by_category(self):
        bridge = TypeDBKanrenBridge()
        data = json.dumps([
            _sample_rule_data(),
            {**_sample_rule_data(), "id": "RULE-002", "category": "testing"},
        ])
        bridge.load_from_mcp(data)
        gov_rules = bridge.get_rules_by_category("governance")
        assert len(gov_rules) == 1
        assert gov_rules[0].rule_id == "RULE-001"
