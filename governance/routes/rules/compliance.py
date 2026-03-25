"""
Rules Compliance Route — Enforcement Summary + Conflict Detection.

Per EPIC-GOV-RULES-V3 P4: GET /api/rules/enforcement/summary endpoint.
Per EPIC-GOV-RULES-V3 P5: GET /api/rules/conflicts endpoint.
SRP: Enforcement/compliance routes separate from rule CRUD routes.

Created: 2026-03-25
Updated: 2026-03-25 - P5: conflicts endpoint
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


@router.get("/rules/conflicts")
async def get_rule_conflicts():
    """
    Detect rule conflicts: scope overlaps and lifecycle breaks.

    Per EPIC-GOV-RULES-V3 P5: Combines kanren analysis with TypeDB dependency graph.
    Uses service layer directly to avoid self-calling REST deadlock.

    Returns:
        JSON with conflicts array, count, and conflict type breakdown
    """
    try:
        from governance.kanren.conflicts import find_rule_conflicts
        from governance.kanren.models import RuleContext
        from governance.services.rules_relations import dependency_overview

        # Fetch all rules via service layer
        result = rule_service.list_rules(limit=200, source="conflicts")
        raw_rules = result.get("items", [])

        # Convert to RuleContext for kanren analysis
        contexts = []
        for r in raw_rules:
            contexts.append(RuleContext(
                rule_id=r.get("id", r.get("rule_id", "")),
                priority=r.get("priority", "MEDIUM"),
                status=r.get("status", "ACTIVE"),
                category=r.get("category", ""),
            ))

        # Fetch dependency graph for lifecycle conflict detection
        from governance.client import get_client
        client = get_client()
        deps = {}
        if client:
            try:
                raw_deps = client.get_all_dependencies()
                deps = {k: list(v) if not isinstance(v, list) else v for k, v in raw_deps.items()}
            except Exception:
                logger.debug("Could not load dependency graph for conflict detection")

        conflicts = find_rule_conflicts(contexts, dependencies=deps)

        # Categorize
        scope_count = sum(1 for c in conflicts if "scope" in c[2].lower())
        lifecycle_count = sum(1 for c in conflicts if "lifecycle" in c[2].lower())

        return {
            "conflicts": [
                {"rule1": c[0], "rule2": c[1], "description": c[2]}
                for c in conflicts
            ],
            "count": len(conflicts),
            "scope_conflicts": scope_count,
            "lifecycle_conflicts": lifecycle_count,
        }
    except ConnectionError:
        raise HTTPException(status_code=503, detail="TypeDB not connected")
    except Exception as e:
        logger.error(f"Failed to detect rule conflicts: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to detect rule conflicts")
