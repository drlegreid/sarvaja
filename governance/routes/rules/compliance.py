"""
Rules Compliance Route — Enforcement Summary.

Per EPIC-GOV-RULES-V3 P4: GET /api/rules/enforcement/summary endpoint.
SRP: Enforcement routes separate from rule CRUD routes.

Created: 2026-03-25
"""

import logging
from fastapi import APIRouter, HTTPException

from governance.services import rules as rule_service
from governance.workflow_compliance.enforcement import ComplianceChecker

router = APIRouter(tags=["Rules Enforcement"])
logger = logging.getLogger(__name__)


@router.get("/rules/enforcement/summary")
async def enforcement_summary():
    """
    Get enforcement summary across all active rules.

    Returns counts per applicability level (MANDATORY, RECOMMENDED,
    FORBIDDEN, CONDITIONAL, unspecified) and lists unimplemented
    MANDATORY rules that lack runtime check functions.

    Uses service layer directly to avoid self-calling REST deadlock.
    """
    try:
        # Fetch rules via service layer (direct TypeDB), not REST API
        result = rule_service.list_rules(limit=200, source="enforcement")
        rules = result.get("items", [])
        checker = ComplianceChecker()
        summary = checker.get_enforcement_summary(rules=rules)
        return summary
    except ConnectionError:
        raise HTTPException(status_code=503, detail="TypeDB not connected")
    except Exception as e:
        logger.error(f"Failed to get enforcement summary: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get enforcement summary")
