"""Task models. Per GAP-UI-046, WORKFLOW-SEQ-01-v1, ORCH-007."""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Literal, Optional


class TaskCreate(BaseModel):
    """Request model for creating a task."""
    task_id: Optional[str] = Field(default=None, description="Task ID (auto-generated from task_type if omitted)")
    description: str = Field(..., min_length=1)
    phase: str = Field(..., min_length=1)
    status: str = "TODO"
    priority: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = None  # BUG-TASK-TAXONOMY-001
    task_type: Optional[Literal["bug", "feature", "chore", "research", "gap", "epic", "test", "specification", "spec"]] = None  # META-TAXON-01-v1 + SRVJ-FEAT-003
    agent_id: Optional[str] = None
    body: Optional[str] = None
    summary: Optional[str] = None  # Phase 9c: structured one-line intent
    linked_rules: Optional[List[str]] = None
    linked_sessions: Optional[List[str]] = None
    linked_documents: Optional[List[str]] = None  # Task document management
    gap_id: Optional[str] = None
    workspace_id: Optional[str] = None  # BUG-WS-API-001: workspace assignment

class TaskUpdate(BaseModel):
    """Request model for updating a task (GAP-UI-107)."""
    description: Optional[str] = None
    phase: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = None  # BUG-TASK-TAXONOMY-001
    task_type: Optional[Literal["bug", "feature", "chore", "research", "gap", "epic", "test", "specification", "spec"]] = None  # META-TAXON-01-v1 + SRVJ-FEAT-003
    agent_id: Optional[str] = None
    body: Optional[str] = None
    summary: Optional[str] = None  # Phase 9c: structured one-line intent
    linked_rules: Optional[List[str]] = None
    linked_sessions: Optional[List[str]] = None
    linked_documents: Optional[List[str]] = None  # Task document management
    gap_id: Optional[str] = None
    workspace_id: Optional[str] = None  # BUG-WS-API-001: workspace assignment
    evidence: Optional[str] = None  # Per EPIC-DR-008
    resolution_notes: Optional[str] = None  # P17: resolution narrative

class TaskResponse(BaseModel):
    """Response model for a task. Per GAP-UI-046, WORKFLOW-SEQ-01-v1."""
    task_id: str
    description: str
    phase: str
    status: str  # OPEN, IN_PROGRESS, CLOSED (or legacy: TODO, IN_PROGRESS, DONE)
    resolution: Optional[str] = None  # NONE, DEFERRED, IMPLEMENTED, VALIDATED, CERTIFIED
    priority: Optional[str] = None  # BUG-TASK-TAXONOMY-001: LOW, MEDIUM, HIGH, CRITICAL
    task_type: Optional[str] = None  # BUG-TASK-TAXONOMY-001: bug, feature, chore, research
    summary: Optional[str] = None  # Phase 9c: structured one-line intent
    agent_id: Optional[str] = None
    created_at: Optional[str] = None
    claimed_at: Optional[str] = None
    completed_at: Optional[str] = None
    body: Optional[str] = None
    linked_rules: Optional[List[str]] = None
    linked_sessions: Optional[List[str]] = None
    linked_commits: Optional[List[str]] = None  # Per GAP-TASK-LINK-002: Git commit linkage
    linked_documents: Optional[List[str]] = None  # Task document management
    gap_id: Optional[str] = None
    evidence: Optional[str] = None  # May include [Verification: L1/L2/L3] prefix
    document_path: Optional[str] = None
    workspace_id: Optional[str] = None  # EPIC-GOV-TASKS-V2 Phase 4
    resolution_notes: Optional[str] = None  # P17: resolution narrative
    warnings: Optional[List[str]] = None  # P16: duplicate detection warnings

class TaskDetailsUpdate(BaseModel):
    """Request model for updating task detail sections (TASK-TECH-01-v1)."""
    business: Optional[str] = Field(default=None, description="Business context (Why)")
    design: Optional[str] = Field(default=None, description="Design/requirements (What)")
    architecture: Optional[str] = Field(default=None, description="Architecture (How)")
    test_section: Optional[str] = Field(default=None, description="Test plan (Verification)")

class TaskDetailsResponse(BaseModel):
    """Response model for task detail sections (TASK-TECH-01-v1)."""
    task_id: str
    business: Optional[str] = None
    design: Optional[str] = None
    architecture: Optional[str] = None
    test_section: Optional[str] = None

class TaskExecutionEvent(BaseModel):
    """Task execution event for execution log (ORCH-007)."""
    event_id: str
    task_id: str
    event_type: str  # claimed, started, progress, delegated, completed, failed, evidence
    timestamp: str
    agent_id: Optional[str] = None
    message: str = ""
    details: Optional[Dict[str, Any]] = None

class TaskExecutionResponse(BaseModel):
    """Response model for task execution history (ORCH-007)."""
    task_id: str
    events: List[TaskExecutionEvent] = []
    current_status: str = "pending"
    current_agent: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
