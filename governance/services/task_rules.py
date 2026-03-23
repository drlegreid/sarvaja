"""Task Quality Rules Engine (SRVJ-FEAT-001 + SRVJ-FEAT-002).

Static validation rules enforced at the MCP/service layer.
RDBMS-like constraints — symbolically strict, not retroactive.

Per DOC-SIZE-01-v1: Single responsibility module.
"""
import re
import logging
from typing import List, Dict, Any, Optional

from agent.governance_ui.state.constants import (
    TASK_TYPE_PREFIX,
    PROJECT_ACRONYMS,
)

logger = logging.getLogger(__name__)

# Laconic summary pattern: domain > entity > action > concern
# Minimum 3 segments separated by " > " (4th optional for simple tasks)
LACONIC_PATTERN = re.compile(r"^.+\s*>\s*.+\s*>\s*.+\s*>\s*.+$")
LACONIC_MIN_PATTERN = re.compile(r"^.+\s*>\s*.+\s*>\s*.+$")

# Valid project acronyms (from constants)
VALID_ACRONYMS = set(PROJECT_ACRONYMS.values())

# Valid type prefixes (from constants)
VALID_TYPE_PREFIXES = set(TASK_TYPE_PREFIX.values())

# Task ID pattern: {ACRONYM}-{TYPE}-{NNN} or legacy {TYPE}-{NNN}
NEW_ID_PATTERN = re.compile(
    r"^([A-Z]{2,6})-([A-Z]{2,6})-(\d{3,})$"
)
LEGACY_ID_PATTERN = re.compile(
    r"^([A-Z]{2,6})-(\d{3,})$"
)


class ValidationError:
    """Structured validation error."""

    def __init__(self, rule: str, field: str, message: str):
        self.rule = rule
        self.field = field
        self.message = message

    def to_dict(self) -> Dict[str, str]:
        return {"rule": self.rule, "field": self.field, "message": self.message}


def validate_on_create(
    task_id: Optional[str] = None,
    summary: Optional[str] = None,
    task_type: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs,
) -> List[ValidationError]:
    """Run on_create validation rules.

    Returns list of validation errors (empty = valid).
    """
    errors: List[ValidationError] = []

    # Rule 1: summary is required
    if not summary and not description:
        errors.append(ValidationError(
            "RequiredField", "summary",
            "summary is required (laconic: domain > entity > action > concern)",
        ))

    # Rule 2: summary format (laconic shorthand) — advisory warning, not blocking
    # Only validate if explicitly provided (auto-generated summaries from description are OK)
    if summary and not LACONIC_MIN_PATTERN.match(summary):
        errors.append(ValidationError(
            "FormatRule", "summary",
            "summary should follow laconic format: domain > entity > action > concern "
            f"(got: '{summary[:60]}')",
        ))

    # Rule 3: task_id project acronym (when explicitly provided with new format)
    if task_id:
        new_match = NEW_ID_PATTERN.match(task_id)
        if new_match:
            acronym = new_match.group(1)
            type_seg = new_match.group(2)
            if acronym not in VALID_ACRONYMS:
                errors.append(ValidationError(
                    "ProjectAcronymRule", "task_id",
                    f"task_id acronym '{acronym}' not in known projects: "
                    f"{sorted(VALID_ACRONYMS)}",
                ))
            if type_seg not in VALID_TYPE_PREFIXES:
                errors.append(ValidationError(
                    "TypePrefixRule", "task_id",
                    f"task_id type prefix '{type_seg}' not in valid types: "
                    f"{sorted(VALID_TYPE_PREFIXES)}",
                ))
            # Rule 4: type prefix must match task_type
            if task_type:
                expected_prefix = TASK_TYPE_PREFIX.get(task_type, "")
                if expected_prefix and type_seg != expected_prefix:
                    errors.append(ValidationError(
                        "TypePrefixMismatch", "task_id",
                        f"task_id type '{type_seg}' doesn't match task_type "
                        f"'{task_type}' (expected prefix: '{expected_prefix}')",
                    ))

    return errors


def validate_on_complete(
    task_id: str,
    summary: Optional[str] = None,
    agent_id: Optional[str] = None,
    completed_at: Optional[str] = None,
    linked_sessions: Optional[List[str]] = None,
    linked_documents: Optional[List[str]] = None,
    **kwargs,
) -> List[ValidationError]:
    """Run on_complete validation rules (DONE gate).

    These rules are enforced when a task transitions to DONE status.

    Returns list of validation errors (empty = valid).
    """
    errors: List[ValidationError] = []

    # Rule 1: Must have at least 1 linked session
    if not linked_sessions:
        errors.append(ValidationError(
            "RequiredField", "linked_sessions",
            "DONE tasks must have at least 1 linked session",
        ))

    # Rule 2: Must have summary
    if not summary:
        errors.append(ValidationError(
            "RequiredField", "summary",
            "DONE tasks must have a summary",
        ))

    # Rule 3: Must have agent_id
    if not agent_id:
        errors.append(ValidationError(
            "RequiredField", "agent_id",
            "DONE tasks must have an agent_id (who did the work)",
        ))

    # Rule 4: Must have completed_at (SRVJ-BUG-002)
    if not completed_at:
        errors.append(ValidationError(
            "RequiredField", "completed_at",
            "DONE tasks must have a completed_at timestamp",
        ))

    # Rule 5: Must have at least 1 linked document / plan reference (SRVJ-BUG-002)
    if not linked_documents:
        errors.append(ValidationError(
            "RequiredField", "linked_documents",
            "DONE tasks must have at least 1 linked document (plan reference)",
        ))

    return errors


def format_validation_result(errors: List[ValidationError]) -> Dict[str, Any]:
    """Format validation errors as structured dict for API responses."""
    return {
        "validation_errors": [e.to_dict() for e in errors],
        "valid": len(errors) == 0,
    }
