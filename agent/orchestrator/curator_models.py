"""
Rules Curator Agent Models.

Per DOC-SIZE-01-v1: Extracted from curator_agent.py (588 lines).
Enums and dataclasses for curation actions, issues, and resolutions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class CurationAction(Enum):
    """Types of curation actions."""
    ANALYZE_QUALITY = "analyze_quality"
    RESOLVE_CONFLICT = "resolve_conflict"
    FIND_ORPHANS = "find_orphans"
    CHECK_DEPENDENCIES = "check_dependencies"
    VALIDATE_RULE = "validate_rule"
    PROPOSE_CHANGE = "propose_change"


class IssueSeverity(Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RuleIssue:
    """A detected issue with a rule."""
    issue_id: str
    rule_id: str
    issue_type: str
    severity: IssueSeverity
    description: str
    recommendation: str
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved: bool = False
    resolved_at: Optional[str] = None


@dataclass
class CurationResult:
    """Result of a curation action."""
    action: CurationAction
    success: bool
    issues_found: List[RuleIssue] = field(default_factory=list)
    issues_resolved: int = 0
    message: str = ""
    evidence: Optional[str] = None


@dataclass
class ConflictResolution:
    """Resolution for a rule conflict."""
    conflict_id: str
    rule_a: str
    rule_b: str
    resolution_type: str  # "merge", "deprecate", "update", "escalate"
    rationale: str
    proposed_changes: Dict[str, Any] = field(default_factory=dict)
