"""
Audit Trail Data Loader Controllers.

Per DOC-SIZE-01-v1: Extracted from data_loaders.py (770→<300 lines).
Per RULE-012: Single Responsibility - only audit trail data loading.
Per RD-DEBUG-AUDIT Phase 4: Dashboard audit trail integration.

Provides:
- load_audit_trail: Fetch audit summary + entries from API
- navigate_to_entity: Cross-view navigation from audit/monitor
"""

import httpx
from typing import Any

from agent.governance_ui.trace_bar.transforms import add_error_trace


def register_audit_loader_controllers(
    state: Any,
    ctrl: Any,
    api_base_url: str
) -> dict:
    """
    Register audit trail data loading controllers with Trame.

    Returns:
        Dict with 'load_audit_trail' loader function.
    """

    def load_audit_trail():
        """Load audit trail data from API. Per RD-DEBUG-AUDIT Phase 4."""
        try:
            summary_response = httpx.get(
                f"{api_base_url}/api/audit/summary", timeout=10.0
            )
            if summary_response.status_code == 200:
                state.audit_summary = summary_response.json()

            params = {'limit': 50}
            if state.audit_filter_entity_type:
                params['entity_type'] = state.audit_filter_entity_type
            if state.audit_filter_action_type:
                params['action_type'] = state.audit_filter_action_type
            if state.audit_filter_entity_id:
                params['entity_id'] = state.audit_filter_entity_id
            if state.audit_filter_correlation_id:
                params['correlation_id'] = state.audit_filter_correlation_id
            if getattr(state, 'audit_filter_date_from', None):
                params['date_from'] = state.audit_filter_date_from
            if getattr(state, 'audit_filter_date_to', None):
                params['date_to'] = state.audit_filter_date_to

            entries_response = httpx.get(
                f"{api_base_url}/api/audit", params=params, timeout=10.0
            )
            if entries_response.status_code == 200:
                entries = entries_response.json()
                for entry in entries:
                    rules = entry.get('applied_rules', [])
                    if isinstance(rules, list):
                        entry['applied_rules_display'] = ', '.join(rules)
                    else:
                        entry['applied_rules_display'] = str(rules) if rules else ''
                state.audit_entries = entries

        except Exception as e:
            add_error_trace(state, f"Load audit trail failed: {e}", "/api/audit")
            # BUG-389-AUD-001: Don't leak exception internals via Trame WebSocket (state.audit_summary is pushed to browser)
            state.audit_summary = {
                'total_entries': 0, 'by_action_type': {},
                'by_entity_type': {}, 'by_actor': {},
                'retention_days': 7, 'error': type(e).__name__
            }
            state.audit_entries = []

        # BUG-193-004: Use finally to guarantee audit_loading reset
        finally:
            state.audit_loading = False

    @ctrl.trigger("load_audit_trail")
    def trigger_load_audit_trail():
        """Trigger for loading audit trail."""
        state.audit_loading = True
        load_audit_trail()

    @ctrl.trigger("navigate_to_entity")
    def navigate_to_entity(entity_type, entity_id):
        """Navigate to an entity's detail view from audit/monitor.

        Switches active_view to the entity's tab and selects the entity.
        Per UI-VUE-IMPL-01-v1: uses @ctrl.trigger for Vue-callable.
        """
        entity_type_lower = (entity_type or "").lower()

        if entity_type_lower == "rule":
            state.active_view = "rules"
            for rule in (state.rules or []):
                if rule.get("rule_id") == entity_id or rule.get("id") == entity_id:
                    state.selected_rule = rule
                    state.show_rule_detail = True
                    return
            state.show_rule_detail = False

        elif entity_type_lower == "task":
            state.active_view = "tasks"
            for task in (state.tasks or []):
                if task.get("task_id") == entity_id or task.get("id") == entity_id:
                    state.selected_task = task
                    state.show_task_detail = True
                    return
            state.show_task_detail = False

        elif entity_type_lower == "session":
            state.active_view = "sessions"
            # Use the session controller's select_session which loads
            # all detail data (tool_calls, evidence, transcript, etc.)
            ctrl.select_session(entity_id)
            # BUG-UI-AUDIT-NAV-001: Was dead code (set False when already False).
            # select_session sets show_session_detail=True on success.

        elif entity_type_lower == "decision":
            state.active_view = "decisions"
            for decision in (state.decisions or []):
                if decision.get("decision_id") == entity_id or decision.get("id") == entity_id:
                    state.selected_decision = decision
                    state.show_decision_detail = True
                    return
            state.show_decision_detail = False

    # Reactive filter handlers — call load_audit_trail() directly (not ctrl.trigger)
    @state.change("audit_filter_entity_type")
    def _on_audit_filter_entity_type(audit_filter_entity_type, **kwargs):
        if state.active_view == "audit":
            load_audit_trail()

    @state.change("audit_filter_action_type")
    def _on_audit_filter_action_type(audit_filter_action_type, **kwargs):
        if state.active_view == "audit":
            load_audit_trail()

    @state.change("audit_filter_entity_id")
    def _on_audit_filter_entity_id(audit_filter_entity_id, **kwargs):
        if state.active_view == "audit":
            load_audit_trail()

    @state.change("audit_filter_correlation_id")
    def _on_audit_filter_correlation_id(audit_filter_correlation_id, **kwargs):
        if state.active_view == "audit":
            load_audit_trail()

    @state.change("audit_filter_date_from")
    def _on_audit_filter_date_from(audit_filter_date_from, **kwargs):
        if state.active_view == "audit":
            load_audit_trail()

    @state.change("audit_filter_date_to")
    def _on_audit_filter_date_to(audit_filter_date_to, **kwargs):
        if state.active_view == "audit":
            load_audit_trail()

    return {'load_audit_trail': load_audit_trail}
