"""
Workflow Compliance MCP Tools.

Per UI-AUDIT-009: Implement Workflow Compliance validation
Per BACKFILL-OPS-01-v1: MCP exposure for auditability

Tools:
- workflow_compliance_check: Run comprehensive compliance checks
- workflow_compliance_summary: Get quick compliance summary

Created: 2026-01-20
"""

import logging

from governance.mcp_tools.common import format_mcp_result

logger = logging.getLogger(__name__)


def register_workflow_compliance_tools(mcp) -> None:
    """Register workflow compliance MCP tools."""

    @mcp.tool()
    def workflow_compliance_check() -> str:
        """
        Run comprehensive workflow compliance checks.

        Per UI-AUDIT-009: Validates governance rules against TypeDB data.

        Checks:
        - TEST-FIX-01-v1: Completed tasks have evidence
        - SESSION-EVID-01-v1: Tasks linked to sessions
        - TASK-LIFE-01-v1: Tasks linked to rules
        - GOV-RULE-01-v1: Active rules count
        - RECOVER-AMNES-01-v1: Required workspace files

        Returns:
            JSON with full compliance report
        """
        try:
            from governance.workflow_compliance import run_compliance_checks

            report = run_compliance_checks()
            return format_mcp_result(report.to_dict())

        # BUG-370-WFC-001: Log full error but return only type name
        except Exception as e:
            logger.error(f"workflow_compliance_check failed: {e}", exc_info=True)
            return format_mcp_result({"error": f"workflow_compliance_check failed: {type(e).__name__}"})

    @mcp.tool()
    def workflow_compliance_summary() -> str:
        """
        Get quick workflow compliance summary.

        Per UI-AUDIT-009: Quick status check.

        Returns:
            JSON with overall status and counts
        """
        try:
            from governance.workflow_compliance import (
                run_compliance_checks,
                format_compliance_for_ui,
            )

            report = run_compliance_checks()
            ui_data = format_compliance_for_ui(report)

            return format_mcp_result({
                "status": ui_data["status"],
                "recommendation_count": len(ui_data["recommendations"]),
                "recommendations": ui_data["recommendations"][:3],
            })

        # BUG-370-WFC-001: Log full error but return only type name
        except Exception as e:
            logger.error(f"workflow_compliance_summary failed: {e}", exc_info=True)
            return format_mcp_result({"error": f"workflow_compliance_summary failed: {type(e).__name__}"})

    logger.info("Registered workflow compliance tools (2 tools)")
