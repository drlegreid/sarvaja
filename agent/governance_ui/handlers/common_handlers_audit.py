"""
Rule Detail & Audit Filter Handlers.

Per DOC-SIZE-01-v1: Extracted from common_handlers.py (404 lines).
Rule implementing tasks loader + audit trail reactive filters.
"""

import os
from typing import Any

import httpx

from ..trace_bar.transforms import add_error_trace

API_BASE_URL = os.environ.get("GOVERNANCE_API_URL", "http://localhost:8082")


def register_rule_detail_handlers(ctrl: Any, state: Any) -> None:
    """Register rule detail handlers (UI-AUDIT-003)."""

    @ctrl.trigger("load_rule_implementing_tasks")
    def load_rule_implementing_tasks() -> None:
        """
        Load tasks that implement the selected rule.

        Per UI-AUDIT-003: Rule-task traceability for dashboard.
        Per GAP-UI-AUDIT-001: Rules view should show implementing tasks.
        """
        if not state.selected_rule:
            state.rule_implementing_tasks = []
            return

        rule_id = state.selected_rule.get("id") or state.selected_rule.get("rule_id")
        if not rule_id:
            state.rule_implementing_tasks = []
            return

        try:
            state.rule_implementing_tasks_loading = True
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{API_BASE_URL}/api/rules/{rule_id}/tasks")
                if response.status_code == 200:
                    data = response.json()
                    state.rule_implementing_tasks = data.get("implementing_tasks", [])
                else:
                    state.rule_implementing_tasks = []
            state.rule_implementing_tasks_loading = False
        except Exception as e:
            add_error_trace(state, f"Load implementing tasks failed: {e}", f"/api/rules/{rule_id}/tasks")
            state.rule_implementing_tasks = []
            state.rule_implementing_tasks_loading = False

    # Auto-load implementing tasks when rule detail is shown
    @state.change("show_rule_detail")
    def on_show_rule_detail_change(show_rule_detail: bool, **kwargs) -> None:
        """Load implementing tasks when rule detail view is opened."""
        if show_rule_detail and state.selected_rule:
            load_rule_implementing_tasks()

    # Also trigger when selected_rule changes (handles state sync timing)
    @state.change("selected_rule")
    def on_selected_rule_change(selected_rule, **kwargs) -> None:
        """Load implementing tasks when a rule is selected."""
        if state.show_rule_detail and selected_rule:
            load_rule_implementing_tasks()

    # AUDIT FILTER REACTIVE HANDLERS moved to audit_loaders.py
    # where load_audit_trail() is in scope for direct function call.
    # The old handlers here used ctrl.trigger("load_audit_trail") which
    # is a decorator call, not a function invocation — that's why filters
    # didn't work (BUG-UI-AUDIT-001).
