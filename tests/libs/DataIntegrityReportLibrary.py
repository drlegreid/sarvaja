"""
Robot Framework Library for Data Integrity - Report & Pattern Tests.

Per P10.7: Data Integrity Validation.
Split from DataIntegrityLibrary.py per DOC-SIZE-01-v1.

Covers: Integrity reports, ValidationResult, ID patterns, validation levels.
"""

from datetime import datetime
from robot.api.deco import keyword


class DataIntegrityReportLibrary:
    """Library for integrity report and pattern test keywords."""

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
