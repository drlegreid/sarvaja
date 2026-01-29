"""
Decisions CRUD Routes.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-UI-033: Full Decision CRUD.
Per GAP-DECISION-001: Linked rules support.
Per DOC-SIZE-01-v1: Modularized from rules.py.

Created: 2024-12-28
Updated: 2026-01-17 - Modularized to package
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from governance.client import get_client
from governance.models import DecisionCreate, DecisionUpdate, DecisionResponse

router = APIRouter(tags=["Decisions"])


# =============================================================================
# DECISIONS CRUD
# =============================================================================

@router.get("/decisions", response_model=List[Dict[str, Any]])
async def list_decisions():
    """List all strategic decisions with linked rules. Per GAP-DECISION-001."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        decisions = client.get_all_decisions()
        result = []
        for d in decisions:
            # Get linked rules per GAP-DECISION-001
            linked_rules = []
            try:
                linked_rules = client.get_decision_impacts(d.id)
            except Exception:
                pass  # Non-critical, return empty list

            result.append({
                "id": d.id,
                "name": d.name,
                "context": d.context,
                "rationale": d.rationale,
                "status": d.status,
                "decision_date": d.decision_date.isoformat() if d.decision_date else None,
                "linked_rules": linked_rules
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions/{decision_id}", response_model=DecisionResponse)
async def get_decision(decision_id: str):
    """Get a specific decision by ID with linked rules. Per GAP-DECISION-001."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        decisions = client.get_all_decisions()
        for d in decisions:
            if d.id == decision_id:
                # Get linked rules per GAP-DECISION-001
                linked_rules = []
                try:
                    linked_rules = client.get_decision_impacts(decision_id)
                except Exception:
                    pass  # Non-critical

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
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
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
                decision_date=created.decision_date.isoformat() if created.decision_date else None,
                linked_rules=[]  # New decisions have no linked rules initially
            )
        raise HTTPException(status_code=500, detail="Failed to create decision")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
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
            status=decision.status,
            decision_date=decision.decision_date
        )

        if updated:
            # Get linked rules per GAP-DECISION-001
            linked_rules = []
            try:
                linked_rules = client.get_decision_impacts(decision_id)
            except Exception:
                pass  # Non-critical

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
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
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
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
