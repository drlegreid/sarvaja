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

# =============================================================================
# TYPE-SPECIFIC DoD REQUIREMENTS (EPIC-TASK-TAXONOMY-V2 Session 3)
# =============================================================================
# Per-type mandatory fields for the DONE gate. Each key is a canonical task type,
# value is a dict of {field_name: human-readable requirement description}.
# Fields: summary, agent_id, linked_sessions, linked_documents, evidence
TYPE_DOD_REQUIREMENTS: Dict[str, Dict[str, str]] = {
    "bug": {
        "summary": "Bug summary is required",
        "agent_id": "Who fixed the bug",
        "linked_sessions": "At least 1 linked session (work evidence)",
        "evidence": "Verification evidence (test results or manual confirmation)",
    },
    "feature": {
        "summary": "Feature summary is required",
        "agent_id": "Who implemented the feature",
        "linked_sessions": "At least 1 linked session (work evidence)",
        "linked_documents": "At least 1 linked document (requirements or plan)",
    },
    "chore": {
        "summary": "Chore summary is required",
        "agent_id": "Who performed the maintenance",
    },
    "research": {
        "summary": "Research summary is required",
        "agent_id": "Who conducted the research",
        "evidence": "Findings documentation",
    },
    "spec": {
        "summary": "Spec summary is required",
        "agent_id": "Who authored the spec",
        "linked_documents": "At least 1 linked document (the spec itself)",
    },
    "test": {
        "summary": "Test summary is required",
        "agent_id": "Who wrote/ran the tests",
        "evidence": "Test results and coverage data",
    },
}

# Default DoD for unknown types — minimal gate (same as chore)
_DEFAULT_DOD_REQUIREMENTS: Dict[str, str] = {
    "summary": "Task summary is required",
    "agent_id": "Who did the work",
}


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


def validate_agent_id(agent_id: Optional[str]) -> List[ValidationError]:
    """Validate agent_id against registered agents (SRVJ-BUG-023).

    Returns empty list if None (optional) or valid. Returns error if non-null
    but not in VALID_AGENT_IDS.
    """
    if agent_id is None:
        return []
    from governance.stores.agents import VALID_AGENT_IDS
    if agent_id not in VALID_AGENT_IDS:
        return [ValidationError(
            "InvalidAgent", "agent_id",
            f"Invalid agent_id '{agent_id}'. Must be one of: {sorted(VALID_AGENT_IDS)}",
        )]
    return []


def validate_on_complete(
    task_id: str,
    summary: Optional[str] = None,
    agent_id: Optional[str] = None,
    completed_at: Optional[str] = None,
    linked_sessions: Optional[List[str]] = None,
    linked_documents: Optional[List[str]] = None,
    task_type: Optional[str] = None,
    evidence: Optional[str] = None,
    **kwargs,
) -> List[ValidationError]:
    """Run on_complete validation rules (DONE gate).

    Per EPIC-TASK-TAXONOMY-V2 Session 3: Type-specific DoD requirements.
    Falls back to universal gate if task_type is None or unknown.

    Returns list of validation errors (empty = valid).
    """
    errors: List[ValidationError] = []

    # Resolve type-specific requirements (or default)
    dod = TYPE_DOD_REQUIREMENTS.get(task_type, _DEFAULT_DOD_REQUIREMENTS) if task_type else _DEFAULT_DOD_REQUIREMENTS

    # Build field→value map for requirement checking
    field_values: Dict[str, Any] = {
        "summary": summary,
        "agent_id": agent_id,
        "linked_sessions": linked_sessions,
        "linked_documents": linked_documents,
        "evidence": evidence,
    }

    # Validate each required field from the DoD
    for field, requirement_msg in dod.items():
        val = field_values.get(field)
        if not val:
            errors.append(ValidationError(
                "RequiredField", field,
                f"DONE gate ({task_type or 'default'}): {requirement_msg}",
            ))

    # Always validate agent_id format if present (SRVJ-BUG-023)
    if agent_id:
        errors.extend(validate_agent_id(agent_id))

    # Always require completed_at (SRVJ-BUG-002)
    if not completed_at:
        errors.append(ValidationError(
            "RequiredField", "completed_at",
            "DONE tasks must have a completed_at timestamp",
        ))

    return errors


def format_validation_result(errors: List[ValidationError]) -> Dict[str, Any]:
    """Format validation errors as structured dict for API responses."""
    return {
        "validation_errors": [e.to_dict() for e in errors],
        "valid": len(errors) == 0,
    }
