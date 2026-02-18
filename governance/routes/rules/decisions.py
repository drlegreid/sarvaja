"""
Decisions CRUD Routes.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-UI-033: Full Decision CRUD.
Per GAP-DECISION-001: Linked rules support.
Per DOC-SIZE-01-v1: Modularized from rules.py.

Created: 2024-12-28
Updated: 2026-01-17 - Modularized to package
"""

import logging

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional

from governance.client import get_client
from governance.models import (
    DecisionCreate, DecisionUpdate, DecisionResponse,
    PaginatedDecisionResponse, PaginationMeta,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Decisions"])


# =============================================================================
# DECISIONS CRUD
# =============================================================================

@router.get("/decisions", response_model=PaginatedDecisionResponse)
async def list_decisions(
    offset: int = Query(0, ge=0, description="Skip first N results"),
    limit: int = Query(50, ge=1, le=200, description="Max results (1-200)"),
    status: Optional[str] = Query(None, description="Filter by status: PENDING, APPROVED, REJECTED"),
):
    """List strategic decisions with pagination and linked rules. Per GAP-DECISION-001."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        # BUG-ROUTE-003: Null-safe — get_all_decisions() may return None
        decisions = client.get_all_decisions() or []

        # Apply status filter
        if status:
            decisions = [d for d in decisions if d.status == status]

        total = len(decisions)
        paginated = decisions[offset:offset + limit]

        items = []
        for d in paginated:
            # Get linked rules per GAP-DECISION-001
            linked_rules = []
            try:
                linked_rules = client.get_decision_impacts(d.id)
            except Exception as e:
                # BUG-468-DEC-001: Sanitize logger message + add exc_info for stack trace preservation
                logger.warning(f"Failed to get impacts for {d.id}: {type(e).__name__}", exc_info=True)

            items.append(DecisionResponse(
                id=d.id,
                name=d.name,
                context=d.context,
                rationale=d.rationale,
                status=d.status,
                decision_date=d.decision_date.isoformat() if d.decision_date else None,
                linked_rules=linked_rules
            ))

        return PaginatedDecisionResponse(
            items=items,
            pagination=PaginationMeta(
                total=total,
                offset=offset,
                limit=limit,
                has_more=(offset + limit) < total,
                returned=len(items),
            ),
        )
    # BUG-377-DEC-001: Log full error but return only type name to HTTP client
    except Exception as e:
        # BUG-468-DEC-002: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"list_decisions failed: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"list_decisions failed: {type(e).__name__}")


@router.get("/decisions/{decision_id}", response_model=DecisionResponse)
async def get_decision(decision_id: str):
    """Get a specific decision by ID with linked rules. Per GAP-DECISION-001."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        # BUG-ROUTE-003: Null-safe — get_all_decisions() may return None
        decisions = client.get_all_decisions() or []
        for d in decisions:
            if d.id == decision_id:
                # Get linked rules per GAP-DECISION-001
                linked_rules = []
                try:
                    linked_rules = client.get_decision_impacts(decision_id)
                except Exception as e:
                    logger.debug(f"Failed to get decision impacts for {decision_id}: {e}")

                return DecisionResponse(
                    id=d.id,
                    name=d.name,
                    context=d.context,
                    rationale=d.rationale,
                    status=d.status,
                    decision_date=d.decision_date.isoformat() if d.decision_date else None,
                    linked_rules=linked_rules
                )
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")
    except HTTPException:
        raise
    # BUG-377-DEC-001: Log full error but return only type name to HTTP client
    except ValueError as e:
        # BUG-468-DEC-003: Sanitize logger message + add exc_info for stack trace preservation
        logger.warning(f"get_decision validation error: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=422, detail=f"Validation error: {type(e).__name__}")
    except Exception as e:
        # BUG-468-DEC-004: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"get_decision failed: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"get_decision failed: {type(e).__name__}")


@router.post("/decisions", response_model=DecisionResponse, status_code=201)
async def create_decision(decision: DecisionCreate):
    """Create a new strategic decision. Per GAP-UI-033."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        # Check if decision already exists
        # BUG-ROUTE-003: Null-safe
        existing = client.get_all_decisions() or []
        if any(d.id == decision.decision_id for d in existing):
            raise HTTPException(status_code=409, detail=f"Decision {decision.decision_id} already exists")

        # Create decision in TypeDB
        created = client.create_decision(
            decision_id=decision.decision_id,
            name=decision.name,
            context=decision.context,
            rationale=decision.rationale,
            status=decision.status
        )

        if created:
            # GAP-DECISION-RULES-001: Link rules atomically at creation
            linked_rules = []
            for rule_id in decision.rules_applied:
                try:
                    if client.link_decision_to_rule(decision.decision_id, rule_id):
                        linked_rules.append(rule_id)
                except Exception as e:
                    # BUG-468-DEC-005: Sanitize logger message + add exc_info for stack trace preservation
                    logger.warning(f"Failed to link rule {rule_id} to {decision.decision_id}: {type(e).__name__}", exc_info=True)
            return DecisionResponse(
                id=created.id,
                name=created.name,
                context=created.context,
                rationale=created.rationale,
                status=created.status,
                decision_date=created.decision_date.isoformat() if created.decision_date else None,
                linked_rules=linked_rules,
            )
        raise HTTPException(status_code=500, detail="Failed to create decision")
    except HTTPException:
        raise
    # BUG-377-DEC-001: Log full error but return only type name to HTTP client
    except ValueError as e:
        # BUG-468-DEC-006: Sanitize logger message + add exc_info for stack trace preservation
        logger.warning(f"create_decision validation error: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=422, detail=f"Validation error: {type(e).__name__}")
    except Exception as e:
        # BUG-468-DEC-007: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"create_decision failed: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"create_decision failed: {type(e).__name__}")


@router.put("/decisions/{decision_id}", response_model=DecisionResponse)
async def update_decision(decision_id: str, decision: DecisionUpdate):
    """Update an existing decision. Per GAP-UI-033."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        updated = client.update_decision(
            decision_id=decision_id,
            name=decision.name,
            context=decision.context,
            rationale=decision.rationale,
            status=decision.status,
            decision_date=decision.decision_date
        )

        if updated:
            # Get linked rules per GAP-DECISION-001
            linked_rules = []
            try:
                linked_rules = client.get_decision_impacts(decision_id)
            except Exception as e:
                logger.debug(f"Failed to get decision impacts for {decision_id}: {e}")

            return DecisionResponse(
                id=updated.id,
                name=updated.name,
                context=updated.context,
                rationale=updated.rationale,
                status=updated.status,
                decision_date=updated.decision_date.isoformat() if updated.decision_date else None,
                linked_rules=linked_rules
            )
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")
    except HTTPException:
        raise
    # BUG-377-DEC-001: Log full error but return only type name to HTTP client
    except ValueError as e:
        # BUG-468-DEC-008: Sanitize logger message + add exc_info for stack trace preservation
        logger.warning(f"update_decision validation error: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=422, detail=f"Validation error: {type(e).__name__}")
    except Exception as e:
        # BUG-468-DEC-009: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"update_decision failed: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"update_decision failed: {type(e).__name__}")


@router.post("/decisions/{decision_id}/rules/{rule_id}", status_code=201)
async def link_rule_to_decision(decision_id: str, rule_id: str):
    """Link a rule to a decision via decision-affects relation."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        success = client.link_decision_to_rule(decision_id, rule_id)
        if success:
            linked_rules = client.get_decision_impacts(decision_id)
            return {"decision_id": decision_id, "rule_id": rule_id, "linked_rules": linked_rules}
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} or rule {rule_id} not found")
    except HTTPException:
        raise
    # BUG-377-DEC-001: Log full error but return only type name to HTTP client
    except Exception as e:
        # BUG-468-DEC-010: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"link_rule_to_decision failed: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"link_rule_to_decision failed: {type(e).__name__}")


@router.delete("/decisions/{decision_id}", status_code=204)
async def delete_decision(decision_id: str):
    """Delete a decision. Per GAP-UI-033."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        deleted = client.delete_decision(decision_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")
    except HTTPException:
        raise
    # BUG-377-DEC-001: Log full error but return only type name to HTTP client
    except ValueError as e:
        # BUG-468-DEC-011: Sanitize logger message + add exc_info for stack trace preservation
        logger.warning(f"delete_decision validation error: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=422, detail=f"Validation error: {type(e).__name__}")
    except Exception as e:
        # BUG-468-DEC-012: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"delete_decision failed: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"delete_decision failed: {type(e).__name__}")
