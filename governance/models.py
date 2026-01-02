"""
Governance API Pydantic Models.

Per RULE-012: DSP Semantic Code Structure - extracted from api.py.
Per GAP-FILE-002: API modularization.

Created: 2024-12-28
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# =============================================================================
# RULE MODELS
# =============================================================================

class RuleCreate(BaseModel):
    """Request model for creating a rule."""
    rule_id: str = Field(..., description="Unique rule ID (e.g., RULE-025)")
    name: str = Field(..., description="Rule name/title")
    category: str = Field(..., description="Category: governance, technical, operational")
    priority: str = Field(..., description="Priority: CRITICAL, HIGH, MEDIUM, LOW")
    directive: str = Field(..., description="Rule directive text")
    status: str = Field(default="DRAFT", description="Status: DRAFT, ACTIVE, DEPRECATED")


class RuleUpdate(BaseModel):
    """Request model for updating a rule."""
    name: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    directive: Optional[str] = None
    status: Optional[str] = None


class RuleResponse(BaseModel):
    """Response model for a rule."""
    id: str
    name: str
    category: str
    priority: str
    status: str
    directive: str
    created_date: Optional[str] = None


# =============================================================================
# TASK MODELS
# =============================================================================

class TaskCreate(BaseModel):
    """Request model for creating a task."""
    task_id: str
    description: str
    phase: str
    status: str = "TODO"
    agent_id: Optional[str] = None
    body: Optional[str] = None
    linked_rules: Optional[List[str]] = None
    linked_sessions: Optional[List[str]] = None
    gap_id: Optional[str] = None


class TaskUpdate(BaseModel):
    """Request model for updating a task (GAP-UI-107)."""
    description: Optional[str] = None
    phase: Optional[str] = None
    status: Optional[str] = None
    agent_id: Optional[str] = None
    body: Optional[str] = None
    linked_rules: Optional[List[str]] = None
    linked_sessions: Optional[List[str]] = None
    gap_id: Optional[str] = None


class TaskResponse(BaseModel):
    """Response model for a task."""
    task_id: str
    description: str
    phase: str
    status: str
    agent_id: Optional[str] = None
    created_at: Optional[str] = None
    claimed_at: Optional[str] = None
    completed_at: Optional[str] = None
    body: Optional[str] = None
    linked_rules: Optional[List[str]] = None
    linked_sessions: Optional[List[str]] = None
    gap_id: Optional[str] = None
    evidence: Optional[str] = None


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


# =============================================================================
# DECISION MODELS (GAP-UI-033)
# =============================================================================

class DecisionCreate(BaseModel):
    """Request model for creating a decision."""
    decision_id: str = Field(..., description="Unique decision ID (e.g., DECISION-010)")
    name: str = Field(..., description="Decision name/title")
    context: str = Field(..., description="Context/problem statement")
    rationale: str = Field(..., description="Reasoning for the decision")
    status: str = Field(default="PENDING", description="Status: PENDING, APPROVED, REJECTED")


class DecisionUpdate(BaseModel):
    """Request model for updating a decision."""
    name: Optional[str] = None
    context: Optional[str] = None
    rationale: Optional[str] = None
    status: Optional[str] = None


class DecisionResponse(BaseModel):
    """Response model for a decision."""
    id: str
    name: str
    context: str
    rationale: str
    status: str
    decision_date: Optional[str] = None


# =============================================================================
# SESSION MODELS
# =============================================================================

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


class SessionCreate(BaseModel):
    """Request model for creating a session."""
    session_id: Optional[str] = None  # Auto-generate if not provided
    description: str
    agent_id: Optional[str] = None


class SessionEnd(BaseModel):
    """Request model for ending a session."""
    tasks_completed: Optional[int] = None
    evidence_files: Optional[List[str]] = None


class SessionUpdate(BaseModel):
    """Request model for updating a session. Per GAP-UI-034."""
    description: Optional[str] = None
    status: Optional[str] = None
    tasks_completed: Optional[int] = None
    agent_id: Optional[str] = None


# =============================================================================
# EVIDENCE MODELS
# =============================================================================

class EvidenceResponse(BaseModel):
    """Response model for evidence."""
    evidence_id: str
    source: str
    content: str
    created_at: str
    session_id: Optional[str] = None


class FileContentResponse(BaseModel):
    """Response model for file content (GAP-DATA-003)."""
    path: str
    content: str
    size: int
    modified_at: str
    exists: bool = True


# =============================================================================
# AGENT MODELS
# =============================================================================

class AgentResponse(BaseModel):
    """Response model for an agent."""
    agent_id: str
    name: str
    agent_type: str
    status: str
    tasks_executed: int = 0
    trust_score: float = 0.0
    last_active: Optional[str] = None


class AgentTaskAssign(BaseModel):
    """Request model for assigning a task to an agent."""
    task_id: str


# =============================================================================
# REPORT MODELS
# =============================================================================

class ExecutiveReportSection(BaseModel):
    """Single section of executive report."""
    title: str
    content: str
    metrics: Optional[Dict[str, Any]] = None
    status: Optional[str] = None  # success, warning, error, info


class ExecutiveSummarySession(BaseModel):
    """Session summary for executive report."""
    session_id: str
    date: str
    tasks_completed: int
    decisions_made: int
    rules_applied: List[str]
    key_outcomes: List[str]


class ExecutiveReportResponse(BaseModel):
    """
    Executive report response per RULE-029.

    7 sections: Highlights, Compliance, Risk, Alignment, Resources, Recommendations, Objectives
    """
    report_id: str
    generated_at: str
    session_id: Optional[str] = None
    period: str  # e.g., "2024-12-27", "2024-12-25 to 2024-12-27"
    sections: List[ExecutiveReportSection]
    overall_status: str  # healthy, warning, critical
    metrics_summary: Dict[str, Any]


# =============================================================================
# CHAT MODELS
# =============================================================================

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


# =============================================================================
# API STATUS
# =============================================================================

class APIStatus(BaseModel):
    """API status response."""
    status: str
    typedb_connected: bool
    rules_count: int
    decisions_count: int
    version: str = "1.0.0"
    auth_enabled: bool = False
