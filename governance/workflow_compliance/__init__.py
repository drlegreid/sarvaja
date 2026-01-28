"""
Workflow Compliance Package.

Per DOC-SIZE-01-v1: Refactored from 653-line monolith to modular package.
Per UI-AUDIT-009: Workflow compliance validation system.

Package Structure:
- models.py: ComplianceCheck, ComplianceReport dataclasses
- api_client.py: REST API data fetching
- checks/: Individual compliance check modules
  - task_checks.py: Task-related compliance
  - rule_checks.py: Rule-related compliance
  - workspace_checks.py: Workspace file compliance

Created: 2026-01-20
"""

import logging
from typing import Dict, Any

from .models import ComplianceCheck, ComplianceReport
from .checks import (
    check_task_evidence_compliance,
    check_task_session_linkage,
    check_task_rule_linkage,
    check_active_rules,
    check_workspace_files,
    check_session_evidence_files,
)

logger = logging.getLogger(__name__)

__all__ = [
    "ComplianceCheck",
    "ComplianceReport",
    "run_compliance_checks",
    "format_compliance_for_ui",
]


def run_compliance_checks() -> ComplianceReport:
    """
    Run all workflow compliance checks.

    Returns full compliance report with all checks and recommendations.
    """
    report = ComplianceReport()

    checks = [
        check_workspace_files,
        check_active_rules,
        check_task_evidence_compliance,
        check_task_session_linkage,
        check_task_rule_linkage,
        check_session_evidence_files,
    ]

    for check_fn in checks:
        try:
            result = check_fn()
            report.add_check(result)
        except Exception as e:
            logger.error(f"Check {check_fn.__name__} failed: {e}")
            report.add_check(ComplianceCheck(
                rule_id="SYSTEM",
                check_name=check_fn.__name__,
                status="SKIP",
                message=f"Check failed: {e}"
            ))

    # Generate recommendations based on failures/warnings
    for check in report.checks:
        if check.status == "FAIL":
            if check.check_name == "task_evidence":
                report.recommendations.append(
                    "Add evidence to completed tasks using task_verify MCP tool"
                )
            elif check.check_name == "task_session_linkage":
                report.recommendations.append(
                    "Run backfill_execute_task_sessions to link tasks to sessions"
                )
            elif check.check_name == "workspace_files":
                report.recommendations.append(
                    "Create missing workspace files per RECOVER-AMNES-01-v1"
                )
        elif check.status == "WARNING":
            if check.check_name == "task_rule_linkage":
                report.recommendations.append(
                    "Link tasks to rules using task_link_rule MCP tool"
                )

    report.finalize()

    # Instrument: log compliance check event
    try:
        from agent.governance_ui.data_access.monitoring import log_monitor_event
        log_monitor_event(
            event_type="compliance_check",
            source="workflow-compliance",
            details={
                "overall_status": report.overall_status,
                "passed": report.passed,
                "failed": report.failed,
                "warnings": report.warnings
            },
            severity="INFO" if report.overall_status == "COMPLIANT" else "WARNING"
        )
    except Exception:
        pass  # Don't fail compliance check if monitoring fails

    return report


def format_compliance_for_ui(report: ComplianceReport) -> Dict[str, Any]:
    """
    Format compliance report for UI state consumption.
    """
    return {
        "status": {
            "overall": report.overall_status,
            "passed": report.passed,
            "failed": report.failed,
            "warnings": report.warnings,
        },
        "checks": [c.to_dict() for c in report.checks],
        "violations": [
            c.to_dict() for c in report.checks
            if c.status == "FAIL"
        ],
        "recommendations": report.recommendations,
    }
