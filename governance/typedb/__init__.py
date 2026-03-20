"""
TypeDB Client Package.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-003: Modular TypeDB client architecture.

This package provides a modular TypeDB client with:
- Base client with connection and query execution
- Entity data classes (Rule, Task, Session, Agent, Decision)
- Query mixins for each entity type

Created: 2024-12-28
"""

from .entities import Rule, Task, Session, Agent, Decision, InferenceResult
from .base import TypeDBBaseClient
from .queries import TaskQueries, SessionQueries, RuleQueries, AgentQueries, CapabilityQueries, WorkspaceQueries

__all__ = [
    # Entities
    "Rule",
    "Task",
    "Session",
    "Agent",
    "Decision",
    "InferenceResult",
    # Base client
    "TypeDBBaseClient",
    # Query mixins
    "TaskQueries",
    "SessionQueries",
    "RuleQueries",
    "AgentQueries",
    "CapabilityQueries",
    "WorkspaceQueries",
]
