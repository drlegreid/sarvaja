"""
Workflow Data Loader Controllers.

Per DOC-SIZE-01-v1: Extracted from data_loaders.py (770→<300 lines).
Per RULE-012: Single Responsibility - only workflow/proposal triggers.

Provides:
- load_workflow_status: Compliance checks from TypeDB
- submit_proposal: Governance proposal via LangGraph
"""

import httpx
from typing import Any

from agent.governance_ui.trace_bar.transforms import (
    add_api_trace,
    add_error_trace,
)


def register_workflow_loader_controllers(
    state: Any,
    ctrl: Any,
    api_base_url: str
) -> dict:
    """
    Register workflow data loading controllers with Trame.

    Returns:
        Dict with 'load_workflow_status' loader function.
    """

    def load_workflow_status():
        """Load workflow compliance status. Per UI-AUDIT-009: Real TypeDB validation."""
        try:
            from governance.workflow_compliance import (
                run_compliance_checks,
                format_compliance_for_ui,
            )

            report = run_compliance_checks()
            ui_data = format_compliance_for_ui(report)

            state.workflow_status = ui_data["status"]

            checks = []
            for check in ui_data["checks"]:
                checks.append({
                    'rule_id': check.get('rule_id', ''),
                    'check_name': check.get('check_name', ''),
                    'status': check.get('status', 'UNKNOWN'),
                    'message': check.get('message', '')
                })
            state.workflow_checks = checks

            state.workflow_violations = ui_data["violations"]
            state.workflow_recommendations = ui_data["recommendations"]

        except Exception as e:
            state.workflow_status = {'overall': 'ERROR', 'passed': 0, 'failed': 0, 'warnings': 0}
            state.workflow_checks = []
            state.workflow_violations = []
            state.workflow_recommendations = [f"Compliance check failed: {e}"]

        state.workflow_loading = False

    @ctrl.trigger("load_workflow_status")
    def trigger_load_workflow_status():
        """Trigger for loading workflow status + proposal info."""
        state.workflow_loading = True
        load_workflow_status()
        # Also load proposal workflow info and history
        try:
            resp = httpx.get(f"{api_base_url}/api/proposals/workflow-info", timeout=10.0)
            add_api_trace(state, "/api/proposals/workflow-info", "GET", resp.status_code, 0)
            if resp.status_code == 200:
                state.workflow_info = resp.json()
        except Exception as e:
            add_error_trace(state, f"Load workflow info failed: {e}", "/api/proposals/workflow-info")
        try:
            resp = httpx.get(f"{api_base_url}/api/proposals/history", timeout=10.0)
            add_api_trace(state, "/api/proposals/history", "GET", resp.status_code, 0)
            if resp.status_code == 200:
                state.proposal_history = resp.json().get("items", [])
        except Exception as e:
            add_error_trace(state, f"Load proposal history failed: {e}", "/api/proposals/history")

    @ctrl.trigger("submit_proposal")
    def trigger_submit_proposal():
        """Submit a governance proposal through LangGraph workflow."""
        state.proposal_submitting = True
        try:
            evidence = [e.strip() for e in (state.proposal_evidence or "").split(",") if e.strip()]
            body = {
                "action": state.proposal_action or "create",
                "hypothesis": state.proposal_hypothesis or "",
                "evidence": evidence or ["no evidence provided"],
                "rule_id": state.proposal_rule_id or None,
                "directive": state.proposal_directive or None,
                "dry_run": state.proposal_dry_run if hasattr(state, 'proposal_dry_run') else True,
            }
            resp = httpx.post(f"{api_base_url}/api/proposals/submit", json=body, timeout=30.0)
            add_api_trace(state, "/api/proposals/submit", "POST", resp.status_code, 0, request_body=body)
            if resp.status_code == 200:
                state.proposal_result = resp.json()
                hist = httpx.get(f"{api_base_url}/api/proposals/history", timeout=10.0)
                if hist.status_code == 200:
                    state.proposal_history = hist.json().get("items", [])
            else:
                state.proposal_result = {"decision": "error", "decision_reasoning": resp.text}
        except Exception as e:
            add_error_trace(state, f"Submit proposal failed: {e}", "/api/proposals/submit")
            state.proposal_result = {"decision": "error", "decision_reasoning": str(e)}
        state.proposal_submitting = False

    return {'load_workflow_status': load_workflow_status}
