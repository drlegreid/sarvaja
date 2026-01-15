"""
Kanren Domain Models.

Per KAN-002: Context constraint DSL dataclasses.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentContext:
    """Agent context for constraint validation."""
    agent_id: str
    name: str
    trust_score: float
    agent_type: str


@dataclass
class TaskContext:
    """Task context for constraint validation."""
    task_id: str
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    requires_evidence: bool
    assigned_agent: Optional[str] = None


@dataclass
class RuleContext:
    """Rule context for constraint validation."""
    rule_id: str
    priority: str
    status: str
    category: str
