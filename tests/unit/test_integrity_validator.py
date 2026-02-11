"""
Unit tests for Data Integrity Validator.

Per P10.7: Tests for DataIntegrityValidator, ValidationResult,
helpers, and schemas.
"""

import pytest

from governance.integrity.models import ValidationLevel, ValidationResult
from governance.integrity.helpers import get_entity_id, get_field_value, camel_case
from governance.integrity.schemas import ENTITY_SCHEMAS, VALID_VALUES, RELATION_SCHEMAS
from governance.integrity.validator import DataIntegrityValidator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class TestCamelCase:
    """Tests for camel_case helper."""

    def test_kebab_to_camel(self):
        assert camel_case("rule-id") == "ruleId"

    def test_multi_part(self):
        assert camel_case("gap-reference-id") == "gapReferenceId"

    def test_no_hyphens(self):
        assert camel_case("name") == "name"


class TestGetEntityId:
    """Tests for get_entity_id helper."""

    def test_kebab_case(self):
        assert get_entity_id("rule", {"rule-id": "RULE-001"}) == "RULE-001"

    def test_snake_case(self):
        assert get_entity_id("rule", {"rule_id": "RULE-001"}) == "RULE-001"

    def test_camel_case(self):
        assert get_entity_id("rule", {"ruleId": "RULE-001"}) == "RULE-001"

    def test_bare_id(self):
        assert get_entity_id("rule", {"id": "RULE-001"}) == "RULE-001"

    def test_unknown(self):
        assert get_entity_id("rule", {"other": "val"}) == "unknown"


class TestGetFieldValue:
    """Tests for get_field_value helper."""

    def test_exact_match(self):
        assert get_field_value({"rule-id": "R-1"}, "rule-id") == "R-1"

    def test_snake_case(self):
        assert get_field_value({"rule_id": "R-1"}, "rule-id") == "R-1"

    def test_camel_case(self):
        assert get_field_value({"ruleId": "R-1"}, "rule-id") == "R-1"

    def test_no_hyphens(self):
        assert get_field_value({"ruleid": "R-1"}, "rule-id") == "R-1"

    def test_not_found(self):
        assert get_field_value({"other": "val"}, "rule-id") is None


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------
class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_initial_state(self):
        vr = ValidationResult("rule", "R-1", ValidationLevel.SCHEMA)
        assert vr.is_valid is True
        assert vr.passed == []
        assert vr.failed == []
        assert vr.warnings == []

    def test_add_pass(self):
        vr = ValidationResult("rule", "R-1", ValidationLevel.SCHEMA)
        vr.add_pass("check_1")
        assert "check_1" in vr.passed
        assert vr.is_valid is True

    def test_add_fail(self):
        vr = ValidationResult("rule", "R-1", ValidationLevel.SCHEMA)
        vr.add_fail("check_1", "missing field")
        assert vr.is_valid is False
        assert vr.failed == [("check_1", "missing field")]

    def test_add_warning(self):
        vr = ValidationResult("rule", "R-1", ValidationLevel.SCHEMA)
        vr.add_warning("check_1", "not ideal")
        assert vr.is_valid is True  # warnings don't fail
        assert vr.warnings == [("check_1", "not ideal")]

    def test_to_dict(self):
        vr = ValidationResult("rule", "R-1", ValidationLevel.SCHEMA)
        vr.add_pass("ok")
        vr.add_fail("bad", "reason")
        d = vr.to_dict()
        assert d["entity_type"] == "rule"
        assert d["entity_id"] == "R-1"
        assert d["level"] == "schema"
        assert d["is_valid"] is False
        assert len(d["passed"]) == 1
        assert len(d["failed"]) == 1


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class TestSchemas:
    """Tests for schema definitions."""

    def test_all_entity_types(self):
        for etype in ["rule", "decision", "task", "gap", "agent", "session"]:
            assert etype in ENTITY_SCHEMAS

    def test_rule_required_fields(self):
        assert "rule-id" in ENTITY_SCHEMAS["rule"]["required"]
        assert "rule-name" in ENTITY_SCHEMAS["rule"]["required"]

    def test_valid_values_priority(self):
        assert "CRITICAL" in VALID_VALUES["priority"]
        assert "HIGH" in VALID_VALUES["priority"]

    def test_relation_schemas(self):
        for rtype in ["references-gap", "task-outcome", "implements-rule",
                       "completed-in", "decision-affects"]:
            assert rtype in RELATION_SCHEMAS
            assert "roles" in RELATION_SCHEMAS[rtype]


