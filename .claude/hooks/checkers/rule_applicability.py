"""
Rule Applicability Checker - Enforcement Level Classification
=============================================================
Per RD-RULE-APPLICABILITY: Check rules against their enforcement level.

Applicability Levels:
- MANDATORY: MUST follow - blocking if violated
- RECOMMENDED: SHOULD follow - warning if violated
- FORBIDDEN: MUST NOT do - blocking if attempted
- CONDITIONAL: Context-dependent - check preconditions

Created: 2026-01-24
"""

import json
import requests
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import re


# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
GOVERNANCE_API_URL = "http://localhost:8082"


@dataclass
class ApplicabilityCheck:
    """Result of an applicability check."""
    rule_id: str
    applicability: str  # MANDATORY | RECOMMENDED | FORBIDDEN | CONDITIONAL
    check_name: str
    status: str  # PASS | FAIL | WARNING | SKIP | BLOCK
    message: str
    context: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "applicability": self.applicability,
            "check_name": self.check_name,
            "status": self.status,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }


# Rule applicability classifications per RD-RULE-APPLICABILITY
# Cached locally to avoid API calls in hooks
MANDATORY_RULES = {
    "SESSION-EVID-01-v1": "Every session MUST create evidence log",
    "GOV-BICAM-01-v1": "Rule changes require bicameral process",
    "SAFETY-HEALTH-02-v1": "Health checks MUST pass before operations",
    "RECOVER-AMNES-02-v1": "Context recovery MUST follow protocol",
    "ARCH-VERSION-01-v1": "Version tagging MUST be consistent",
    "GOV-RULE-01-v1": "Rules MUST be stored in TypeDB",
    "ARCH-INFRA-02-v1": "Infrastructure MUST use defined stack",
    "CONTAINER-TYPEDB-01-v1": "TypeDB MUST run in container",
    "CONTAINER-LIFECYCLE-01-v1": "Containers MUST follow lifecycle",
    "WORKFLOW-SHELL-01-v1": "Use python3, not python",
    "META-TAXON-01-v1": "Semantic rule IDs required",
    "TASK-LIFE-01-v1": "Task lifecycle MUST be tracked",
    "TASK-VALID-01-v1": "Task completion requires validation",
    "ARCH-EBMSF-01-v1": "Evidence-based methodology required",
    "ARCH-MCP-02-v1": "MCP split architecture required",
}

CONDITIONAL_RULES = {
    "WORKFLOW-AUTO-02-v1": {
        "directive": "Autonomous sequencing unless HALT",
        "condition": "halt_requested",
        "when_true": "HALT - stop autonomous sequencing",
        "when_false": "Continue autonomous work"
    },
    "WORKFLOW-RD-02-v1": {
        "directive": "R&D human approval for budget/architecture",
        "condition": "impacts_budget_or_architecture",
        "when_true": "Requires human approval",
        "when_false": "Can proceed autonomously"
    },
    "SESSION-DSP-NOTIFY-01-v1": {
        "directive": "DSP prompting when entropy high",
        "condition": "entropy_high",
        "when_true": "Prompt for Deep Sleep Protocol",
        "when_false": "Continue normal operation"
    },
    "SESSION-DSM-01-v1": {
        "directive": "Deep sleep protocol for backlog hygiene",
        "condition": "backlog_needs_hygiene",
        "when_true": "Run DSM cycle",
        "when_false": "Skip DSM"
    },
}

RECOMMENDED_RULES = {
    "DOC-SOURCE-01-v1": "Prefer official documentation",
    "CONTEXT-SAVE-01-v1": "Save context periodically",
    "GAP-DOC-01-v1": "Document discovered gaps",
    "PKG-LATEST-01-v1": "Use latest stable packages",
    "UI-NAV-01-v1": "UI navigation patterns",
    "RECOVER-MEM-01-v1": "Memory recovery protocol",
    "GOV-TRUST-01-v1": "Trust score tracking",
    "GOV-PROP-01-v1": "Proposal process",
    "UI-TRAME-01-v1": "Trame UI patterns",
    "UI-LOADER-01-v1": "Loader patterns",
    "UI-TRACE-01-v1": "Trace bar patterns",
    "TASK-TECH-01-v1": "Technical task format",
    "REPORT-OBJ-01-v1": "Objective reporting",
    "UI-DESIGN-02-v1": "UI design guidelines",
    "DOC-GAP-ARCHIVE-01-v1": "Archive resolved gaps",
    "GOV-AUDIT-01-v1": "Audit trail requirements",
    "REPORT-EXEC-01-v1": "Executive report format",
}

# FORBIDDEN rules (to be defined - safety constraints)
FORBIDDEN_PATTERNS = {
    "destructive_commands": {
        "patterns": [r"rm\s+-rf\s+/", r"mkfs\.", r"dd\s+if=.*/dev/"],
        "rule_ref": "SAFETY-DESTR-01-v1",
        "message": "Destructive system commands are FORBIDDEN"
    },
    "secret_exposure": {
        "patterns": [r"API_KEY\s*=", r"PASSWORD\s*=", r"SECRET\s*="],
        "rule_ref": "SAFETY-SECRET-01-v1",
        "message": "Exposing secrets in code is FORBIDDEN"
    }
}


