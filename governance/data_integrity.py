"""
Data Integrity Validation Module (DEPRECATED - use governance.integrity package)
Created: P10.7
Modularized: 2026-01-02 (RULE-032)

This file is kept for backward compatibility.
Import from governance.integrity instead:

    from governance.integrity import DataIntegrityValidator, ValidationLevel

Per RULE-012 DSP: Data integrity validation documented
Per RULE-032: Files >300 lines MUST be modularized.
"""
import warnings

# Re-export from modular package for backward compatibility
from governance.integrity import (
    ValidationLevel,
    ValidationResult,
    ENTITY_SCHEMAS,
    VALID_VALUES,
    RELATION_SCHEMAS,
    get_entity_id,
    get_field_value,
    camel_case,
    DataIntegrityValidator,
    validate_edge_to_edge,
)

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

# Emit deprecation warning on import
warnings.warn(
    "governance.data_integrity is deprecated. "
    "Use 'from governance.integrity import DataIntegrityValidator' instead.",
    DeprecationWarning,
    stacklevel=2
)
