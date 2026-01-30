"""
Tests for data integrity schemas.

Per P10.7: TypeDB entity schemas, valid values, and relation schemas.
Covers ENTITY_SCHEMAS, VALID_VALUES, RELATION_SCHEMAS structure.

Created: 2026-01-30
"""

import re
import pytest

from governance.integrity.schemas import (
    ENTITY_SCHEMAS,
    VALID_VALUES,
    RELATION_SCHEMAS,
)


class TestEntitySchemas:
    """Test entity schema definitions."""

    def test_all_entity_types_present(self):
        expected = {"rule", "decision", "task", "gap", "agent", "session"}
        assert set(ENTITY_SCHEMAS.keys()) == expected

    def test_each_has_required_fields(self):
        for entity_type, schema in ENTITY_SCHEMAS.items():
            assert "required" in schema, f"{entity_type} missing 'required'"
            assert isinstance(schema["required"], list)
            assert len(schema["required"]) > 0, f"{entity_type} has empty required"

    def test_each_has_optional_fields(self):
        for entity_type, schema in ENTITY_SCHEMAS.items():
            assert "optional" in schema, f"{entity_type} missing 'optional'"
            assert isinstance(schema["optional"], list)

    def test_each_has_id_pattern(self):
        for entity_type, schema in ENTITY_SCHEMAS.items():
            assert "id_pattern" in schema, f"{entity_type} missing 'id_pattern'"
            # Verify patterns compile
            re.compile(schema["id_pattern"])

    def test_rule_schema(self):
        s = ENTITY_SCHEMAS["rule"]
        assert "rule-id" in s["required"]
        assert "rule-name" in s["required"]
        assert "directive" in s["required"]

    def test_rule_id_pattern(self):
        pattern = re.compile(ENTITY_SCHEMAS["rule"]["id_pattern"])
        assert pattern.match("RULE-001")
        assert pattern.match("RULE-050")
        assert not pattern.match("RULE-1")
        assert not pattern.match("R-001")

    def test_decision_schema(self):
        s = ENTITY_SCHEMAS["decision"]
        assert "decision-id" in s["required"]
        assert "context" in s["required"]
        assert "rationale" in s["required"]

    def test_decision_id_pattern(self):
        pattern = re.compile(ENTITY_SCHEMAS["decision"]["id_pattern"])
        assert pattern.match("DECISION-001")
        assert not pattern.match("DEC-001")

    def test_task_schema(self):
        s = ENTITY_SCHEMAS["task"]
        assert "task-id" in s["required"]
        assert "task-status" in s["required"]

    def test_session_schema(self):
        s = ENTITY_SCHEMAS["session"]
        assert "session-id" in s["required"]
        assert "started-at" in s["optional"]

    def test_agent_schema(self):
        s = ENTITY_SCHEMAS["agent"]
        assert "agent-id" in s["required"]
        assert "agent-type" in s["required"]
        assert "trust-score" in s["optional"]


class TestValidValues:
    """Test valid value enumerations."""

    def test_priority_values(self):
        assert "CRITICAL" in VALID_VALUES["priority"]
        assert "HIGH" in VALID_VALUES["priority"]
        assert "MEDIUM" in VALID_VALUES["priority"]
        assert "LOW" in VALID_VALUES["priority"]

    def test_status_values(self):
        assert "ACTIVE" in VALID_VALUES["status"]
        assert "DRAFT" in VALID_VALUES["status"]
        assert "DEPRECATED" in VALID_VALUES["status"]

    def test_task_status_values(self):
        statuses = VALID_VALUES["task-status"]
        assert "TODO" in statuses
        assert "IN_PROGRESS" in statuses
        assert "DONE" in statuses

    def test_severity_values(self):
        assert VALID_VALUES["severity"] == VALID_VALUES["priority"]  # Same levels

    def test_agent_type_values(self):
        assert "claude-code" in VALID_VALUES["agent-type"]

    def test_gap_status_values(self):
        assert "OPEN" in VALID_VALUES["gap-status"]
        assert "RESOLVED" in VALID_VALUES["gap-status"]


class TestRelationSchemas:
    """Test relation schema definitions."""

    def test_all_relations_present(self):
        expected = {"references-gap", "task-outcome", "implements-rule",
                    "completed-in", "decision-affects"}
        assert set(RELATION_SCHEMAS.keys()) == expected

    def test_each_has_roles(self):
        for rel_name, schema in RELATION_SCHEMAS.items():
            assert "roles" in schema, f"{rel_name} missing 'roles'"
            assert len(schema["roles"]) == 2, f"{rel_name} should have 2 roles"

    def test_each_has_required_entities(self):
        for rel_name, schema in RELATION_SCHEMAS.items():
            assert "required_entities" in schema
            assert len(schema["required_entities"]) == 2

    def test_implements_rule(self):
        s = RELATION_SCHEMAS["implements-rule"]
        assert "implementing-task" in s["roles"]
        assert "implemented-rule" in s["roles"]
        assert set(s["required_entities"]) == {"task", "rule"}

    def test_completed_in(self):
        s = RELATION_SCHEMAS["completed-in"]
        assert "completed-task" in s["roles"]
        assert "hosting-session" in s["roles"]

    def test_decision_affects(self):
        s = RELATION_SCHEMAS["decision-affects"]
        assert set(s["required_entities"]) == {"decision", "rule"}

    def test_task_outcome_has_attributes(self):
        s = RELATION_SCHEMAS["task-outcome"]
        assert "attributes" in s
        assert "has-authority" in s["attributes"]
