"""Taxonomy API Endpoint (META-TAXON-01-v1).

Returns task/rule taxonomy enums for UI dropdowns and validation.
"""
from fastapi import APIRouter

from agent.governance_ui.state.constants import (
    TASK_TYPES,
    TASK_PRIORITIES,
    TASK_TYPE_PREFIX,
    TASK_STATUSES,
    TASK_PHASES,
    RULE_CATEGORIES,
    RULE_PRIORITIES,
    RULE_STATUSES,
    PROJECT_ACRONYMS,
)

router = APIRouter()


@router.get("/taxonomy")
async def get_taxonomy():
    """Get task/rule taxonomy (types, priorities, statuses, prefixes).

    Returns all enum values used for validation and UI dropdowns.
    """
    return {
        "task_types": TASK_TYPES,
        "task_priorities": TASK_PRIORITIES,
        "task_type_prefixes": TASK_TYPE_PREFIX,
        "task_statuses": TASK_STATUSES,
        "task_phases": TASK_PHASES,
        "rule_categories": RULE_CATEGORIES,
        "rule_priorities": RULE_PRIORITIES,
        "rule_statuses": RULE_STATUSES,
        "project_acronyms": PROJECT_ACRONYMS,
    }
