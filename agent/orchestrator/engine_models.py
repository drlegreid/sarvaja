"""
Orchestrator Engine Models.

Per DOC-SIZE-01-v1: Extracted from engine.py (478 lines).
Enums and dataclasses for agent roles, info, and dispatch results.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class AgentRole(Enum):
    """Agent role types for dispatch."""
    ORCHESTRATOR = "orchestrator"
    RESEARCH = "research"
    CODING = "coding"
    CURATOR = "curator"
    SYNC = "sync"


@dataclass
class AgentInfo:
    """Agent registration info."""
    agent_id: str
    name: str
    role: AgentRole
    trust_score: float
    status: str = "AVAILABLE"
    current_task: Optional[str] = None
    tasks_completed: int = 0

    @property
    def trust_level(self) -> str:
        """Get trust level string per RULE-011."""
        if self.trust_score >= 0.9:
            return "expert"
        elif self.trust_score >= 0.7:
            return "trusted"
        elif self.trust_score >= 0.5:
            return "supervised"
        else:
            return "restricted"


@dataclass
class DispatchResult:
    """Result of task dispatch."""
    success: bool
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    message: str = ""
    requires_supervisor: bool = False
    constraints_checked: List[str] = None

    def __post_init__(self):
        if self.constraints_checked is None:
            self.constraints_checked = []
