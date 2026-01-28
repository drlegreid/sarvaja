"""
Workflow Compliance Models.

Per DOC-SIZE-01-v1: Extracted from workflow_compliance.py (653 lines).
Per UI-AUDIT-009: Data models for compliance reporting.

Created: 2026-01-20
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional


@dataclass
class ComplianceCheck:
    """Result of a compliance check."""
    rule_id: str
    check_name: str
    status: str  # PASS | FAIL | WARNING | SKIP
    message: str
    count: int = 0
    violations: List[str] = field(default_factory=list)
    evidence: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "check_name": self.check_name,
            "status": self.status,
            "message": self.message,
            "count": self.count,
            "violations": self.violations[:10],  # Limit for UI
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ComplianceReport:
    """Full compliance report."""
    overall_status: str = "UNKNOWN"
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    checks: List[ComplianceCheck] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def add_check(self, check: ComplianceCheck) -> None:
        """Add a check and update counters."""
        self.checks.append(check)
        if check.status == "PASS":
            self.passed += 1
        elif check.status == "FAIL":
            self.failed += 1
        elif check.status == "WARNING":
            self.warnings += 1

    def finalize(self) -> None:
        """Calculate overall status after all checks."""
        if self.failed > 0:
            self.overall_status = "VIOLATIONS"
        elif self.warnings > 0:
            self.overall_status = "WARNINGS"
        elif self.passed > 0:
            self.overall_status = "COMPLIANT"
        else:
            self.overall_status = "UNKNOWN"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "checks": [c.to_dict() for c in self.checks],
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat()
        }
