"""
Robot Framework Library for Data Integrity Validation Tests (P10.7)
Migrated from tests/test_data_integrity.py
"""

from datetime import datetime
from robot.api.deco import keyword


class DataIntegrityLibrary:
    """Library for data integrity validation test keywords."""

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

    # =========================================================================
    # Relation Validation Tests
    # =========================================================================

    @keyword("Valid References Gap Passes")
    def valid_references_gap_passes(self):
        """Valid references-gap relation should pass."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        relation = {
            "id": "ref-gap-001",
            "referencing-task": "P10.7",
            "referenced-gap": "GAP-ARCH-007"
        }

        result = validator.validate_relation("references-gap", relation)
        return {
            "is_valid": result.is_valid,
            "has_task_role": "role_referencing-task" in result.passed,
            "has_gap_role": "role_referenced-gap" in result.passed
        }

    @keyword("Valid Task Outcome Passes")
    def valid_task_outcome_passes(self):
        """Valid task-outcome relation should pass."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        relation = {
            "id": "outcome-001",
            "outcome-decision": "DECISION-003",
            "source-task": "P7.1",
            "has-authority": True
        }

        result = validator.validate_relation("task-outcome", relation)
        return {
            "is_valid": result.is_valid,
            "has_authority_attr": "attribute_has-authority" in result.passed
        }

    @keyword("Missing Role Fails")
    def missing_role_fails(self):
        """Missing role should fail."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        incomplete_relation = {
            "id": "ref-gap-002",
            "referencing-task": "P10.7"
        }

        result = validator.validate_relation("references-gap", incomplete_relation)
        return {
            "not_valid": not result.is_valid,
            "has_gap_failure": any("referenced-gap" in f[0] for f in result.failed)
        }

    @keyword("Unknown Relation Fails")
    def unknown_relation_fails(self):
        """Unknown relation type should fail."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        result = validator.validate_relation("unknown-relation", {"id": "test"})
        return {"not_valid": not result.is_valid}

    # =========================================================================
    # Entity Set Validation Tests
    # =========================================================================

    @keyword("Validate Entity Set")
    def validate_entity_set(self):
        """Should validate set of entities and return summary."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        rules = [
            self._valid_rule(),
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
        return {
            "total_correct": result["total"] == 2,
            "valid_correct": result["valid"] == 2,
            "coverage_100": result["coverage"] == 100
        }

    @keyword("Mixed Validity Set")
    def mixed_validity_set(self):
        """Should correctly count valid and invalid entities."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        rules = [
            self._valid_rule(),
            {"rule-id": "RULE-002"}
        ]

        result = validator.validate_entity_set("rule", rules)
        return {
            "total_correct": result["total"] == 2,
            "valid_correct": result["valid"] == 1,
            "invalid_correct": result["invalid"] == 1,
            "has_failures": len(result["failures"]) == 1
        }

    # =========================================================================
    # Cross-Entity Consistency Tests
    # =========================================================================

    @keyword("Valid Gap Reference")
    def valid_gap_reference(self):
        """Task with valid gap reference should pass."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        tasks = [self._valid_task()]
        gaps = [self._valid_gap()]

        report = validator.validate_cross_entity_consistency(tasks, gaps, [], [])
        return {
            "score_100": report["consistency_score"] == 100,
            "no_orphans": len(report["orphan_gap_references"]) == 0
        }

    @keyword("Orphan Gap Reference")
    def orphan_gap_reference(self):
        """Task referencing non-existent gap should be flagged."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        tasks = [self._valid_task()]
        gaps = []

        report = validator.validate_cross_entity_consistency(tasks, gaps, [], [])
        return {
            "score_below_100": report["consistency_score"] < 100,
            "has_orphan": len(report["orphan_gap_references"]) == 1,
            "correct_gap": report["orphan_gap_references"][0]["gap_reference"] == "GAP-ARCH-007"
        }

    # =========================================================================
    # Integrity Report Tests
    # =========================================================================

    @keyword("Generate Report")
    def generate_report(self):
        """Should generate comprehensive report."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        validator.validate_entity("rule", self._valid_rule())
        validator.validate_entity("task", self._valid_task())

        report = validator.generate_integrity_report()
        return {
            "has_summary": "summary" in report,
            "total_2": report["summary"]["total_validations"] == 2,
            "valid_2": report["summary"]["valid"] == 2,
            "score_100": report["summary"]["integrity_score"] == 100,
            "has_by_type": "by_entity_type" in report,
            "has_rule": "rule" in report["by_entity_type"]
        }

    @keyword("Empty Report")
    def empty_report(self):
        """Should handle no validations."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        report = validator.generate_integrity_report()
        return {"has_error": "error" in report}

    # =========================================================================
    # ValidationResult Tests
    # =========================================================================

    @keyword("Result To Dict")
    def result_to_dict(self):
        """Should serialize to dictionary."""
        try:
            from governance.data_integrity import ValidationResult, ValidationLevel

            result = ValidationResult("rule", "RULE-001", ValidationLevel.SCHEMA)
            result.add_pass("check1")
            result.add_fail("check2", "Failed because...")

            data = result.to_dict()
            return {
                "entity_type": data["entity_type"] == "rule",
                "entity_id": data["entity_id"] == "RULE-001",
                "not_valid": data["is_valid"] is False,
                "has_passed": len(data["passed"]) == 1,
                "has_failed": len(data["failed"]) == 1
            }
        except ImportError:
            return {"skipped": True, "reason": "Import failed"}

    @keyword("Is Valid Property")
    def is_valid_property(self):
        """is_valid should reflect failure state."""
        try:
            from governance.data_integrity import ValidationResult, ValidationLevel

            result = ValidationResult("rule", "RULE-001", ValidationLevel.SCHEMA)
            initial_valid = result.is_valid

            result.add_fail("check", "reason")
            after_fail = result.is_valid

            return {
                "initially_valid": initial_valid is True,
                "not_valid_after_fail": after_fail is False
            }
        except ImportError:
            return {"skipped": True, "reason": "Import failed"}

    # =========================================================================
    # Validator Accumulation Tests
    # =========================================================================

    @keyword("Validator Accumulates Results")
    def validator_accumulates_results(self):
        """Validator should accumulate all results."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        validator.validate_entity("rule", self._valid_rule())
        validator.validate_entity("task", self._valid_task())
        validator.validate_entity("decision", self._valid_decision())

        report = validator.generate_integrity_report()
        return {
            "three_results": len(validator.results) == 3,
            "total_3": report["summary"]["total_validations"] == 3,
            "has_rule": "rule" in report["by_entity_type"],
            "has_task": "task" in report["by_entity_type"],
            "has_decision": "decision" in report["by_entity_type"]
        }

    # =========================================================================
    # ID Pattern Validation Tests
    # =========================================================================

    @keyword("Valid Rule ID Pattern")
    def valid_rule_id_pattern(self):
        """RULE-XXX pattern should pass."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        result = validator.validate_entity("rule", self._valid_rule())
        return {"has_id_pattern": "id_pattern" in result.passed}

    @keyword("Invalid Rule ID Pattern")
    def invalid_rule_id_pattern(self):
        """Non-conforming rule ID should warn."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        rule = {
            "rule-id": "R-1",
            "rule-name": "Test",
            "category": "test",
            "priority": "LOW",
            "status": "DRAFT",
            "directive": "Test"
        }

        result = validator.validate_entity("rule", rule)
        return {"has_id_warning": any("id_pattern" in w[0] for w in result.warnings)}

    @keyword("Valid Task ID Patterns")
    def valid_task_id_patterns(self):
        """Various valid task ID patterns should pass."""
        validator = self._get_validator()
        if not validator:
            return {"skipped": True, "reason": "Import failed"}

        valid_ids = ["P10.7", "RD-001", "ORCH-001", "TEST-001", "FH-001", "TOOL-001", "DOC-001"]
        results = []

        for task_id in valid_ids:
            task = {
                "task-id": task_id,
                "task-name": "Test Task",
                "task-status": "TODO"
            }
            result = validator.validate_entity("task", task)
            results.append(result.is_valid)

        return {"all_valid": all(results)}

    # =========================================================================
    # Validation Level Tests
    # =========================================================================

    @keyword("Schema Level Validation")
    def schema_level_validation(self):
        """Schema level validation."""
        try:
            from governance.data_integrity import ValidationLevel
            validator = self._get_validator()
            if not validator:
                return {"skipped": True, "reason": "Import failed"}

            result = validator.validate_entity("rule", self._valid_rule(), ValidationLevel.SCHEMA)
            return {"correct_level": result.level == ValidationLevel.SCHEMA}
        except ImportError:
            return {"skipped": True, "reason": "Import failed"}

    @keyword("API Level Validation")
    def api_level_validation(self):
        """API level validation."""
        try:
            from governance.data_integrity import ValidationLevel
            validator = self._get_validator()
            if not validator:
                return {"skipped": True, "reason": "Import failed"}

            result = validator.validate_entity("rule", self._valid_rule(), ValidationLevel.API)
            return {"correct_level": result.level == ValidationLevel.API}
        except ImportError:
            return {"skipped": True, "reason": "Import failed"}

    @keyword("UI Level Validation")
    def ui_level_validation(self):
        """UI level validation."""
        try:
            from governance.data_integrity import ValidationLevel
            validator = self._get_validator()
            if not validator:
                return {"skipped": True, "reason": "Import failed"}

            result = validator.validate_entity("rule", self._valid_rule(), ValidationLevel.UI)
            return {"correct_level": result.level == ValidationLevel.UI}
        except ImportError:
            return {"skipped": True, "reason": "Import failed"}

    @keyword("Report Groups By Level")
    def report_groups_by_level(self):
        """Report should group by validation level."""
        try:
            from governance.data_integrity import ValidationLevel
            validator = self._get_validator()
            if not validator:
                return {"skipped": True, "reason": "Import failed"}

            validator.validate_entity("rule", self._valid_rule(), ValidationLevel.SCHEMA)
            validator.validate_entity("rule", self._valid_rule(), ValidationLevel.API)

            report = validator.generate_integrity_report()
            return {
                "has_by_level": "by_level" in report,
                "has_schema": "schema" in report["by_level"],
                "has_api": "api" in report["by_level"]
            }
        except ImportError:
            return {"skipped": True, "reason": "Import failed"}
