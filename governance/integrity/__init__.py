"""
Data Integrity Package (P10.7 - Edge-to-Edge Validation)
Created: P10.7
Modularized: 2026-01-02 (RULE-032)

Provides validation from TypeDB schema through to UI,
ensuring data consistency across all layers.

Layers:
1. TypeDB Schema - Entity definitions and relations
2. Python Client - TypeDB client operations
3. API Layer - REST API endpoints
4. UI Layer - Governance dashboard display

Per RULE-012 DSP: Data integrity validation documented

Usage:
    from governance.integrity import DataIntegrityValidator, ValidationLevel

    validator = DataIntegrityValidator()
    result = validator.validate_entity("rule", rule_data, ValidationLevel.API)
"""

from governance.integrity.models import ValidationLevel, ValidationResult
from governance.integrity.schemas import ENTITY_SCHEMAS, VALID_VALUES, RELATION_SCHEMAS
from governance.integrity.helpers import get_entity_id, get_field_value, camel_case
from governance.integrity.validator import DataIntegrityValidator
from governance.integrity.edge_to_edge import validate_edge_to_edge

__all__ = [
    "ValidationLevel",
    "ValidationResult",
    "ENTITY_SCHEMAS",
    "VALID_VALUES",
    "RELATION_SCHEMAS",
    "get_entity_id",
    "get_field_value",
    "camel_case",
    "DataIntegrityValidator",
    "validate_edge_to_edge",
]
