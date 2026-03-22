"""Governance API Pydantic Models. Per RULE-012, GAP-FILE-002, GAP-MCP-008."""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any

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

# DECISION MODELS (GAP-UI-033, PLAN-UI-OVERHAUL-001 Task 4.2)

class DecisionOption(BaseModel):
    """An option considered in a decision, with pros and cons."""
    label: str = Field(..., min_length=1, description="Option name")
    pros: List[str] = Field(default_factory=list, description="Advantages")
    cons: List[str] = Field(default_factory=list, description="Disadvantages")

class DecisionCreate(BaseModel):
    """Request model for creating a decision."""
    decision_id: str = Field(..., min_length=1, description="Unique decision ID (e.g., DECISION-010)")
    name: str = Field(..., min_length=1, description="Decision name/title")
    context: str = Field(..., min_length=1, description="Context/problem statement")
    rationale: str = Field(..., min_length=1, description="Reasoning for the decision")
    status: Literal["PENDING", "APPROVED", "REJECTED"] = Field(default="PENDING", description="Status")
    options: List[DecisionOption] = Field(default_factory=list, description="Options considered")
    selected_option: Optional[str] = Field(default=None, description="Label of chosen option")
    rules_applied: List[str] = Field(default_factory=list, description="Rule IDs to link via decision-affects")

class DecisionUpdate(BaseModel):
    """Request model for updating a decision."""
    name: Optional[str] = None
    context: Optional[str] = None
    rationale: Optional[str] = None
    status: Optional[Literal["PENDING", "APPROVED", "REJECTED"]] = None
    decision_date: Optional[str] = None
    options: Optional[List[DecisionOption]] = None
    selected_option: Optional[str] = None

class DecisionResponse(BaseModel):
    """Response model for a decision."""
    id: str
    name: str
    context: str
    rationale: str
    status: str
    decision_date: Optional[str] = None
    # Per GAP-DECISION-001: Rules affected by this decision
    linked_rules: List[str] = []
    options: List[DecisionOption] = Field(default_factory=list)
    selected_option: Optional[str] = None

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

class EvidenceResponse(BaseModel):
    """Response model for evidence."""
    evidence_id: str
    source: str
    content: str
    created_at: str
    session_id: Optional[str] = None

class EvidenceSearchResult(BaseModel):
    """Single search result for evidence search (GAP-UI-009)."""
    source: str
    source_type: str
    score: float
    content: str

class EvidenceSearchResponse(BaseModel):
    """Response model for evidence search (GAP-UI-009)."""
    query: str
    results: List[EvidenceSearchResult]
    count: int
    search_method: str

class FileContentResponse(BaseModel):
    """Response model for file content (GAP-DATA-003)."""
    path: str
    content: str
    size: int
    modified_at: str
    exists: bool = True
    rendered_html: Optional[str] = None

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
    """Executive report per RULE-029. 7 sections: Highlights, Compliance, Risk, Alignment, Resources, Recommendations, Objectives."""
    report_id: str
    generated_at: str
    session_id: Optional[str] = None
    period: str  # e.g., "2024-12-27", "2024-12-25 to 2024-12-27"
    sections: List[ExecutiveReportSection]
    overall_status: str  # healthy, warning, critical
    metrics_summary: Dict[str, Any]

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

# PAGINATION (EPIC-DR-003)

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

# PROJECT HIERARCHY (GOV-PROJECT-01-v1)

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

# API STATUS

class APIStatus(BaseModel):
    """API status response."""
    status: str
    typedb_connected: bool
    rules_count: int
    decisions_count: int
    version: str = "1.0.0"
    auth_enabled: bool = False
