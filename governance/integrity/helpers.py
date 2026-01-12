"""
Data Integrity Helpers
Created: P10.7
Modularized: 2026-01-02 (RULE-032)

Helper functions for field extraction and naming convention handling.
"""
from typing import Dict, Any, Optional


def get_entity_id(entity_type: str, entity_data: Dict) -> str:
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


def get_field_value(data: Dict, field: str) -> Optional[Any]:
    """Get field value, handling various naming conventions."""
    field_variations = [
        field,
        field.replace("-", "_"),
        field.replace("-", ""),
        camel_case(field)
    ]
    for f in field_variations:
        if f in data:
            return data[f]
    return None


def camel_case(s: str) -> str:
    """Convert kebab-case to camelCase."""
    parts = s.split("-")
    return parts[0] + "".join(p.title() for p in parts[1:])
