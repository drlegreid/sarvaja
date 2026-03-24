"""Rule models. Per RULE-012, GAP-MCP-008."""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class RuleCreate(BaseModel):
    """Request model for creating a rule."""
    rule_id: str = Field(..., min_length=1, description="Unique rule ID (e.g., RULE-025)")
    name: str = Field(..., min_length=1, description="Rule name/title")
    category: Literal["governance", "technical", "operational"] = Field(..., description="Category")
    priority: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = Field(..., description="Priority")
    directive: str = Field(..., min_length=1, description="Rule directive text")
    status: Literal["DRAFT", "ACTIVE", "DEPRECATED"] = Field(default="DRAFT", description="Status")
    # RD-WORKSPACE Phase 3: Skill tags and applicable roles
    tags: Optional[str] = Field(default=None, description="Comma-separated skill tags")
    applicable_roles: Optional[str] = Field(default=None, description="Comma-separated agent roles")

class RuleUpdate(BaseModel):
    """Request model for updating a rule."""
    name: Optional[str] = None
    category: Optional[Literal["governance", "technical", "operational"]] = None
    priority: Optional[Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]] = None
    directive: Optional[str] = None
    status: Optional[Literal["DRAFT", "ACTIVE", "DEPRECATED"]] = None

class RuleResponse(BaseModel):
    """Response model for a rule. Per GAP-MCP-008: includes semantic_id."""
    id: str  # Legacy ID: RULE-XXX
    semantic_id: Optional[str] = None  # Semantic ID: DOMAIN-SUB-NN-vN
    name: str
    category: str
    priority: str
    status: str
    directive: str
    created_date: Optional[str] = None
    document_path: Optional[str] = None  # Per GAP-UI-AUDIT-001: Rule-document linkage
    applicability: Optional[str] = None  # Per RD-RULE-APPLICABILITY: MANDATORY|RECOMMENDED|FORBIDDEN|CONDITIONAL
    linked_tasks_count: int = 0  # Per PLAN-UI-OVERHAUL-001 Task 1.1
    linked_sessions_count: int = 0  # Per PLAN-UI-OVERHAUL-001 Task 1.1
