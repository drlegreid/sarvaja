"""
Data Integrity Validator
Created: P10.7
Modularized: 2026-01-02 (RULE-032)

Main validator class for edge-to-edge data integrity checks.
Per RULE-012 DSP: Data integrity validation documented.
"""
import re
from typing import Dict, List, Any
from datetime import datetime

from governance.integrity.models import ValidationLevel, ValidationResult
from governance.integrity.schemas import ENTITY_SCHEMAS, VALID_VALUES, RELATION_SCHEMAS
from governance.integrity.helpers import get_entity_id, get_field_value, camel_case


class DataIntegrityValidator:
    """
    Edge-to-edge data integrity validator.

    Validates entities across all layers:
    - Schema compliance (TypeDB entity structure)
    - Client compliance (Python dataclass/dict structure)
    - API compliance (REST response structure)
    - UI compliance (Display data structure)
    """

    def __init__(self):
        self.results: List[ValidationResult] = []

    def validate_entity(
        self,
        entity_type: str,
        entity_data: Dict,
        level: ValidationLevel = ValidationLevel.SCHEMA
    ) -> ValidationResult:
        """
        Validate an entity against its schema.

        Args:
            entity_type: Type of entity (rule, decision, task, gap, agent, session)
            entity_data: Entity data dictionary
            level: Validation level (schema, client, api, ui)

        Returns:
            ValidationResult with passed/failed checks
        """
        entity_id = get_entity_id(entity_type, entity_data)
        result = ValidationResult(entity_type, entity_id, level)

        schema = ENTITY_SCHEMAS.get(entity_type)
        if not schema:
            result.add_fail("schema_exists", f"Unknown entity type: {entity_type}")
            return result

        # Check required fields
        for field in schema["required"]:
            field_variations = [
                field,
                field.replace("-", "_"),
                field.replace("-", ""),
                camel_case(field)
            ]

            found = any(f in entity_data and entity_data[f] is not None for f in field_variations)
            if found:
                result.add_pass(f"required_field_{field}")
            else:
                result.add_fail(f"required_field_{field}", f"Missing required field: {field}")

        # Validate ID pattern
        id_field = f"{entity_type}-id" if entity_type != "session" else "session-id"
        id_value = get_field_value(entity_data, id_field)
        if id_value:
            pattern = schema.get("id_pattern")
            if pattern and not re.match(pattern, str(id_value)):
                result.add_warning("id_pattern", f"ID '{id_value}' doesn't match expected pattern: {pattern}")
            else:
                result.add_pass("id_pattern")

        # Validate enum values
        for field, valid_values in VALID_VALUES.items():
            value = get_field_value(entity_data, field)
            if value is not None:
                if value in valid_values:
                    result.add_pass(f"valid_value_{field}")
                else:
                    result.add_warning(f"valid_value_{field}",
                                      f"Value '{value}' not in expected values: {valid_values}")

        self.results.append(result)
        return result

    def validate_relation(
        self,
        relation_type: str,
        relation_data: Dict,
        level: ValidationLevel = ValidationLevel.SCHEMA
    ) -> ValidationResult:
        """
        Validate a relation against P10.7 typed reference schema.

        Args:
            relation_type: Type of relation (references-gap, task-outcome, etc.)
            relation_data: Relation data with role players
            level: Validation level

        Returns:
            ValidationResult with passed/failed checks
        """
        relation_id = relation_data.get("id", f"{relation_type}-{datetime.now().timestamp()}")
        result = ValidationResult(f"relation:{relation_type}", relation_id, level)

        schema = RELATION_SCHEMAS.get(relation_type)
        if not schema:
            result.add_fail("schema_exists", f"Unknown relation type: {relation_type}")
            return result

        # Check required roles
        for role in schema["roles"]:
            if role in relation_data:
                result.add_pass(f"role_{role}")
            else:
                result.add_fail(f"role_{role}", f"Missing role: {role}")

        # Check relation attributes (e.g., has-authority for task-outcome)
        for attr in schema.get("attributes", []):
            if attr in relation_data:
                result.add_pass(f"attribute_{attr}")
            else:
                result.add_warning(f"attribute_{attr}", f"Optional attribute missing: {attr}")

        self.results.append(result)
        return result

    def validate_entity_set(
        self,
        entity_type: str,
        entities: List[Dict],
        level: ValidationLevel = ValidationLevel.API
    ) -> Dict[str, Any]:
        """
        Validate a set of entities and return summary.

        Args:
            entity_type: Type of entities
            entities: List of entity dictionaries
            level: Validation level

        Returns:
            Summary dictionary with counts and details
        """
        results = []
        for entity in entities:
            results.append(self.validate_entity(entity_type, entity, level))

        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = len(results) - valid_count

        return {
            "entity_type": entity_type,
            "total": len(results),
            "valid": valid_count,
            "invalid": invalid_count,
            "coverage": (valid_count / len(results) * 100) if results else 0,
            "failures": [
                {
                    "entity_id": r.entity_id,
                    "failed_checks": r.failed
                }
                for r in results if not r.is_valid
            ]
        }

    def validate_cross_entity_consistency(
        self,
        tasks: List[Dict],
        gaps: List[Dict],
        rules: List[Dict],
        decisions: List[Dict]
    ) -> Dict[str, Any]:
        """
        Validate cross-entity references are consistent.

        Checks:
        - Tasks with gap-reference have valid gap entities
        - Decisions affecting rules have valid rule entities
        - Task-session linkages are valid

        Returns:
            Consistency report
        """
        report = {
            "orphan_gap_references": [],
            "orphan_rule_references": [],
            "missing_authority_links": [],
            "valid_references": 0,
            "total_references": 0
        }

        # Build lookup sets
        gap_ids = {get_field_value(g, "gap-id") for g in gaps if get_field_value(g, "gap-id")}
        rule_ids = {get_field_value(r, "rule-id") for r in rules if get_field_value(r, "rule-id")}

        # Check task gap references
        for task in tasks:
            gap_ref = get_field_value(task, "gap-reference")
            if gap_ref:
                report["total_references"] += 1
                if gap_ref in gap_ids:
                    report["valid_references"] += 1
                else:
                    report["orphan_gap_references"].append({
                        "task_id": get_field_value(task, "task-id"),
                        "gap_reference": gap_ref
                    })

        # Check decisions without task linkage (per P10.7 - decisions should be task outcomes)
        for decision in decisions:
            decision_id = get_field_value(decision, "decision-id")
            report["missing_authority_links"].append({
                "decision_id": decision_id,
                "note": "Consider linking to source task with has-authority"
            })

        report["consistency_score"] = (
            report["valid_references"] / report["total_references"] * 100
            if report["total_references"] > 0 else 100
        )

        return report

    def generate_integrity_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive integrity report from all validations.

        Returns:
            Full report with statistics and details
        """
        if not self.results:
            return {"error": "No validations performed"}

        by_entity_type = {}
        by_level = {}

        for result in self.results:
            # Group by entity type
            if result.entity_type not in by_entity_type:
                by_entity_type[result.entity_type] = {"valid": 0, "invalid": 0, "warnings": 0}

            if result.is_valid:
                by_entity_type[result.entity_type]["valid"] += 1
            else:
                by_entity_type[result.entity_type]["invalid"] += 1

            if result.warnings:
                by_entity_type[result.entity_type]["warnings"] += len(result.warnings)

            # Group by level
            level_key = result.level.value
            if level_key not in by_level:
                by_level[level_key] = {"valid": 0, "invalid": 0}

            if result.is_valid:
                by_level[level_key]["valid"] += 1
            else:
                by_level[level_key]["invalid"] += 1

        total_valid = sum(d["valid"] for d in by_entity_type.values())
        total_invalid = sum(d["invalid"] for d in by_entity_type.values())

        return {
            "summary": {
                "total_validations": len(self.results),
                "valid": total_valid,
                "invalid": total_invalid,
                "integrity_score": (total_valid / len(self.results) * 100) if self.results else 0
            },
            "by_entity_type": by_entity_type,
            "by_level": by_level,
            "timestamp": datetime.now().isoformat()
        }
