"""
Rules and Decisions Routes.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-002: Extracted from api.py.

Created: 2024-12-28
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any

from governance.client import get_client
from governance.models import (
    RuleCreate, RuleUpdate, RuleResponse,
    DecisionCreate, DecisionUpdate, DecisionResponse
)

router = APIRouter(tags=["Rules"])


# =============================================================================
# RULES CRUD
# =============================================================================

@router.get("/rules", response_model=List[RuleResponse])
async def list_rules(
    offset: int = Query(0, ge=0, description="Skip first N results"),
    limit: int = Query(50, ge=1, le=200, description="Max results (1-200)"),
    sort_by: str = Query("id", description="Sort by: id, name, priority, status, category"),
    order: str = Query("asc", description="Sort order: asc or desc"),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority")
):
    """
    List governance rules with pagination, sorting, and filtering.

    Per GAP-UI-036: Pagination support.
    """
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        if category:
            rules = client.get_rules_by_category(category)
        elif status == "ACTIVE":
            rules = client.get_active_rules()
        else:
            rules = client.get_all_rules()

        # Filter by status if provided and not already filtered
        if status and status != "ACTIVE":
            rules = [r for r in rules if r.status == status]

        # Filter by priority
        if priority:
            rules = [r for r in rules if r.priority == priority]

        # Apply sorting
        valid_sort_fields = ["id", "name", "priority", "status", "category"]
        sort_field = sort_by if sort_by in valid_sort_fields else "id"
        reverse = order.lower() == "desc"
        rules.sort(key=lambda r: getattr(r, sort_field) or "", reverse=reverse)

        # Apply pagination
        rules = rules[offset:offset + limit]

        return [
            RuleResponse(
                id=r.id,
                name=r.name,
                category=r.category,
                priority=r.priority,
                status=r.status,
                directive=r.directive,
                created_date=r.created_date.isoformat() if r.created_date else None
            )
            for r in rules
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: str):
    """Get a specific rule by ID."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        rule = client.get_rule_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

        return RuleResponse(
            id=rule.id,
            name=rule.name,
            category=rule.category,
            priority=rule.priority,
            status=rule.status,
            directive=rule.directive,
            created_date=rule.created_date.isoformat() if rule.created_date else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules", response_model=RuleResponse, status_code=201)
async def create_rule(rule: RuleCreate):
    """Create a new governance rule."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        # Check if rule already exists
        existing = client.get_rule_by_id(rule.rule_id)
        if existing:
            raise HTTPException(status_code=409, detail=f"Rule {rule.rule_id} already exists")

        created = client.create_rule(
            rule_id=rule.rule_id,
            name=rule.name,
            category=rule.category,
            priority=rule.priority,
            directive=rule.directive,
            status=rule.status
        )

        if not created:
            raise HTTPException(status_code=500, detail="Failed to create rule")

        return RuleResponse(
            id=created.id,
            name=created.name,
            category=created.category,
            priority=created.priority,
            status=created.status,
            directive=created.directive,
            created_date=created.created_date.isoformat() if created.created_date else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(rule_id: str, rule: RuleUpdate):
    """Update an existing rule."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        # Check if rule exists
        existing = client.get_rule_by_id(rule_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

        updated = client.update_rule(
            rule_id=rule_id,
            name=rule.name,
            category=rule.category,
            priority=rule.priority,
            directive=rule.directive,
            status=rule.status
        )

        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update rule")

        return RuleResponse(
            id=updated.id,
            name=updated.name,
            category=updated.category,
            priority=updated.priority,
            status=updated.status,
            directive=updated.directive,
            created_date=updated.created_date.isoformat() if updated.created_date else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: str, archive: bool = Query(True, description="Archive before delete")):
    """Delete a rule (archives by default)."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        # Check if rule exists
        existing = client.get_rule_by_id(rule_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

        deleted = client.delete_rule(rule_id, archive=archive)
        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete rule")

        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# DECISIONS (Read-only from TypeDB)
# =============================================================================

@router.get("/decisions", response_model=List[Dict[str, Any]])
async def list_decisions():
    """List all strategic decisions."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        decisions = client.get_all_decisions()
        return [
            {
                "id": d.id,
                "name": d.name,
                "context": d.context,
                "rationale": d.rationale,
                "status": d.status,
                "decision_date": d.decision_date.isoformat() if d.decision_date else None
            }
            for d in decisions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions/{decision_id}", response_model=DecisionResponse)
async def get_decision(decision_id: str):
    """Get a specific decision by ID."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        decisions = client.get_all_decisions()
        for d in decisions:
            if d.id == decision_id:
                return DecisionResponse(
                    id=d.id,
                    name=d.name,
                    context=d.context,
                    rationale=d.rationale,
                    status=d.status,
                    decision_date=d.decision_date.isoformat() if d.decision_date else None
                )
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decisions", response_model=DecisionResponse, status_code=201)
async def create_decision(decision: DecisionCreate):
    """Create a new strategic decision. Per GAP-UI-033."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        # Check if decision already exists
        existing = client.get_all_decisions()
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
            return DecisionResponse(
                id=created.id,
                name=created.name,
                context=created.context,
                rationale=created.rationale,
                status=created.status,
                decision_date=created.decision_date.isoformat() if created.decision_date else None
            )
        raise HTTPException(status_code=500, detail="Failed to create decision")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            status=decision.status
        )

        if updated:
            return DecisionResponse(
                id=updated.id,
                name=updated.name,
                context=updated.context,
                rationale=updated.rationale,
                status=updated.status,
                decision_date=updated.decision_date.isoformat() if updated.decision_date else None
            )
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
