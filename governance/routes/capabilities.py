"""Capability API Routes — Rule→Agent binding CRUD.

Completes the entity chain: Agent → **Capabilities** (rules applied to agents).
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from governance.models_entities import (
    CapabilityCreate,
    CapabilityResponse,
    CapabilityStatusUpdate,
    CapabilitySummaryResponse,
)
from governance.services import capabilities as cap_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Capabilities"])


@router.get("/capabilities", response_model=list[CapabilityResponse])
async def list_capabilities(
    agent_id: Optional[str] = Query(None),
    rule_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """List rule→agent bindings with optional filters."""
    items = cap_service.list_capabilities(
        agent_id=agent_id, rule_id=rule_id,
        category=category, status=status,
    )
    return [CapabilityResponse(**c) for c in items]


@router.get("/capabilities/summary", response_model=CapabilitySummaryResponse)
async def get_capability_summary():
    """Get capability summary stats."""
    return CapabilitySummaryResponse(**cap_service.get_capability_summary())


@router.get("/agents/{agent_id}/capabilities", response_model=list[CapabilityResponse])
async def get_agent_capabilities(agent_id: str):
    """Get all rule bindings for a specific agent."""
    items = cap_service.get_capabilities_for_agent(agent_id)
    return [CapabilityResponse(**c) for c in items]


@router.get("/rules/{rule_id}/agents", response_model=list[CapabilityResponse])
async def get_rule_agents(rule_id: str):
    """Get all agents bound to a specific rule."""
    items = cap_service.get_agents_for_rule(rule_id)
    return [CapabilityResponse(**c) for c in items]


@router.post("/capabilities", response_model=CapabilityResponse, status_code=201)
async def bind_rule_to_agent(body: CapabilityCreate):
    """Bind a rule to an agent."""
    result = cap_service.bind_rule_to_agent(
        agent_id=body.agent_id,
        rule_id=body.rule_id,
        category=body.category,
        source="rest-api",
    )
    return CapabilityResponse(**result)


@router.delete("/capabilities/{agent_id}/{rule_id}")
async def unbind_rule_from_agent(agent_id: str, rule_id: str):
    """Remove a rule→agent binding."""
    if not cap_service.unbind_rule_from_agent(agent_id, rule_id, source="rest-api"):
        raise HTTPException(status_code=404, detail="Capability binding not found")
    return {"status": "deleted", "agent_id": agent_id, "rule_id": rule_id}


@router.put("/capabilities/{agent_id}/{rule_id}/status", response_model=CapabilityResponse)
async def update_capability_status(agent_id: str, rule_id: str, body: CapabilityStatusUpdate):
    """Update capability status (active/suspended)."""
    result = cap_service.update_capability_status(
        agent_id, rule_id, body.status, source="rest-api",
    )
    if not result:
        raise HTTPException(status_code=404, detail="Capability binding not found")
    return CapabilityResponse(**result)