def check_mandatory_rules(context: Dict[str, Any] = None) -> List[ApplicabilityCheck]:
    """
    Check if session satisfies MANDATORY rules.

    Args:
        context: Current session context (services status, etc.)

    Returns:
        List of ApplicabilityCheck results
    """
    results = []
    context = context or {}

    # Check SAFETY-HEALTH-02-v1: Health checks must pass
    if "services" in context:
        services = context["services"]
        typedb_ok = services.get("typedb", {}).get("healthy", False)
        chromadb_ok = services.get("chromadb", {}).get("healthy", False)

        if not typedb_ok or not chromadb_ok:
            results.append(ApplicabilityCheck(
                rule_id="SAFETY-HEALTH-02-v1",
                applicability="MANDATORY",
                check_name="health_check_required",
                status="FAIL",
                message="MANDATORY: Services must be healthy before operations",
                context=f"TypeDB: {typedb_ok}, ChromaDB: {chromadb_ok}"
            ))
        else:
            results.append(ApplicabilityCheck(
                rule_id="SAFETY-HEALTH-02-v1",
                applicability="MANDATORY",
                check_name="health_check_required",
                status="PASS",
                message="Health checks passed",
                context=None
            ))

    # Check WORKFLOW-SHELL-01-v1: Use python3
    if "command" in context:
        cmd = context["command"]
        if re.match(r'^python\s+', cmd) and not cmd.startswith("python3"):
            results.append(ApplicabilityCheck(
                rule_id="WORKFLOW-SHELL-01-v1",
                applicability="MANDATORY",
                check_name="python3_required",
                status="FAIL",
                message="MANDATORY: Use python3, not python",
                context=cmd
            ))

    # Check SESSION-EVID-01-v1: Evidence logging
    if context.get("session_active") and not context.get("evidence_path"):
        results.append(ApplicabilityCheck(
            rule_id="SESSION-EVID-01-v1",
            applicability="MANDATORY",
            check_name="evidence_logging",
            status="WARNING",
            message="Session should have evidence logging configured",
            context=None
        ))

    return results


def check_forbidden_actions(action: str, action_type: str = "command") -> List[ApplicabilityCheck]:
    """
    Check if action is FORBIDDEN.

    Args:
        action: The action being attempted (command, code, etc.)
        action_type: Type of action (command, code, file_write)

    Returns:
        List of ApplicabilityCheck results (BLOCK status if forbidden)
    """
    results = []

    for forbidden_name, config in FORBIDDEN_PATTERNS.items():
        for pattern in config["patterns"]:
            if re.search(pattern, action, re.IGNORECASE):
                results.append(ApplicabilityCheck(
                    rule_id=config["rule_ref"],
                    applicability="FORBIDDEN",
                    check_name=forbidden_name,
                    status="BLOCK",
                    message=f"FORBIDDEN: {config['message']}",
                    context=f"Pattern matched: {pattern}"
                ))
                break

    if not results:
        results.append(ApplicabilityCheck(
            rule_id="SAFETY",
            applicability="FORBIDDEN",
            check_name="forbidden_check",
            status="PASS",
            message="No forbidden patterns detected",
            context=None
        ))

    return results


def check_conditional_rules(context: Dict[str, Any] = None) -> List[ApplicabilityCheck]:
    """
    Check CONDITIONAL rules against current context.

    Args:
        context: Current context with condition flags

    Returns:
        List of ApplicabilityCheck results with applicable rules
    """
    results = []
    context = context or {}

    for rule_id, config in CONDITIONAL_RULES.items():
        condition = config["condition"]
        condition_met = context.get(condition, False)

        if condition_met:
            results.append(ApplicabilityCheck(
                rule_id=rule_id,
                applicability="CONDITIONAL",
                check_name=f"condition_{condition}",
                status="APPLICABLE",
                message=config["when_true"],
                context=f"Condition '{condition}' is TRUE"
            ))
        else:
            results.append(ApplicabilityCheck(
                rule_id=rule_id,
                applicability="CONDITIONAL",
                check_name=f"condition_{condition}",
                status="SKIP",
                message=config["when_false"],
                context=f"Condition '{condition}' is FALSE"
            ))

    return results


