"""
Project CRUD Routes.

Per GOV-PROJECT-01-v1: Project hierarchy management.
Created: 2026-02-11
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from governance.models import (
    ProjectCreate, ProjectResponse, PaginatedProjectResponse, PaginationMeta,
)
from governance.services import projects as project_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Projects"])


@router.get("/projects", response_model=PaginatedProjectResponse)
def list_projects(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List all projects with pagination."""
    result = project_service.list_projects(limit=limit, offset=offset)
    items = [ProjectResponse(**p) if isinstance(p, dict) else p for p in result["items"]]
    return PaginatedProjectResponse(
        items=items,
        pagination=PaginationMeta(**result["pagination"]),
    )


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(data: ProjectCreate):
    """Create a new project."""
    result = project_service.create_project(
        project_id=data.project_id,
        name=data.name,
        path=data.path,
    )
    if not result:
        raise HTTPException(status_code=409, detail="Project already exists")
    return ProjectResponse(**result) if isinstance(result, dict) else result


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str):
    """Get a single project by ID."""
    result = project_service.get_project(project_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return ProjectResponse(**result) if isinstance(result, dict) else result


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: str):
    """Delete a project."""
    deleted = project_service.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")


@router.post("/projects/{project_id}/sessions/{session_id}", status_code=201)
def link_session_to_project(project_id: str, session_id: str):
    """Link a session to a project."""
    linked = project_service.link_session_to_project(project_id, session_id)
    if not linked:
        raise HTTPException(status_code=400, detail="Failed to link session to project")
    return {"status": "linked", "project_id": project_id, "session_id": session_id}
