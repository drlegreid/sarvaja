"""Pydantic Models for Workspace & Capability entities.

Per DOC-SIZE-01-v1: Separate from models.py (431 lines).
These models complete the entity chain:
Project → Workspace → Agent → Capabilities → Tasks → Sessions
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# =============================================================================
# CAPABILITY MODELS (Rule → Agent binding)
# =============================================================================

class CapabilityCreate(BaseModel):
    """Request: bind a rule to an agent."""
    agent_id: str = Field(..., min_length=1)
    rule_id: str = Field(..., min_length=1)
    category: str = Field(default="general", description="coding, testing, governance, research")


class CapabilityResponse(BaseModel):
    """Response: a rule→agent binding."""
    agent_id: str
    rule_id: str
    category: str
    status: str
    created_at: Optional[str] = None


class CapabilityStatusUpdate(BaseModel):
    """Request: update capability status."""
    status: str = Field(..., pattern="^(active|suspended)$")


class CapabilitySummaryResponse(BaseModel):
    """Response: capability summary stats."""
    total_bindings: int
    agents_with_rules: int
    rules_applied: int
    by_category: dict
    active: int
    suspended: int


# =============================================================================
# WORKSPACE MODELS
# =============================================================================

class WorkspaceCreate(BaseModel):
    """Request: create a workspace."""
    name: str = Field(..., min_length=1)
    workspace_type: str = Field(default="generic")
    project_id: Optional[str] = None
    description: Optional[str] = None
    agent_ids: Optional[List[str]] = None


class WorkspaceUpdate(BaseModel):
    """Request: update a workspace."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    agent_ids: Optional[List[str]] = None


class WorkspaceResponse(BaseModel):
    """Response: a workspace."""
    workspace_id: str
    name: str
    workspace_type: str
    project_id: Optional[str] = None
    description: Optional[str] = None
    status: str = "active"
    created_at: Optional[str] = None
    agent_ids: List[str] = []
    default_rules: List[str] = []
    capabilities: List[str] = []
    icon: str = "mdi-folder"
    color: str = "#64748b"


class WorkspaceTypeResponse(BaseModel):
    """Response: a workspace type definition."""
    type_id: str
    name: str
    description: str
    icon: str
    color: str
    mcp_servers: List[str] = []
    agent_templates: list = []
    default_rules: List[str] = []
    capabilities: List[str] = []
    commands: List[str] = []
    file_patterns: List[str] = []
    tags: List[str] = []


class WorkspaceAgentAssign(BaseModel):
    """Request: assign/remove agent from workspace."""
    agent_id: str = Field(..., min_length=1)
