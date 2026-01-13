"""
TypeDB Entity Data Classes.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-003: Extracted from client.py.

Created: 2024-12-28
"""

from dataclasses import dataclass, asdict
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
    """Task entity for P10 TypeDB migration. Per GAP-ARCH-001."""
    id: str
    name: str
    status: str
    phase: str
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
class InferenceResult:
    """Result from inference query."""
    query: str
    results: List[Dict[str, Any]]
    count: int
    inference_used: bool
