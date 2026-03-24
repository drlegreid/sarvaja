"""Project hierarchy models. Per GOV-PROJECT-01-v1."""

from pydantic import BaseModel, Field
from typing import List, Optional

from .common import PaginationMeta


class ProjectCreate(BaseModel):
    """Request model for creating a project."""
    project_id: Optional[str] = None  # Auto-generate if empty
    name: str = Field(..., min_length=1)
    path: Optional[str] = None
    project_type: str = "generic"  # Workspace type from registry

class ProjectResponse(BaseModel):
    """Response model for a project."""
    project_id: str
    name: str
    path: Optional[str] = None
    project_type: str = "generic"
    plan_count: int = 0
    session_count: int = 0

class PlanCreate(BaseModel):
    """Request model for creating a plan."""
    plan_id: Optional[str] = None
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    project_id: str = Field(..., min_length=1)

class PlanResponse(BaseModel):
    """Response model for a plan."""
    plan_id: str
    name: str
    description: Optional[str] = None
    project_id: Optional[str] = None
    epic_count: int = 0

class EpicCreate(BaseModel):
    """Request model for creating an epic."""
    epic_id: Optional[str] = None
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    plan_id: str = Field(..., min_length=1)

class EpicResponse(BaseModel):
    """Response model for an epic."""
    epic_id: str
    name: str
    description: Optional[str] = None
    plan_id: Optional[str] = None
    task_count: int = 0

class PaginatedProjectResponse(BaseModel):
    """Paginated project list response."""
    items: List[ProjectResponse]
    pagination: PaginationMeta
