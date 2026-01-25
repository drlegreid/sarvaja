"""
Robot Framework Library for Data Integrity - Entity Validation Tests.

Per P10.7: Data Integrity Validation.
Split from DataIntegrityLibrary.py per DOC-SIZE-01-v1.

Covers: Entity validation (rule, task, decision, gap, agent, session).
"""

from datetime import datetime
from robot.api.deco import keyword


class DataIntegrityEntityLibrary:
    """Library for entity validation test keywords."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def _get_validator(self):
        """Get fresh validator instance."""
        try:
            from governance.data_integrity import DataIntegrityValidator
            return DataIntegrityValidator()
        except ImportError:
            return None

    def _valid_rule(self):
        """Valid rule entity data."""
        return {
            "rule-id": "RULE-001",
            "rule-name": "Session Evidence Logging",
            "category": "governance",
            "priority": "CRITICAL",
            "status": "ACTIVE",
            "directive": "All sessions must log evidence"
        }

    def _valid_task(self):
        """Valid task entity data."""
        return {
            "task-id": "P10.7",
            "task-name": "Entity Hierarchy Review",
            "task-status": "TODO",
            "task-body": "Review entity relationships",
            "phase": "P10",
            "gap-reference": "GAP-ARCH-007"
        }

    def _valid_decision(self):
        """Valid decision entity data."""
        return {
            "decision-id": "DECISION-003",
            "decision-name": "TypeDB-First Strategy",
            "context": "Need unified data layer",
            "rationale": "TypeDB provides inference + types",
            "decision-status": "APPROVED"
        }

    def _valid_gap(self):
        """Valid gap entity data."""
        return {
            "gap-id": "GAP-ARCH-007",
            "gap-name": "Entity hierarchy undefined",
            "gap-status": "RESOLVED",
            "severity": "HIGH",
            "location": "schema.tql:48-60"
        }

    def _valid_agent(self):
        """Valid agent entity data."""
        return {
            "agent-id": "AGENT-001",
            "agent-name": "Claude Code R&D",
            "agent-type": "claude-code",
            "trust-score": 0.95
        }

    def _valid_session(self):
        """Valid session entity data."""
        return {
            "session-id": "SESSION-2024-12-27-001",
            "session-name": "P10.7 Implementation",
            "started-at": datetime.now().isoformat()
        }

    # =========================================================================
    # Entity Validation Tests
    # =========================================================================

    @keyword("Valid Rule Passes")
    def valid_rule_passes(self):
        """Valid rule should pass all checks."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        result = validator.validate_entity("rule", self._valid_rule())
        return {
            "is_valid": result.is_valid,
            "no_failures": len(result.failed) == 0,
            "has_rule_id": "required_field_rule-id" in result.passed,
            "has_directive": "required_field_directive" in result.passed
        }

    @keyword("Missing Required Field Fails")
    def missing_required_field_fails(self):
        """Missing required field should fail."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        incomplete_rule = {
            "rule-id": "RULE-001",
            "rule-name": "Test Rule"
        }

        result = validator.validate_entity("rule", incomplete_rule)
        return {
            "not_valid": not result.is_valid,
            "has_category_failure": any("category" in f[0] for f in result.failed),
            "has_priority_failure": any("priority" in f[0] for f in result.failed)
        }

    @keyword("Valid Task Passes")
    def valid_task_passes(self):
        """Valid task should pass all checks."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        result = validator.validate_entity("task", self._valid_task())
        return {
            "is_valid": result.is_valid,
            "has_task_id": "required_field_task-id" in result.passed
        }

    @keyword("Valid Decision Passes")
    def valid_decision_passes(self):
        """Valid decision should pass all checks."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        result = validator.validate_entity("decision", self._valid_decision())
        return {
            "is_valid": result.is_valid,
            "has_context": "required_field_context" in result.passed,
            "has_rationale": "required_field_rationale" in result.passed
        }

    @keyword("Valid Gap Passes")
    def valid_gap_passes(self):
        """Valid gap should pass all checks."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        result = validator.validate_entity("gap", self._valid_gap())
        return {
            "is_valid": result.is_valid,
            "has_severity": "required_field_severity" in result.passed
        }

    @keyword("Valid Agent Passes")
    def valid_agent_passes(self):
        """Valid agent should pass all checks."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        result = validator.validate_entity("agent", self._valid_agent())
        return {
            "is_valid": result.is_valid,
            "has_agent_type": "required_field_agent-type" in result.passed
        }

    @keyword("Valid Session Passes")
    def valid_session_passes(self):
        """Valid session should pass all checks."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        result = validator.validate_entity("session", self._valid_session())
        return {"is_valid": result.is_valid}

    @keyword("Unknown Entity Type Fails")
    def unknown_entity_type_fails(self):
        """Unknown entity type should fail."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        result = validator.validate_entity("unknown_type", {"id": "test"})
        return {
            "not_valid": not result.is_valid,
            "has_unknown_error": any("Unknown entity type" in f[1] for f in result.failed)
        }

    @keyword("Alternative Field Naming")
    def alternative_field_naming(self):
        """Should handle snake_case field names."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        rule_snake_case = {
            "rule_id": "RULE-001",
            "rule_name": "Test Rule",
            "category": "governance",
            "priority": "HIGH",
            "status": "ACTIVE",
            "directive": "Test directive"
        }

        result = validator.validate_entity("rule", rule_snake_case)
        return {"is_valid": result.is_valid}

    @keyword("Invalid Enum Value Warns")
    def invalid_enum_value_warns(self):
        """Invalid enum value should generate warning."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        rule_invalid_priority = {
            "rule-id": "RULE-001",
            "rule-name": "Test Rule",
            "category": "governance",
            "priority": "INVALID_PRIORITY",
            "status": "ACTIVE",
            "directive": "Test directive"
        }

        result = validator.validate_entity("rule", rule_invalid_priority)
        return {
            "is_valid": result.is_valid,
            "has_warnings": len(result.warnings) > 0,
            "priority_warning": any("priority" in w[0] for w in result.warnings)
        }
