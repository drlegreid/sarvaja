"""Common models: pagination and API status. Per EPIC-DR-003."""

from pydantic import BaseModel
from typing import List

from .rule import RuleResponse
from .task import TaskResponse
from .session import SessionResponse
from .decision import DecisionResponse
from .agent import AgentResponse


class PaginationMeta(BaseModel):
    """Pagination metadata for list endpoints. Per EPIC-DR-003."""
    total: int
    offset: int
    limit: int
    has_more: bool
    returned: int

class PaginatedRuleResponse(BaseModel):
    """Paginated rule list response."""
    items: List[RuleResponse]
    pagination: PaginationMeta

class PaginatedTaskResponse(BaseModel):
    """Paginated task list response. Per EPIC-DR-003."""
    items: List[TaskResponse]
    pagination: PaginationMeta

class PaginatedSessionResponse(BaseModel):
    """Paginated session list response."""
    items: List[SessionResponse]
    pagination: PaginationMeta

class PaginatedAgentResponse(BaseModel):
    """Paginated agent list response."""
    items: List[AgentResponse]
    pagination: PaginationMeta

class PaginatedDecisionResponse(BaseModel):
    """Paginated decision list response."""
    items: List[DecisionResponse]
    pagination: PaginationMeta

class APIStatus(BaseModel):
    """API status response."""
    status: str
    typedb_connected: bool
    rules_count: int
    decisions_count: int
    version: str = "1.0.0"
    auth_enabled: bool = False
