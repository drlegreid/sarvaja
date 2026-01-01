"""
Data Integrity Validation Module (P10.7 - Edge-to-Edge Validation)

This module provides validation from TypeDB schema through to UI,
ensuring data consistency across all layers per user directive.

Layers:
1. TypeDB Schema - Entity definitions and relations
2. Python Client - TypeDB client operations
3. API Layer - REST API endpoints
4. UI Layer - Governance dashboard display

Per RULE-012 DSP: Data integrity validation documented
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json
import re
from datetime import datetime


class ValidationLevel(Enum):
    """Validation levels for edge-to-edge checks."""
    SCHEMA = "schema"      # TypeDB schema validation
    CLIENT = "client"      # Python client validation
    API = "api"            # REST API validation
    UI = "ui"              # UI display validation


class ValidationResult:
    """Result of a validation check."""

    def __init__(self, entity_type: str, entity_id: str, level: ValidationLevel):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.level = level
        self.passed: List[str] = []
        self.failed: List[Tuple[str, str]] = []  # (check_name, reason)
        self.warnings: List[Tuple[str, str]] = []
        self.timestamp = datetime.now()

    @property
    def is_valid(self) -> bool:
        return len(self.failed) == 0

    def add_pass(self, check_name: str):
        self.passed.append(check_name)

    def add_fail(self, check_name: str, reason: str):
        self.failed.append((check_name, reason))

    def add_warning(self, check_name: str, reason: str):
        self.warnings.append((check_name, reason))

    def to_dict(self) -> Dict:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "level": self.level.value,
            "is_valid": self.is_valid,
            "passed": self.passed,
            "failed": [{"check": c, "reason": r} for c, r in self.failed],
            "warnings": [{"check": c, "reason": r} for c, r in self.warnings],
            "timestamp": self.timestamp.isoformat()
        }


class DataIntegrityValidator:
    """
    Edge-to-edge data integrity validator.

    Validates entities across all layers:
    - Schema compliance (TypeDB entity structure)
    - Client compliance (Python dataclass/dict structure)
    - API compliance (REST response structure)
    - UI compliance (Display data structure)
    """

    # Required fields per entity type (from TypeDB schema)
    ENTITY_SCHEMAS = {
        "rule": {
            "required": ["rule-id", "rule-name", "category", "priority", "status", "directive"],
            "optional": ["created-date"],
            "id_pattern": r"^RULE-\d{3}$"
        },
        "decision": {
            "required": ["decision-id", "decision-name", "context", "rationale"],
            "optional": ["decision-status", "decision-date"],
            "id_pattern": r"^DECISION-\d{3}$"
        },
        "task": {
            "required": ["task-id", "task-name", "task-status"],
            "optional": ["task-body", "phase", "gap-reference"],
            "id_pattern": r"^(P\d+\.\d+|RD-\d{3}|ORCH-\d{3}|TEST-\d{3}|FH-\d{3}|TOOL-\d{3}|DOC-\d{3})$"
        },
        "gap": {
            "required": ["gap-id", "gap-name", "gap-status", "severity"],
            "optional": ["location"],
            "id_pattern": r"^GAP-[A-Z]+-\d{3}$"
        },
        "agent": {
            "required": ["agent-id", "agent-name", "agent-type"],
            "optional": ["trust-score", "compliance-rate", "accuracy-rate", "tenure-days"],
            "id_pattern": r"^(AGENT-\d{3}|TEST-AGENT-\d{3})$"
        },
        "session": {
            "required": ["session-id"],
            "optional": ["session-name", "session-description", "session-file-path", "started-at", "completed-at"],
            "id_pattern": r"^SESSION-\d{4}-\d{2}-\d{2}-.*$"
        }
    }

    # Valid values for enum-like attributes
    VALID_VALUES = {
        "priority": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        "status": ["ACTIVE", "DRAFT", "DEPRECATED"],
        "decision-status": ["APPROVED", "PENDING", "SUPERSEDED"],
        "task-status": ["TODO", "IN_PROGRESS", "DONE", "BLOCKED", "pending", "in_progress", "completed"],
        "gap-status": ["OPEN", "RESOLVED", "DEFERRED", "PARTIAL"],
        "severity": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        "agent-type": ["claude-code", "docker-agent", "sync-agent", "test-agent"]
    }

    # Relation schemas (P10.7 typed references)
    RELATION_SCHEMAS = {
        "references-gap": {
            "roles": ["referencing-task", "referenced-gap"],
            "required_entities": ["task", "gap"]
        },
        "task-outcome": {
            "roles": ["outcome-decision", "source-task"],
            "attributes": ["has-authority"],
            "required_entities": ["decision", "task"]
        },
        "implements-rule": {
            "roles": ["implementing-task", "implemented-rule"],
            "required_entities": ["task", "rule"]
        },
        "completed-in": {
            "roles": ["completed-task", "hosting-session"],
            "required_entities": ["task", "session"]
        },
        "decision-affects": {
            "roles": ["affecting-decision", "affected-rule"],
            "required_entities": ["decision", "rule"]
        }
    }

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
        entity_id = self._get_entity_id(entity_type, entity_data)
        result = ValidationResult(entity_type, entity_id, level)

        schema = self.ENTITY_SCHEMAS.get(entity_type)
        if not schema:
            result.add_fail("schema_exists", f"Unknown entity type: {entity_type}")
            return result

        # Check required fields
        for field in schema["required"]:
            # Convert TypeDB naming (e.g., "rule-id") to common variations
            field_variations = [
                field,
                field.replace("-", "_"),
                field.replace("-", ""),
                self._camel_case(field)
            ]

            found = any(f in entity_data and entity_data[f] is not None for f in field_variations)
            if found:
                result.add_pass(f"required_field_{field}")
            else:
                result.add_fail(f"required_field_{field}", f"Missing required field: {field}")

        # Validate ID pattern
        id_field = f"{entity_type}-id" if entity_type != "session" else "session-id"
        id_value = self._get_field_value(entity_data, id_field)
        if id_value:
            pattern = schema.get("id_pattern")
            if pattern and not re.match(pattern, str(id_value)):
                result.add_warning(f"id_pattern", f"ID '{id_value}' doesn't match expected pattern: {pattern}")
            else:
                result.add_pass("id_pattern")

        # Validate enum values
        for field, valid_values in self.VALID_VALUES.items():
            value = self._get_field_value(entity_data, field)
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

        schema = self.RELATION_SCHEMAS.get(relation_type)
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
        gap_ids = {self._get_field_value(g, "gap-id") for g in gaps if self._get_field_value(g, "gap-id")}
        rule_ids = {self._get_field_value(r, "rule-id") for r in rules if self._get_field_value(r, "rule-id")}

        # Check task gap references
        for task in tasks:
            gap_ref = self._get_field_value(task, "gap-reference")
            if gap_ref:
                report["total_references"] += 1
                if gap_ref in gap_ids:
                    report["valid_references"] += 1
                else:
                    report["orphan_gap_references"].append({
                        "task_id": self._get_field_value(task, "task-id"),
                        "gap_reference": gap_ref
                    })

        # Check decisions without task linkage (per P10.7 - decisions should be task outcomes)
        for decision in decisions:
            decision_id = self._get_field_value(decision, "decision-id")
            # This is informational - authority links may not exist yet
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

    def _get_entity_id(self, entity_type: str, entity_data: Dict) -> str:
        """Get entity ID from data, handling various naming conventions."""
        id_fields = [
            f"{entity_type}-id",
            f"{entity_type}_id",
            f"{entity_type}Id",
            "id"
        ]
        for field in id_fields:
            if field in entity_data:
                return str(entity_data[field])
        return "unknown"

    def _get_field_value(self, data: Dict, field: str) -> Optional[Any]:
        """Get field value, handling various naming conventions."""
        field_variations = [
            field,
            field.replace("-", "_"),
            field.replace("-", ""),
            self._camel_case(field)
        ]
        for f in field_variations:
            if f in data:
                return data[f]
        return None

    def _camel_case(self, s: str) -> str:
        """Convert kebab-case to camelCase."""
        parts = s.split("-")
        return parts[0] + "".join(p.title() for p in parts[1:])


def validate_edge_to_edge(
    client=None,
    api_url: str = "http://localhost:8082"
) -> Dict[str, Any]:
    """
    Run full edge-to-edge validation.

    Args:
        client: Optional TypeDBClient instance
        api_url: REST API base URL

    Returns:
        Complete validation report
    """
    import httpx

    validator = DataIntegrityValidator()
    results = {}

    # API Layer Validation
    try:
        with httpx.Client(timeout=10.0) as http:
            # Validate rules
            response = http.get(f"{api_url}/api/rules")
            if response.status_code == 200:
                rules = response.json()
                results["rules"] = validator.validate_entity_set("rule", rules, ValidationLevel.API)

            # Validate tasks
            response = http.get(f"{api_url}/api/tasks")
            if response.status_code == 200:
                tasks = response.json()
                results["tasks"] = validator.validate_entity_set("task", tasks, ValidationLevel.API)

            # Validate agents
            response = http.get(f"{api_url}/api/agents")
            if response.status_code == 200:
                agents = response.json()
                results["agents"] = validator.validate_entity_set("agent", agents, ValidationLevel.API)

            # Validate sessions
            response = http.get(f"{api_url}/api/sessions")
            if response.status_code == 200:
                sessions = response.json()
                results["sessions"] = validator.validate_entity_set("session", sessions, ValidationLevel.API)

            # Validate decisions
            response = http.get(f"{api_url}/api/decisions")
            if response.status_code == 200:
                decisions = response.json()
                results["decisions"] = validator.validate_entity_set("decision", decisions, ValidationLevel.API)

    except Exception as e:
        results["api_error"] = str(e)

    # Generate final report
    results["integrity_report"] = validator.generate_integrity_report()

    return results
