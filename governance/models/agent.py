"""Agent models. Per GAP-AGENT-004, GAP-UI-048."""

from pydantic import BaseModel
from typing import List, Optional


class AgentCreate(BaseModel):
    """Request model for creating a new agent."""
    agent_id: str
    name: str
    agent_type: str = "custom"
    trust_score: float = 0.8
    capabilities: List[str] = []
    rules: List[str] = []

class AgentResponse(BaseModel):
    """Response model for an agent."""
    agent_id: str
    name: str
    agent_type: str
    status: str
    tasks_executed: int = 0
    trust_score: float = 0.0
    last_active: Optional[str] = None
    # Capabilities per GAP-AGENT-004
    capabilities: List[str] = []
    # Relations (GAP-UI-048)
    recent_sessions: List[str] = []
    active_tasks: List[str] = []

class AgentTaskAssign(BaseModel):
    """Request model for assigning a task to an agent."""
    task_id: str
