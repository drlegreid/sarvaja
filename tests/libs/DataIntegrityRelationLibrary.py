"""
Robot Framework Library for Data Integrity - Relation Validation Tests.

Per P10.7: Data Integrity Validation.
Split from DataIntegrityLibrary.py per DOC-SIZE-01-v1.

Covers: Relation validation, entity set validation, cross-entity consistency.
"""

from datetime import datetime
from robot.api.deco import keyword


class DataIntegrityRelationLibrary:
    """Library for relation validation test keywords."""

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

    def _valid_gap(self):
        """Valid gap entity data."""
        return {
            "gap-id": "GAP-ARCH-007",
            "gap-name": "Entity hierarchy undefined",
            "gap-status": "RESOLVED",
            "severity": "HIGH",
            "location": "schema.tql:48-60"
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