def get_applicability_status(context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get comprehensive rule applicability status for healthcheck integration.

    Args:
        context: Current session context

    Returns:
        Dict with applicability summary for hooks integration
    """
    context = context or {}
    all_checks = []

    # Run all checks
    mandatory_checks = check_mandatory_rules(context)
    all_checks.extend(mandatory_checks)

    # Check for forbidden actions if command provided
    if "command" in context:
        forbidden_checks = check_forbidden_actions(context["command"])
        all_checks.extend(forbidden_checks)

    # Check conditional rules
    conditional_checks = check_conditional_rules(context)
    all_checks.extend(conditional_checks)

    # Aggregate results
    mandatory_passed = sum(1 for c in mandatory_checks if c.status == "PASS")
    mandatory_failed = sum(1 for c in mandatory_checks if c.status == "FAIL")
    mandatory_warnings = sum(1 for c in mandatory_checks if c.status == "WARNING")

    blocked = [c for c in all_checks if c.status == "BLOCK"]
    applicable = [c for c in conditional_checks if c.status == "APPLICABLE"]

    # Determine overall status
    if blocked:
        overall_status = "BLOCKED"
    elif mandatory_failed > 0:
        overall_status = "MANDATORY_VIOLATIONS"
    elif mandatory_warnings > 0:
        overall_status = "WARNINGS"
    else:
        overall_status = "COMPLIANT"

    return {
        "overall_status": overall_status,
        "mandatory": {
            "passed": mandatory_passed,
            "failed": mandatory_failed,
            "warnings": mandatory_warnings,
            "checks": [c.to_dict() for c in mandatory_checks]
        },
        "forbidden": {
            "blocked": len(blocked),
            "checks": [c.to_dict() for c in blocked]
        },
        "conditional": {
            "applicable_count": len(applicable),
            "applicable_rules": [c.to_dict() for c in applicable]
        },
        "all_checks": [c.to_dict() for c in all_checks],
        "timestamp": datetime.now().isoformat()
    }


def format_for_healthcheck(status: Dict[str, Any]) -> List[str]:
    """
    Format applicability status for healthcheck output.

    Args:
        status: Result from get_applicability_status()

    Returns:
        List of lines for healthcheck output
    """
    lines = []

    overall = status.get("overall_status", "UNKNOWN")
    mandatory = status.get("mandatory", {})
    forbidden = status.get("forbidden", {})
    conditional = status.get("conditional", {})

    lines.append("")
    lines.append("Rule Applicability:")
    lines.append(f"  Status: {overall}")

    # Mandatory summary
    m_passed = mandatory.get("passed", 0)
    m_failed = mandatory.get("failed", 0)
    m_warn = mandatory.get("warnings", 0)
    lines.append(f"  Mandatory: {m_passed} passed, {m_failed} failed, {m_warn} warnings")

    # Show violations if any
    if m_failed > 0:
        lines.append("  Mandatory Violations:")
        for check in mandatory.get("checks", []):
            if check.get("status") == "FAIL":
                lines.append(f"    - [{check['rule_id']}] {check['message']}")

    # Show blocks if any
    if forbidden.get("blocked", 0) > 0:
        lines.append("  BLOCKED Actions:")
        for check in forbidden.get("checks", []):
            lines.append(f"    - [{check['rule_id']}] {check['message']}")

    # Show applicable conditional rules
    if conditional.get("applicable_count", 0) > 0:
        lines.append(f"  Conditional Rules Triggered: {conditional['applicable_count']}")
        for rule in conditional.get("applicable_rules", [])[:3]:
            lines.append(f"    - {rule['rule_id']}: {rule['message']}")

    return lines


# Convenience function for healthcheck.py
def get_rule_applicability_summary(context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Quick summary for healthcheck integration.

    Returns:
        Dict with:
        - compliant: bool (no mandatory violations or blocks)
        - summary: str (one-liner)
        - lines: List[str] (for detailed output)
        - blocked: bool (has FORBIDDEN blocks)
    """
    status = get_applicability_status(context)

    overall = status.get("overall_status", "UNKNOWN")
    mandatory = status.get("mandatory", {})
    forbidden = status.get("forbidden", {})

    m_passed = mandatory.get("passed", 0)
    m_total = m_passed + mandatory.get("failed", 0) + mandatory.get("warnings", 0)

    summary = f"Rules: {overall} ({m_passed}/{m_total} mandatory passed)"
    if forbidden.get("blocked", 0) > 0:
        summary += f", {forbidden['blocked']} BLOCKED"

    return {
        "compliant": overall in ("COMPLIANT", "WARNINGS"),
        "blocked": forbidden.get("blocked", 0) > 0,
        "summary": summary,
        "lines": format_for_healthcheck(status),
        "raw": status
    }


# CLI for testing
if __name__ == "__main__":
    import sys

    # Test with sample context
    test_context = {
        "services": {
            "typedb": {"healthy": True},
            "chromadb": {"healthy": True}
        },
        "command": "python3 script.py",
        "entropy_high": False,
        "halt_requested": False
    }

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "check":
            result = get_applicability_status(test_context)
            print(json.dumps(result, indent=2))

        elif cmd == "summary":
            result = get_rule_applicability_summary(test_context)
            print(json.dumps(result, indent=2, default=str))

        elif cmd == "forbidden":
            test_cmd = sys.argv[2] if len(sys.argv) > 2 else "rm -rf /"
            result = check_forbidden_actions(test_cmd)
            for r in result:
                print(json.dumps(r.to_dict(), indent=2))

        else:
            print("Usage: python rule_applicability.py [check | summary | forbidden <cmd>]")
    else:
        # Default: show summary
        result = get_rule_applicability_summary(test_context)
        print(json.dumps(result, indent=2, default=str))
