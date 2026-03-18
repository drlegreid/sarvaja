"""
TypeDB Query Modules.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-003: Extracted from client.py.

Created: 2024-12-28
"""

from .tasks import TaskQueries
from .sessions import SessionQueries
from .rules import RuleQueries
from .agents import AgentQueries
from .projects import ProjectQueries
from .proposals import ProposalQueries

__all__ = [
    "TaskQueries",
    "SessionQueries",
    "RuleQueries",
    "AgentQueries",
    "ProjectQueries",
    "ProposalQueries",
]
