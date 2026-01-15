"""
Session Collector Data Models.

Per RULE-032: Modularized from session_collector.py (591 lines).
Contains: SessionEvent, Task, Decision dataclasses.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class SessionEvent:
    """
    Single event in a session.

    Event types:
    - prompt: User prompt/input
    - response: Assistant response
    - decision: Strategic decision recorded
    - task: Task creation/update
    - error: Error event
    - intent: Session intent (start)
    - outcome: Session outcome (end)
    - tool_call: MCP tool call with arguments (Task 2.3)
    - thought: Assistant reasoning/thinking (Task 2.3)
    """
    timestamp: str
    event_type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """Task entity for session tracking."""
    id: str
    name: str
    description: str
    status: str  # pending, in_progress, completed, blocked
    priority: str = "MEDIUM"
    created_date: Optional[str] = None


@dataclass
class Decision:
    """
    Decision entity for session tracking.

    Note: This is a local version used when TypeDB client is not available.
    When governance.client is available, use that Decision class instead.
    """
    id: str
    name: str
    context: str
    rationale: str
    status: str
    decision_date: Optional[datetime] = None


@dataclass
class SessionIntent:
    """
    Session intent captured at start.

    Per RD-INTENT: Tracks what a session intends to accomplish.
    Per SESSION-PROMPT-01-v1: Initial prompt must be captured verbatim.
    """
    goal: str  # Primary goal for the session
    source: str  # Where the goal came from: "TODO.md", "User request", "Handoff from SESSION-XXX"
    planned_tasks: list = field(default_factory=list)  # List of task IDs planned
    previous_session_id: Optional[str] = None  # Link to previous session for continuity
    initial_prompt: Optional[str] = None  # Per SESSION-PROMPT-01-v1: Verbatim user's first message
    captured_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SessionOutcome:
    """
    Session outcome captured at end.

    Per RD-INTENT: Tracks what a session accomplished.
    """
    status: str  # COMPLETE, PARTIAL, ABANDONED, DEFERRED
    achieved_tasks: list = field(default_factory=list)  # Task IDs completed
    deferred_tasks: list = field(default_factory=list)  # Task IDs deferred (with reasons)
    handoff_items: list = field(default_factory=list)  # Items for next session
    discoveries: list = field(default_factory=list)  # New gaps, R&D items discovered
    captured_at: str = field(default_factory=lambda: datetime.now().isoformat())


# Import TypeDB Decision if available
try:
    from governance.client import Decision as TypeDBDecision
    TYPEDB_AVAILABLE = True
except ImportError:
    TypeDBDecision = Decision
    TYPEDB_AVAILABLE = False


def get_decision_class():
    """Return the appropriate Decision class based on availability."""
    if TYPEDB_AVAILABLE:
        from governance.client import Decision as TypeDBDecision
        return TypeDBDecision
    return Decision
