"""
Data Integrity Models
Created: P10.7
Modularized: 2026-01-02 (RULE-032)

Enums and dataclasses for validation operations.
"""
from typing import Dict, List, Tuple
from enum import Enum
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
