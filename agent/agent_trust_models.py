"""
Agent Trust Models.

Per DOC-SIZE-01-v1: Extracted from agent_trust.py (437 lines).
Dataclasses for action records and compliance status.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ActionRecord:
    """Record of an agent action."""
    agent_id: str
    action: str
    compliant: bool
    timestamp: str
    trust_delta: float


@dataclass
class ComplianceStatus:
    """Compliance status for an agent."""
    agent_id: str
    compliant: bool
    rules: List[str]
    violations: List[str]
    last_check: str