# ---------------------------------------------------------------------------
# DataIntegrityValidator
# ---------------------------------------------------------------------------
class TestDataIntegrityValidator:
    """Tests for DataIntegrityValidator class."""

    def test_validate_valid_rule(self):
        v = DataIntegrityValidator()
        result = v.validate_entity("rule", {
            "rule-id": "RULE-001",
            "rule-name": "Test Rule",
            "category": "governance",
            "priority": "HIGH",
            "status": "ACTIVE",
            "directive": "Do something",
        })
        assert result.is_valid is True
        assert len(v.results) == 1

    def test_validate_missing_required(self):
        v = DataIntegrityValidator()
        result = v.validate_entity("rule", {
            "rule-id": "RULE-001",
            # missing rule-name, category, priority, status, directive
        })
        assert result.is_valid is False
        assert len(result.failed) >= 4

    def test_validate_unknown_entity_type(self):
        v = DataIntegrityValidator()
        result = v.validate_entity("unknown_type", {"id": "1"})
        assert result.is_valid is False
        assert any("Unknown entity type" in r for _, r in result.failed)

    def test_validate_invalid_id_pattern(self):
        v = DataIntegrityValidator()
        result = v.validate_entity("rule", {
            "rule-id": "BAD-ID-FORMAT",
            "rule-name": "Test", "category": "x",
            "priority": "HIGH", "status": "ACTIVE", "directive": "x",
        })
        # Should have warning about ID pattern
        assert any("id_pattern" in c for c, _ in result.warnings)

    def test_validate_valid_id_pattern(self):
        v = DataIntegrityValidator()
        result = v.validate_entity("rule", {
            "rule-id": "RULE-001",
            "rule-name": "Test", "category": "x",
            "priority": "HIGH", "status": "ACTIVE", "directive": "x",
        })
        assert "id_pattern" in result.passed

    def test_validate_enum_values(self):
        v = DataIntegrityValidator()
        result = v.validate_entity("rule", {
            "rule-id": "RULE-001", "rule-name": "Test",
            "category": "x", "priority": "INVALID_PRIORITY",
            "status": "ACTIVE", "directive": "x",
        })
        # Should warn about invalid priority value
        assert any("valid_value_priority" in c for c, _ in result.warnings)

    def test_validate_snake_case_fields(self):
        v = DataIntegrityValidator()
        result = v.validate_entity("rule", {
            "rule_id": "RULE-001",
            "rule_name": "Test", "category": "x",
            "priority": "HIGH", "status": "ACTIVE", "directive": "x",
        })
        assert result.is_valid is True

    def test_validate_session(self):
        v = DataIntegrityValidator()
        result = v.validate_entity("session", {
            "session-id": "SESSION-2026-02-11-TEST",
        })
        assert result.is_valid is True

    # -- Relations --
    def test_validate_valid_relation(self):
        v = DataIntegrityValidator()
        result = v.validate_relation("references-gap", {
            "referencing-task": "T-1",
            "referenced-gap": "GAP-1",
        })
        assert result.is_valid is True

    def test_validate_relation_missing_role(self):
        v = DataIntegrityValidator()
        result = v.validate_relation("references-gap", {
            "referencing-task": "T-1",
            # missing referenced-gap
        })
        assert result.is_valid is False

    def test_validate_unknown_relation(self):
        v = DataIntegrityValidator()
        result = v.validate_relation("nonexistent", {})
        assert result.is_valid is False

    def test_validate_relation_optional_attributes(self):
        v = DataIntegrityValidator()
        result = v.validate_relation("task-outcome", {
            "outcome-decision": "D-1",
            "source-task": "T-1",
            # missing has-authority (optional)
        })
        assert result.is_valid is True
        assert any("has-authority" in c for c, _ in result.warnings)

    # -- Entity set --
    def test_validate_entity_set(self):
        v = DataIntegrityValidator()
        entities = [
            {"rule-id": "RULE-001", "rule-name": "R1", "category": "x",
             "priority": "HIGH", "status": "ACTIVE", "directive": "d"},
            {"rule-id": "RULE-002"},  # incomplete
        ]
        summary = v.validate_entity_set("rule", entities)
        assert summary["total"] == 2
        assert summary["valid"] == 1
        assert summary["invalid"] == 1
        assert summary["coverage"] == 50.0

    def test_validate_entity_set_empty(self):
        v = DataIntegrityValidator()
        summary = v.validate_entity_set("rule", [])
        assert summary["total"] == 0
        assert summary["coverage"] == 0

    # -- Cross-entity consistency --
    def test_cross_entity_valid_refs(self):
        v = DataIntegrityValidator()
        tasks = [{"task-id": "T-1", "gap-reference": "GAP-1"}]
        gaps = [{"gap-id": "GAP-1"}]
        report = v.validate_cross_entity_consistency(tasks, gaps, [], [])
        assert report["valid_references"] == 1
        assert report["orphan_gap_references"] == []
        assert report["consistency_score"] == 100

    def test_cross_entity_orphan_gap_ref(self):
        v = DataIntegrityValidator()
        tasks = [{"task-id": "T-1", "gap-reference": "GAP-MISSING"}]
        gaps = [{"gap-id": "GAP-1"}]
        report = v.validate_cross_entity_consistency(tasks, gaps, [], [])
        assert len(report["orphan_gap_references"]) == 1
        assert report["consistency_score"] == 0

    def test_cross_entity_no_refs(self):
        v = DataIntegrityValidator()
        report = v.validate_cross_entity_consistency([], [], [], [])
        assert report["consistency_score"] == 100

    # -- Integrity report --
    def test_generate_report_empty(self):
        v = DataIntegrityValidator()
        report = v.generate_integrity_report()
        assert "error" in report

    def test_generate_report_with_data(self):
        v = DataIntegrityValidator()
        v.validate_entity("rule", {
            "rule-id": "RULE-001", "rule-name": "R1", "category": "x",
            "priority": "HIGH", "status": "ACTIVE", "directive": "d",
        })
        v.validate_entity("rule", {"rule-id": "RULE-002"})
        report = v.generate_integrity_report()
        assert report["summary"]["total_validations"] == 2
        assert report["summary"]["valid"] == 1
        assert report["summary"]["invalid"] == 1
        assert "rule" in report["by_entity_type"]
        assert "schema" in report["by_level"]
