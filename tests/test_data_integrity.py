"""
Tests for Data Integrity Validation Module (P10.7 Edge-to-Edge)

Tests validate:
1. Entity schema compliance
2. Relation schema compliance (typed references)
3. Cross-entity consistency
4. Edge-to-edge validation chain
"""

import pytest
from datetime import datetime

from governance.data_integrity import (
    DataIntegrityValidator,
    ValidationResult,
    ValidationLevel,
    validate_edge_to_edge
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def validator():
    """Fresh validator instance."""
    return DataIntegrityValidator()


@pytest.fixture
def valid_rule():
    """Valid rule entity data."""
    return {
        "rule-id": "RULE-001",
        "rule-name": "Session Evidence Logging",
        "category": "governance",
        "priority": "CRITICAL",
        "status": "ACTIVE",
        "directive": "All sessions must log evidence"
    }


@pytest.fixture
def valid_task():
    """Valid task entity data."""
    return {
        "task-id": "P10.7",
        "task-name": "Entity Hierarchy Review",
        "task-status": "TODO",
        "task-body": "Review entity relationships",
        "phase": "P10",
        "gap-reference": "GAP-ARCH-007"
    }


@pytest.fixture
def valid_decision():
    """Valid decision entity data."""
    return {
        "decision-id": "DECISION-003",
        "decision-name": "TypeDB-First Strategy",
        "context": "Need unified data layer",
        "rationale": "TypeDB provides inference + types",
        "decision-status": "APPROVED"
    }


@pytest.fixture
def valid_gap():
    """Valid gap entity data."""
    return {
        "gap-id": "GAP-ARCH-007",
        "gap-name": "Entity hierarchy undefined",
        "gap-status": "RESOLVED",
        "severity": "HIGH",
        "location": "schema.tql:48-60"
    }


@pytest.fixture
def valid_agent():
    """Valid agent entity data."""
    return {
        "agent-id": "AGENT-001",
        "agent-name": "Claude Code R&D",
        "agent-type": "claude-code",
        "trust-score": 0.95
    }


@pytest.fixture
def valid_session():
    """Valid session entity data."""
    return {
        "session-id": "SESSION-2024-12-27-001",
        "session-name": "P10.7 Implementation",
        "started-at": datetime.now().isoformat()
    }


# =============================================================================
# Entity Validation Tests
# =============================================================================

class TestEntityValidation:
    """Tests for individual entity validation."""

    def test_valid_rule_passes(self, validator, valid_rule):
        """Valid rule should pass all checks."""
        result = validator.validate_entity("rule", valid_rule)

        assert result.is_valid
        assert len(result.failed) == 0
        assert "required_field_rule-id" in result.passed
        assert "required_field_directive" in result.passed

    def test_missing_required_field_fails(self, validator):
        """Missing required field should fail."""
        incomplete_rule = {
            "rule-id": "RULE-001",
            "rule-name": "Test Rule"
            # Missing: category, priority, status, directive
        }

        result = validator.validate_entity("rule", incomplete_rule)

        assert not result.is_valid
        assert any("category" in f[0] for f in result.failed)
        assert any("priority" in f[0] for f in result.failed)

    def test_valid_task_passes(self, validator, valid_task):
        """Valid task should pass all checks."""
        result = validator.validate_entity("task", valid_task)

        assert result.is_valid
        assert "required_field_task-id" in result.passed

    def test_valid_decision_passes(self, validator, valid_decision):
        """Valid decision should pass all checks."""
        result = validator.validate_entity("decision", valid_decision)

        assert result.is_valid
        assert "required_field_context" in result.passed
        assert "required_field_rationale" in result.passed

    def test_valid_gap_passes(self, validator, valid_gap):
        """Valid gap should pass all checks."""
        result = validator.validate_entity("gap", valid_gap)

        assert result.is_valid
        assert "required_field_severity" in result.passed

    def test_valid_agent_passes(self, validator, valid_agent):
        """Valid agent should pass all checks."""
        result = validator.validate_entity("agent", valid_agent)

        assert result.is_valid
        assert "required_field_agent-type" in result.passed

    def test_valid_session_passes(self, validator, valid_session):
        """Valid session should pass all checks."""
        result = validator.validate_entity("session", valid_session)

        assert result.is_valid

    def test_unknown_entity_type_fails(self, validator):
        """Unknown entity type should fail."""
        result = validator.validate_entity("unknown_type", {"id": "test"})

        assert not result.is_valid
        assert any("Unknown entity type" in f[1] for f in result.failed)

    def test_alternative_field_naming(self, validator):
        """Should handle snake_case field names."""
        rule_snake_case = {
            "rule_id": "RULE-001",
            "rule_name": "Test Rule",
            "category": "governance",
            "priority": "HIGH",
            "status": "ACTIVE",
            "directive": "Test directive"
        }

        result = validator.validate_entity("rule", rule_snake_case)

        assert result.is_valid

    def test_invalid_enum_value_warns(self, validator):
        """Invalid enum value should generate warning."""
        rule_invalid_priority = {
            "rule-id": "RULE-001",
            "rule-name": "Test Rule",
            "category": "governance",
            "priority": "INVALID_PRIORITY",
            "status": "ACTIVE",
            "directive": "Test directive"
        }

        result = validator.validate_entity("rule", rule_invalid_priority)

        # Still valid but with warning
        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("priority" in w[0] for w in result.warnings)


# =============================================================================
# Relation Validation Tests (P10.7 Typed References)
# =============================================================================

class TestRelationValidation:
    """Tests for P10.7 typed reference validation."""

    def test_valid_references_gap_passes(self, validator):
        """Valid references-gap relation should pass."""
        relation = {
            "id": "ref-gap-001",
            "referencing-task": "P10.7",
            "referenced-gap": "GAP-ARCH-007"
        }

        result = validator.validate_relation("references-gap", relation)

        assert result.is_valid
        assert "role_referencing-task" in result.passed
        assert "role_referenced-gap" in result.passed

    def test_valid_task_outcome_passes(self, validator):
        """Valid task-outcome relation should pass."""
        relation = {
            "id": "outcome-001",
            "outcome-decision": "DECISION-003",
            "source-task": "P7.1",
            "has-authority": True
        }

        result = validator.validate_relation("task-outcome", relation)

        assert result.is_valid
        assert "attribute_has-authority" in result.passed

    def test_missing_role_fails(self, validator):
        """Missing role should fail."""
        incomplete_relation = {
            "id": "ref-gap-002",
            "referencing-task": "P10.7"
            # Missing: referenced-gap
        }

        result = validator.validate_relation("references-gap", incomplete_relation)

        assert not result.is_valid
        assert any("referenced-gap" in f[0] for f in result.failed)

    def test_unknown_relation_fails(self, validator):
        """Unknown relation type should fail."""
        result = validator.validate_relation("unknown-relation", {"id": "test"})

        assert not result.is_valid


# =============================================================================
# Entity Set Validation Tests
# =============================================================================

class TestEntitySetValidation:
    """Tests for validating sets of entities."""

    def test_validate_entity_set(self, validator, valid_rule):
        """Should validate set of entities and return summary."""
        rules = [
            valid_rule,
            {
                "rule-id": "RULE-002",
                "rule-name": "Another Rule",
                "category": "technical",
                "priority": "HIGH",
                "status": "ACTIVE",
                "directive": "Test"
            }
        ]

        result = validator.validate_entity_set("rule", rules)

        assert result["total"] == 2
        assert result["valid"] == 2
        assert result["coverage"] == 100

    def test_mixed_validity_set(self, validator, valid_rule):
        """Should correctly count valid and invalid entities."""
        rules = [
            valid_rule,
            {
                "rule-id": "RULE-002"
                # Missing required fields
            }
        ]

        result = validator.validate_entity_set("rule", rules)

        assert result["total"] == 2
        assert result["valid"] == 1
        assert result["invalid"] == 1
        assert len(result["failures"]) == 1


# =============================================================================
# Cross-Entity Consistency Tests
# =============================================================================

class TestCrossEntityConsistency:
    """Tests for cross-entity reference consistency."""

    def test_valid_gap_reference(self, validator, valid_task, valid_gap):
        """Task with valid gap reference should pass."""
        tasks = [valid_task]
        gaps = [valid_gap]
        rules = []
        decisions = []

        report = validator.validate_cross_entity_consistency(
            tasks, gaps, rules, decisions
        )

        assert report["consistency_score"] == 100
        assert len(report["orphan_gap_references"]) == 0

    def test_orphan_gap_reference(self, validator, valid_task):
        """Task referencing non-existent gap should be flagged."""
        tasks = [valid_task]
        gaps = []  # No gaps
        rules = []
        decisions = []

        report = validator.validate_cross_entity_consistency(
            tasks, gaps, rules, decisions
        )

        assert report["consistency_score"] < 100
        assert len(report["orphan_gap_references"]) == 1
        assert report["orphan_gap_references"][0]["gap_reference"] == "GAP-ARCH-007"


# =============================================================================
# Integrity Report Tests
# =============================================================================

class TestIntegrityReport:
    """Tests for integrity report generation."""

    def test_generate_report(self, validator, valid_rule, valid_task):
        """Should generate comprehensive report."""
        validator.validate_entity("rule", valid_rule)
        validator.validate_entity("task", valid_task)

        report = validator.generate_integrity_report()

        assert "summary" in report
        assert report["summary"]["total_validations"] == 2
        assert report["summary"]["valid"] == 2
        assert report["summary"]["integrity_score"] == 100
        assert "by_entity_type" in report
        assert "rule" in report["by_entity_type"]

    def test_empty_report(self, validator):
        """Should handle no validations."""
        report = validator.generate_integrity_report()

        assert "error" in report


# =============================================================================
# ValidationResult Tests
# =============================================================================

class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_result_to_dict(self):
        """Should serialize to dictionary."""
        result = ValidationResult("rule", "RULE-001", ValidationLevel.SCHEMA)
        result.add_pass("check1")
        result.add_fail("check2", "Failed because...")

        data = result.to_dict()

        assert data["entity_type"] == "rule"
        assert data["entity_id"] == "RULE-001"
        assert data["is_valid"] is False
        assert len(data["passed"]) == 1
        assert len(data["failed"]) == 1

    def test_is_valid_property(self):
        """is_valid should reflect failure state."""
        result = ValidationResult("rule", "RULE-001", ValidationLevel.SCHEMA)

        assert result.is_valid is True

        result.add_fail("check", "reason")

        assert result.is_valid is False


# =============================================================================
# Edge-to-Edge Integration Tests
# =============================================================================

class TestEdgeToEdgeValidation:
    """Integration tests for full edge-to-edge validation."""

    @pytest.mark.integration
    def test_validate_edge_to_edge(self):
        """
        Full edge-to-edge validation requires API running.
        Mark as integration test.
        """
        # This test requires the API to be running
        # Skip in unit test mode
        pytest.skip("Integration test - requires API server")

    def test_validator_accumulates_results(self, validator, valid_rule, valid_task, valid_decision):
        """Validator should accumulate all results."""
        validator.validate_entity("rule", valid_rule)
        validator.validate_entity("task", valid_task)
        validator.validate_entity("decision", valid_decision)

        assert len(validator.results) == 3

        report = validator.generate_integrity_report()

        assert report["summary"]["total_validations"] == 3
        assert "rule" in report["by_entity_type"]
        assert "task" in report["by_entity_type"]
        assert "decision" in report["by_entity_type"]


# =============================================================================
# ID Pattern Validation Tests
# =============================================================================

class TestIdPatternValidation:
    """Tests for entity ID pattern validation."""

    def test_valid_rule_id_pattern(self, validator, valid_rule):
        """RULE-XXX pattern should pass."""
        result = validator.validate_entity("rule", valid_rule)

        assert "id_pattern" in result.passed

    def test_invalid_rule_id_pattern(self, validator):
        """Non-conforming rule ID should warn."""
        rule = {
            "rule-id": "R-1",  # Wrong pattern
            "rule-name": "Test",
            "category": "test",
            "priority": "LOW",
            "status": "DRAFT",
            "directive": "Test"
        }

        result = validator.validate_entity("rule", rule)

        assert any("id_pattern" in w[0] for w in result.warnings)

    def test_valid_task_id_patterns(self, validator):
        """Various valid task ID patterns should pass."""
        valid_ids = ["P10.7", "RD-001", "ORCH-001", "TEST-001", "FH-001", "TOOL-001", "DOC-001"]

        for task_id in valid_ids:
            task = {
                "task-id": task_id,
                "task-name": "Test Task",
                "task-status": "TODO"
            }

            result = validator.validate_entity("task", task)

            assert result.is_valid, f"Task ID {task_id} should be valid"


# =============================================================================
# Validation Level Tests
# =============================================================================

class TestValidationLevels:
    """Tests for different validation levels."""

    def test_schema_level(self, validator, valid_rule):
        """Schema level validation."""
        result = validator.validate_entity("rule", valid_rule, ValidationLevel.SCHEMA)

        assert result.level == ValidationLevel.SCHEMA

    def test_api_level(self, validator, valid_rule):
        """API level validation."""
        result = validator.validate_entity("rule", valid_rule, ValidationLevel.API)

        assert result.level == ValidationLevel.API

    def test_ui_level(self, validator, valid_rule):
        """UI level validation."""
        result = validator.validate_entity("rule", valid_rule, ValidationLevel.UI)

        assert result.level == ValidationLevel.UI

    def test_report_groups_by_level(self, validator, valid_rule):
        """Report should group by validation level."""
        validator.validate_entity("rule", valid_rule, ValidationLevel.SCHEMA)
        validator.validate_entity("rule", valid_rule, ValidationLevel.API)

        report = validator.generate_integrity_report()

        assert "by_level" in report
        assert "schema" in report["by_level"]
        assert "api" in report["by_level"]
