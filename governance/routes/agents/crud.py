"""Agents CRUD Routes - Delegates to service layer for MCP compliance.

Per DOC-SIZE-01-v1: Files under 300 lines.
Per MCP enforcement: Uses governance.services.agents for all operations.

Created: 2026-01-14
Updated: 2026-02-01 - Refactored to service layer delegation
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from governance.models import AgentCreate, AgentResponse, PaginatedAgentResponse, PaginationMeta
from governance.services import agents as agent_service
from governance.services import sessions as session_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Agents"])


@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_agent(body: AgentCreate):
    """Create a new agent. Per ASSESS-PLATFORM-GAPS-2026-02-15 Fix B."""
    result = agent_service.create_agent(
        agent_id=body.agent_id,
        name=body.name,
        agent_type=body.agent_type,
        trust_score=body.trust_score,
        capabilities=body.capabilities,
        rules=body.rules,
        source="rest-api",
    )
    if result is None:
        raise HTTPException(status_code=409, detail=f"Agent {body.agent_id} already exists")
    return AgentResponse(**result)


@router.get("/agents", response_model=PaginatedAgentResponse)
async def list_agents(
    offset: int = Query(0, ge=0, description="Skip first N results"),
    limit: int = Query(50, ge=1, le=200, description="Max results (1-200)"),
    sort_by: str = Query("trust_score", description="Sort by: agent_id, name, trust_score, status"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE, INACTIVE")
):
    """List agents with pagination, sorting, and filtering. Per GAP-ARCH-003, GAP-UI-036."""
    result = agent_service.list_agents(
        agent_type=agent_type, status=status,
        sort_by=sort_by, order=order, offset=offset, limit=limit,
        source="rest-api",
    )
    items = [AgentResponse(**a) for a in result["items"]]
    return PaginatedAgentResponse(
        items=items,
        pagination=PaginationMeta(
            total=result["total"], offset=result["offset"],
            limit=result["limit"], has_more=result["has_more"],
            returned=len(items),
        ),
    )


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get a specific agent. Per GAP-ARCH-003, GAP-UI-048."""
    result = agent_service.get_agent(agent_id, source="rest-api")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return AgentResponse(**result)


@router.delete("/agents/{agent_id}", status_code=204)
async def delete_agent(agent_id: str):
    """Delete an agent. Per GAP-ARCH-003."""
    if not agent_service.delete_agent(agent_id, source="rest-api"):
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return None


@router.put("/agents/{agent_id}/status/toggle", response_model=AgentResponse)
async def toggle_agent_status(agent_id: str):
    """Toggle agent between PAUSED and ACTIVE. Per GAP-AGENT-PAUSE-001."""
    result = agent_service.toggle_agent_status(agent_id, source="rest-api")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return AgentResponse(**result)


@router.put("/agents/{agent_id}/task", response_model=AgentResponse)
async def record_agent_task(agent_id: str):
    """Record that an agent executed a task. Per P11.9, GAP-STUB-005."""
    result = agent_service.record_task_execution(agent_id, source="rest-api")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return AgentResponse(**result)


@router.get("/agents/{agent_id}/sessions")
async def get_agent_sessions(
    agent_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Get sessions linked to an agent. Per EPIC-A.4: Session-agent linking."""
    # Verify agent exists
    agent = agent_service.get_agent(agent_id, source="rest-api")
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    result = session_service.list_sessions(
        agent_id=agent_id, offset=offset, limit=limit,
    )
    return {
        "agent_id": agent_id,
        "sessions": result["items"],
        "pagination": {
            "total": result["total"],
            "offset": result["offset"],
            "limit": result["limit"],
            "has_more": result["has_more"],
        },
    }
