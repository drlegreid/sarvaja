"""Workspace API Routes — CRUD for workspace entities.

Completes the entity chain: Project → **Workspace** → Agent.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from governance.models_entities import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceTypeResponse,
    WorkspaceAgentAssign,
)
from governance.services import workspaces as ws_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Workspaces"])


@router.get("/workspaces", response_model=list[WorkspaceResponse])
async def list_workspaces(
    project_id: Optional[str] = Query(None),
    workspace_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List workspaces with optional filters."""
    result = ws_service.list_workspaces(
        project_id=project_id, workspace_type=workspace_type,
        status=status, offset=offset, limit=limit,
    )
    return [WorkspaceResponse(**w) for w in result["items"]]


@router.get("/workspaces/types", response_model=list[WorkspaceTypeResponse])
async def list_workspace_types():
    """List all available workspace types."""
    return [WorkspaceTypeResponse(**wt) for wt in ws_service.get_workspace_types_list()]


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: str):
    """Get a workspace by ID."""
    ws = ws_service.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceResponse(**ws)


@router.post("/workspaces", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(body: WorkspaceCreate):
    """Create a new workspace."""
    result = ws_service.create_workspace(
        name=body.name,
        workspace_type=body.workspace_type,
        project_id=body.project_id,
        description=body.description,
        agent_ids=body.agent_ids,
        source="rest-api",
    )
    return WorkspaceResponse(**result)


@router.put("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(workspace_id: str, body: WorkspaceUpdate):
    """Update a workspace."""
    result = ws_service.update_workspace(
        workspace_id=workspace_id,
        name=body.name,
        description=body.description,
        status=body.status,
        agent_ids=body.agent_ids,
        source="rest-api",
    )
    if not result:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceResponse(**result)


@router.delete("/workspaces/{workspace_id}")
async def delete_workspace(workspace_id: str):
    """Delete a workspace."""
    if not ws_service.delete_workspace(workspace_id, source="rest-api"):
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"status": "deleted", "workspace_id": workspace_id}


@router.post("/workspaces/{workspace_id}/agents", response_model=WorkspaceResponse)
async def assign_agent(workspace_id: str, body: WorkspaceAgentAssign):
    """Assign an agent to a workspace."""
    result = ws_service.assign_agent_to_workspace(
        workspace_id, body.agent_id, source="rest-api",
    )
    if not result:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceResponse(**result)


@router.delete("/workspaces/{workspace_id}/agents/{agent_id}", response_model=WorkspaceResponse)
async def remove_agent(workspace_id: str, agent_id: str):
    """Remove an agent from a workspace."""
    result = ws_service.remove_agent_from_workspace(
        workspace_id, agent_id, source="rest-api",
    )
    if not result:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceResponse(**result)
