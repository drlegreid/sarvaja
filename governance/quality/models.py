"""
Rule Quality Models
Created: 2024-12-24
Modularized: 2026-01-02 (RULE-032)

Enums and dataclasses for rule quality analysis.
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum


class IssueSeverity(Enum):
    """Severity levels for rule issues."""
    CRITICAL = "CRITICAL"  # Must fix immediately
    HIGH = "HIGH"          # Should fix soon
    MEDIUM = "MEDIUM"      # Fix when convenient
    LOW = "LOW"            # Minor improvement
    INFO = "INFO"          # Informational only


class IssueType(Enum):
    """Types of rule quality issues."""
    ORPHANED = "orphaned"              # No dependents
    SHALLOW = "shallow"                # Missing attributes
    OVER_CONNECTED = "over_connected"  # Too many dependencies
    UNDER_DOCUMENTED = "under_documented"  # Not in any docs
    CIRCULAR_DEPENDENCY = "circular"   # A→B→A loop
    STALE_REFERENCE = "stale_reference"  # References deprecated rule
    PRIORITY_MISMATCH = "priority_mismatch"  # Dependencies have higher priority
    MISSING_DEPENDENCY = "missing_dependency"  # Referenced rule doesn't exist


@dataclass
class RuleIssue:
    """A detected issue with a rule."""
    rule_id: str
    issue_type: IssueType
    severity: IssueSeverity
    description: str
    impact: str
    remediation: str
    related_rules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "rule_id": self.rule_id,
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "impact": self.impact,
            "remediation": self.remediation,
            "related_rules": self.related_rules,
            "metadata": self.metadata
        }


@dataclass
class RuleHealthReport:
    """Complete health report for all rules."""
    total_rules: int
    issues_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    issues: List[RuleIssue]
    healthy_rules: List[str]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_rules": self.total_rules,
            "issues_count": self.issues_count,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "issues": [i.to_dict() for i in self.issues],
            "healthy_rules": self.healthy_rules,
            "timestamp": self.timestamp
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
