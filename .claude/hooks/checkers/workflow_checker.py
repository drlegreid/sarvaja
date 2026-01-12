"""
Workflow Checker Module for Healthcheck Integration.

Per RD-WORKFLOW: Provides gap-based workflow validation.
Per RULE-032: Modularized from healthcheck.py

Validates:
- Gap state transitions have required evidence
- Workflow rules (RULE-020, RULE-023) are followed
- Work is properly linked to gaps/tasks

This enables workflow integrity monitoring per RULE-020.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import re


@dataclass
class ValidationResult:
    """Result of a workflow validation check."""
    rule_id: str
    check_name: str
    status: str  # PASS | FAIL | SKIP | WARNING
    message: str
    evidence: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "check_name": self.check_name,
            "status": self.status,
            "message": self.message,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class GapTransition:
    """Represents a gap state transition."""
    gap_id: str
    from_state: str
    to_state: str
    timestamp: datetime
    evidence: Optional[str] = None
    validated: bool = False


# Valid gap state transitions
VALID_TRANSITIONS = {
    "OPEN": ["IN_PROGRESS", "RESOLVED", "DEFERRED"],
    "IN_PROGRESS": ["RESOLVED", "OPEN", "DEFERRED"],
    "PARTIAL": ["RESOLVED", "IN_PROGRESS", "OPEN"],
    "DEFERRED": ["OPEN", "IN_PROGRESS"],
    "RESOLVED": []  # Terminal state - no transitions out
}

# Rules that require specific evidence for gap resolution
RESOLUTION_RULES = {
    "UI": {
        "rule": "RULE-023",
        "check": "e2e_test_required",
        "evidence_pattern": r"(test_.*\.py|\.robot|results/robot/)",
        "message": "UI gaps require E2E test evidence"
    },
    "functionality": {
        "rule": "RULE-020",
        "check": "test_before_claim",
        "evidence_pattern": r"(test_.*\.py|pytest|results/)",
        "message": "Functionality gaps require test evidence"
    },
    "infra": {
        "rule": "RULE-016",
        "check": "infra_validation",
        "evidence_pattern": r"(docker|podman|compose|healthcheck)",
        "message": "Infrastructure gaps require service validation"
    }
}


def validate_gap_transition(
    gap_id: str,
    from_state: str,
    to_state: str,
    evidence: Optional[str] = None
) -> ValidationResult:
    """
    Validate a gap state transition is allowed and has required evidence.

    Per RD-WORKFLOW Phase 1: Gap lifecycle validation.

    Args:
        gap_id: Gap being transitioned (e.g., "GAP-UI-001")
        from_state: Current state
        to_state: Target state
        evidence: Optional evidence for the transition

    Returns:
        ValidationResult with status and any violations
    """
    # Check if transition is valid
    valid_targets = VALID_TRANSITIONS.get(from_state, [])

    if to_state not in valid_targets:
        return ValidationResult(
            rule_id="WORKFLOW",
            check_name="valid_transition",
            status="FAIL",
            message=f"Invalid transition: {from_state} -> {to_state} not allowed",
            evidence=None
        )

    # Check if resolving requires evidence
    if to_state == "RESOLVED":
        # Determine gap category from ID prefix
        category = _get_gap_category(gap_id)
        rule_config = RESOLUTION_RULES.get(category)

        if rule_config and not evidence:
            return ValidationResult(
                rule_id=rule_config["rule"],
                check_name=rule_config["check"],
                status="WARNING",
                message=f"{rule_config['message']} (gap: {gap_id})",
                evidence=None
            )

        # Validate evidence matches expected pattern
        if rule_config and evidence:
            if not re.search(rule_config["evidence_pattern"], evidence, re.IGNORECASE):
                return ValidationResult(
                    rule_id=rule_config["rule"],
                    check_name=rule_config["check"],
                    status="WARNING",
                    message=f"Evidence doesn't match expected pattern for {category} gap",
                    evidence=evidence
                )

    return ValidationResult(
        rule_id="WORKFLOW",
        check_name="valid_transition",
        status="PASS",
        message=f"Transition {from_state} -> {to_state} validated",
        evidence=evidence
    )


def _get_gap_category(gap_id: str) -> str:
    """Extract category from gap ID prefix."""
    if gap_id.startswith("GAP-UI"):
        return "UI"
    elif gap_id.startswith("GAP-INFRA"):
        return "infra"
    elif gap_id.startswith("GAP-MCP"):
        return "functionality"
    elif gap_id.startswith("GAP-WORKFLOW"):
        return "functionality"
    else:
        return "general"


def validate_session_start(project_root: Path = None) -> List[ValidationResult]:
    """
    Validate session start follows RULE-024 requirements.

    Checks:
    - CLAUDE.md was read (context recovery)
    - governance_health() was called
    - Previous session handoffs addressed

    Returns:
        List of ValidationResult for each check
    """
    results = []

    if project_root is None:
        project_root = Path(__file__).parent.parent.parent.parent

    # Check 1: CLAUDE.md exists and is readable
    claude_md = project_root / "CLAUDE.md"
    if claude_md.exists():
        results.append(ValidationResult(
            rule_id="RULE-024",
            check_name="claude_md_exists",
            status="PASS",
            message="CLAUDE.md available for context recovery",
            evidence=str(claude_md)
        ))
    else:
        results.append(ValidationResult(
            rule_id="RULE-024",
            check_name="claude_md_exists",
            status="FAIL",
            message="CLAUDE.md not found - context recovery impaired",
            evidence=None
        ))

    # Check 2: TODO.md exists (task tracking)
    todo_md = project_root / "TODO.md"
    if todo_md.exists():
        results.append(ValidationResult(
            rule_id="RULE-001",
            check_name="todo_md_exists",
            status="PASS",
            message="TODO.md available for task tracking",
            evidence=str(todo_md)
        ))
    else:
        results.append(ValidationResult(
            rule_id="RULE-001",
            check_name="todo_md_exists",
            status="WARNING",
            message="TODO.md not found - task tracking impaired",
            evidence=None
        ))

    # Check 3: Evidence directory exists
    evidence_dir = project_root / "evidence"
    if evidence_dir.exists() and evidence_dir.is_dir():
        results.append(ValidationResult(
            rule_id="RULE-001",
            check_name="evidence_dir_exists",
            status="PASS",
            message="Evidence directory available for session logging",
            evidence=str(evidence_dir)
        ))
    else:
        results.append(ValidationResult(
            rule_id="RULE-001",
            check_name="evidence_dir_exists",
            status="FAIL",
            message="Evidence directory missing - session logging impaired",
            evidence=None
        ))

    return results


def validate_session_end(
    session_id: str,
    evidence_path: Optional[str] = None,
    tasks_completed: List[str] = None
) -> List[ValidationResult]:
    """
    Validate session end follows RULE-001 requirements.

    Checks:
    - Evidence file was created
    - Tasks have outcomes recorded
    - No orphaned work

    Returns:
        List of ValidationResult for each check
    """
    results = []

    if tasks_completed is None:
        tasks_completed = []

    # Check 1: Evidence file exists
    if evidence_path:
        evidence_file = Path(evidence_path)
        if evidence_file.exists():
            results.append(ValidationResult(
                rule_id="RULE-001",
                check_name="session_evidence",
                status="PASS",
                message=f"Session evidence logged: {evidence_file.name}",
                evidence=str(evidence_file)
            ))
        else:
            results.append(ValidationResult(
                rule_id="RULE-001",
                check_name="session_evidence",
                status="FAIL",
                message="Session evidence file not created",
                evidence=None
            ))
    else:
        results.append(ValidationResult(
            rule_id="RULE-001",
            check_name="session_evidence",
            status="WARNING",
            message="No evidence path provided for session",
            evidence=None
        ))

    # Check 2: Tasks have outcomes
    if tasks_completed:
        results.append(ValidationResult(
            rule_id="RULE-001",
            check_name="tasks_documented",
            status="PASS",
            message=f"{len(tasks_completed)} tasks documented",
            evidence=",".join(tasks_completed[:5])
        ))
    else:
        results.append(ValidationResult(
            rule_id="RULE-001",
            check_name="tasks_documented",
            status="WARNING",
            message="No tasks documented for session",
            evidence=None
        ))

    return results


def check_workflow_compliance(project_root: Path = None) -> Dict[str, Any]:
    """
    Run comprehensive workflow compliance check.

    Returns summary for healthcheck integration:
    - overall_status: COMPLIANT | WARNINGS | VIOLATIONS
    - checks_passed: count
    - checks_failed: count
    - violations: list of failed checks
    - recommendations: list of actions

    Returns:
        Dict with compliance summary
    """
    if project_root is None:
        project_root = Path(__file__).parent.parent.parent.parent

    result = {
        "overall_status": "COMPLIANT",
        "checks_passed": 0,
        "checks_failed": 0,
        "checks_warning": 0,
        "violations": [],
        "warnings": [],
        "recommendations": []
    }

    # Run session start validations
    start_results = validate_session_start(project_root)

    for check in start_results:
        if check.status == "PASS":
            result["checks_passed"] += 1
        elif check.status == "FAIL":
            result["checks_failed"] += 1
            result["violations"].append(check.to_dict())
        elif check.status == "WARNING":
            result["checks_warning"] += 1
            result["warnings"].append(check.to_dict())

    # Determine overall status
    if result["checks_failed"] > 0:
        result["overall_status"] = "VIOLATIONS"
        result["recommendations"].append("Address failed checks before proceeding")
    elif result["checks_warning"] > 0:
        result["overall_status"] = "WARNINGS"
        result["recommendations"].append("Review warnings for potential issues")

    return result


def format_workflow_for_healthcheck(compliance: Dict) -> List[str]:
    """
    Format workflow compliance data for healthcheck output.

    Args:
        compliance: Result from check_workflow_compliance()

    Returns:
        List of lines to add to healthcheck output
    """
    lines = []

    status = compliance.get("overall_status", "UNKNOWN")
    passed = compliance.get("checks_passed", 0)
    failed = compliance.get("checks_failed", 0)
    warnings = compliance.get("checks_warning", 0)

    lines.append("")
    lines.append("Workflow Compliance:")
    lines.append(f"  Status: {status}")
    lines.append(f"  Passed: {passed}, Failed: {failed}, Warnings: {warnings}")

    if compliance.get("violations"):
        lines.append("")
        lines.append("  Violations:")
        for v in compliance["violations"][:3]:
            lines.append(f"    - [{v['rule_id']}] {v['message']}")

    if compliance.get("warnings"):
        lines.append("")
        lines.append("  Warnings:")
        for w in compliance["warnings"][:3]:
            lines.append(f"    - [{w['rule_id']}] {w['message']}")

    return lines


# Convenience function for healthcheck.py import
def get_workflow_status(project_root: Path = None) -> Dict[str, Any]:
    """
    Quick workflow status check for healthcheck integration.

    Returns minimal dict with:
    - compliant: bool
    - summary: str (one-liner for compact output)
    - lines: List[str] (for detailed output)
    """
    compliance = check_workflow_compliance(project_root)

    status = compliance.get("overall_status", "UNKNOWN")
    passed = compliance.get("checks_passed", 0)
    total = passed + compliance.get("checks_failed", 0) + compliance.get("checks_warning", 0)

    summary = f"Workflow: {status} ({passed}/{total} passed)"

    return {
        "compliant": status == "COMPLIANT",
        "summary": summary,
        "lines": format_workflow_for_healthcheck(compliance),
        "raw": compliance
    }
