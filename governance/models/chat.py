"""Chat models."""

from pydantic import BaseModel
from typing import List, Optional


class ChatMessageRequest(BaseModel):
    """Chat message request."""
    content: str
    agent_id: Optional[str] = None  # None = auto-select by orchestrator
    session_id: Optional[str] = None

class ChatMessageResponse(BaseModel):
    """Chat message response."""
    id: str
    role: str  # user, agent, system, error
    content: str
    timestamp: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    task_id: Optional[str] = None
    status: str = "complete"

class ChatSessionResponse(BaseModel):
    """Chat session response."""
    session_id: str
    messages: List[ChatMessageResponse]
    active_task_id: Optional[str] = None
    selected_agent_id: Optional[str] = None
