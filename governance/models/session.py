"""Session models. Per SESSION-CC-01-v1."""

from pydantic import BaseModel
from typing import List, Optional


class SessionResponse(BaseModel):
    """Response model for a session."""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    status: str
    tasks_completed: int = 0
    agent_id: Optional[str] = None
    description: Optional[str] = None
    file_path: Optional[str] = None
    evidence_files: Optional[List[str]] = None
    linked_rules_applied: Optional[List[str]] = None
    linked_decisions: Optional[List[str]] = None
    # Claude Code session attributes (SESSION-CC-01-v1)
    cc_session_uuid: Optional[str] = None
    cc_project_slug: Optional[str] = None
    cc_git_branch: Optional[str] = None
    cc_tool_count: Optional[int] = None
    cc_thinking_chars: Optional[int] = None
    cc_compaction_count: Optional[int] = None
    cc_external_name: Optional[str] = None
    project_id: Optional[str] = None
    # P0-2: Server-computed duration (single source of truth)
    duration: Optional[str] = None

class SessionCreate(BaseModel):
    """Request model for creating a session."""
    session_id: Optional[str] = None  # Auto-generate if not provided
    description: str
    agent_id: Optional[str] = None
    # Claude Code session attributes (SESSION-CC-01-v1)
    cc_session_uuid: Optional[str] = None
    cc_project_slug: Optional[str] = None
    cc_git_branch: Optional[str] = None
    cc_tool_count: Optional[int] = None
    cc_thinking_chars: Optional[int] = None
    cc_compaction_count: Optional[int] = None

class SessionEnd(BaseModel):
    """Request model for ending a session."""
    tasks_completed: Optional[int] = None
    evidence_files: Optional[List[str]] = None

class SessionUpdate(BaseModel):
    """Request model for updating a session. Per GAP-UI-034, SESSION-CC-01-v1."""
    description: Optional[str] = None
    status: Optional[str] = None
    tasks_completed: Optional[int] = None
    agent_id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    # Claude Code session attributes (SESSION-CC-01-v1)
    cc_session_uuid: Optional[str] = None
    cc_project_slug: Optional[str] = None
    cc_git_branch: Optional[str] = None
    cc_tool_count: Optional[int] = None
    cc_thinking_chars: Optional[int] = None
    cc_compaction_count: Optional[int] = None
