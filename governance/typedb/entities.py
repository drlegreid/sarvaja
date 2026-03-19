"""
TypeDB Entity Data Classes.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-003: Extracted from client.py.

Created: 2024-12-28
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class Rule:
    """Governance rule entity."""
    id: str
    name: str
    category: str
    priority: str
    status: str  # ACTIVE, PROPOSED, DISABLED
    directive: str
    rule_type: Optional[str] = None  # FOUNDATIONAL, OPERATIONAL, TECHNICAL, META, LEAF
    semantic_id: Optional[str] = None  # META-TAXON-01-v1: e.g., SESSION-EVID-01-v1
    applicability: Optional[str] = None  # RD-RULE-APPLICABILITY: MANDATORY|RECOMMENDED|FORBIDDEN|CONDITIONAL
    created_date: Optional[datetime] = None


@dataclass
class Decision:
    """Strategic decision entity."""
    id: str
    name: str
    context: str
    rationale: str
    status: str
    decision_date: Optional[datetime] = None


@dataclass
class Task:
    """Task entity for P10 TypeDB migration. Per GAP-ARCH-001, GAP-UI-046, GAP-GAPS-TASKS-001."""
    id: str
    name: str
    status: str  # GAP-UI-046: OPEN, IN_PROGRESS, CLOSED (lifecycle)
    phase: str
    resolution: str = "NONE"  # GAP-UI-046: NONE, DEFERRED, IMPLEMENTED, VALIDATED, CERTIFIED
    priority: Optional[str] = None  # BUG-TASK-TAXONOMY-001: LOW, MEDIUM, HIGH, CRITICAL
    task_type: Optional[str] = None  # BUG-TASK-TAXONOMY-001: bug, feature, chore, research
    description: Optional[str] = None
    body: Optional[str] = None
    agent_id: Optional[str] = None
    gap_id: Optional[str] = None
    linked_rules: Optional[List[str]] = None
    linked_sessions: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    claimed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    evidence: Optional[str] = None
    # GAP-TASK-LINK-002: Git commit linking
    linked_commits: Optional[List[str]] = None
    # GAP-TASK-LINK-004: Task detail sections (per TASK-TECH-01-v1)
    business: Optional[str] = None  # Why - User problem, business value
    design: Optional[str] = None  # What - Functional requirements, acceptance criteria
    architecture: Optional[str] = None  # How - Technical approach, technology choices
    test_section: Optional[str] = None  # Verification - Test plan, evidence
    # GAP-TASK-LINK-003: Task relationships
    parent_task: Optional[str] = None
    child_tasks: Optional[List[str]] = None
    blocks: Optional[List[str]] = None
    blocked_by: Optional[List[str]] = None
    related_tasks: Optional[List[str]] = None
    # GAP-GAPS-TASKS-001: Unified work item attributes
    item_type: Optional[str] = None  # "gap", "task", or "rd"
    document_path: Optional[str] = None  # Path to source document
    # Task document management: multiple linked documents
    linked_documents: Optional[List[str]] = None


@dataclass
class Session:
    """Work session entity for P10.2 TypeDB migration. Per GAP-ARCH-002."""
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    file_path: Optional[str] = None
    status: str = "ACTIVE"
    tasks_completed: int = 0
    agent_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    linked_rules_applied: Optional[List[str]] = None
    linked_decisions: Optional[List[str]] = None
    evidence_files: Optional[List[str]] = None
    # Claude Code session attributes (SESSION-CC-01-v1)
    cc_session_uuid: Optional[str] = None
    cc_project_slug: Optional[str] = None
    cc_git_branch: Optional[str] = None
    cc_tool_count: Optional[int] = None
    cc_thinking_chars: Optional[int] = None
    cc_compaction_count: Optional[int] = None
    cc_external_name: Optional[str] = None
    project_id: Optional[str] = None


@dataclass
class Project:
    """Project entity — top-level organizational unit. Per GOV-PROJECT-01-v1."""
    id: str
    name: str
    path: Optional[str] = None
    plan_ids: Optional[List[str]] = None
    session_ids: Optional[List[str]] = None


@dataclass
class Plan:
    """Plan entity — a planned body of work within a project. Per GOV-PROJECT-01-v1."""
    id: str
    name: str
    description: Optional[str] = None
    project_id: Optional[str] = None
    epic_ids: Optional[List[str]] = None


@dataclass
class Epic:
    """Epic entity — a large feature/initiative within a plan. Per GOV-PROJECT-01-v1."""
    id: str
    name: str
    description: Optional[str] = None
    plan_id: Optional[str] = None
    task_ids: Optional[List[str]] = None


@dataclass
class Agent:
    """Agent entity for P10.3 TypeDB integration. Per GAP-ARCH-003."""
    id: str
    name: str
    agent_type: str
    status: str = "ACTIVE"
    trust_score: float = 0.8
    compliance_rate: float = 0.9
    accuracy_rate: float = 0.85
    tenure_days: int = 0
    tasks_executed: int = 0
    last_active: Optional[datetime] = None


@dataclass
class Workspace:
    """Workspace entity — organizational context within a project.

    Completes the chain: Project → Workspace → Agent → Capabilities → Tasks → Sessions.
    """
    id: str
    name: str
    workspace_type: str  # "governance", "gamedev", "video", "financial", "ml", "generic"
    project_id: Optional[str] = None
    description: Optional[str] = None
    status: str = "active"  # "active", "archived"
    created_at: Optional[datetime] = None
    agent_ids: Optional[List[str]] = None
    rule_ids: Optional[List[str]] = None


@dataclass
class Capability:
    """Capability — binding of a rule to an agent.

    Represents which rules govern which agents and in what category.
    This is the critical link between rules and agents.
    """
    agent_id: str
    rule_id: str
    category: str = "general"  # "coding", "testing", "governance", "research"
    status: str = "active"  # "active", "suspended"


@dataclass
class InferenceResult:
    """Result from inference query."""
    query: str
    results: List[Dict[str, Any]]
    count: int
    inference_used: bool
