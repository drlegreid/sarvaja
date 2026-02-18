"""
Decisions Controllers (GAP-FILE-005)
====================================
Controller functions for decision CRUD operations.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py
Per GAP-UI-033: Decision CRUD operations

Created: 2024-12-28
Updated: 2026-01-02 (GAP-UI-033)
"""

import httpx
from typing import Any

from agent.governance_ui.trace_bar.transforms import add_error_trace


def register_decisions_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """
    Register decision-related controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls
    """

    @ctrl.trigger("select_decision")
    def select_decision(decision_id):
        """Handle decision selection for detail view."""
        # BUG-239-RULES-001: Guard against None state.decisions
        for decision in (state.decisions or []):
            if decision.get('decision_id') == decision_id or decision.get('id') == decision_id:
                state.selected_decision = decision
                state.show_decision_detail = True
                break

    @ctrl.trigger("close_decision_detail")
    def close_decision_detail():
        """Close decision detail view."""
        state.show_decision_detail = False
        state.selected_decision = None

    @ctrl.trigger("open_decision_form")
    def open_decision_form(mode="create"):
        """Show decision create/edit form."""
        state.decision_form_mode = mode
        if mode == "edit" and state.selected_decision:
            # Populate form with selected decision data
            state.form_decision_id = state.selected_decision.get('decision_id') or state.selected_decision.get('id', '')
            state.form_decision_name = state.selected_decision.get('name') or state.selected_decision.get('title', '')
            state.form_decision_context = state.selected_decision.get('context', '')
            state.form_decision_rationale = state.selected_decision.get('rationale', '')
            state.form_decision_status = state.selected_decision.get('status', 'PENDING')
            state.form_decision_options = state.selected_decision.get('options', [])
            state.form_decision_selected_option = state.selected_decision.get('selected_option', '')
        else:
            # Clear form for new decision
            state.form_decision_id = ''
            state.form_decision_name = ''
            state.form_decision_context = ''
            state.form_decision_rationale = ''
            state.form_decision_status = 'PENDING'
            state.form_decision_options = []
            state.form_decision_selected_option = ''
        state.show_decision_form = True

    @ctrl.trigger("close_decision_form")
    def close_decision_form():
        """Close decision form."""
        state.show_decision_form = False

    @ctrl.trigger("submit_decision_form")
    def submit_decision_form():
        """Submit decision form (create/update) via REST API."""
        # BUG-UI-DOUBLECLICK-001: Prevent double-click race condition
        if state.is_loading:
            return
        state.has_error = False
        # BUG-UI-VALIDATION-001: Validate required fields
        name = (state.form_decision_name or "").strip()
        context = (state.form_decision_context or "").strip()
        if not name:
            state.has_error = True
            state.error_message = "Decision name is required"
            return
        if not context:
            state.has_error = True
            state.error_message = "Decision context is required"
            return
        try:
            state.is_loading = True
            decision_data = {
                "decision_id": (state.form_decision_id or "").strip(),
                "name": name,
                "context": context,
                "rationale": (state.form_decision_rationale or "").strip(),
                "status": state.form_decision_status,
                "options": state.form_decision_options or [],
                "selected_option": state.form_decision_selected_option or None,
            }

            with httpx.Client(timeout=10.0) as client:
                if state.decision_form_mode == "create":
                    response = client.post(f"{api_base_url}/api/decisions", json=decision_data)
                else:
                    # Edit mode - update existing decision
                    # BUG-UI-DECISION-GUARD-001: Guard against None selected_decision
                    if not state.selected_decision:
                        state.has_error = True
                        state.error_message = "No decision selected for editing"
                        # BUG-187-002: Reset is_loading on early return
                        state.is_loading = False
                        return
                    decision_id = state.selected_decision.get('id') or state.selected_decision.get('decision_id')
                    response = client.put(f"{api_base_url}/api/decisions/{decision_id}", json=decision_data)

                if response.status_code in (200, 201):
                    state.status_message = f"Decision {'created' if state.decision_form_mode == 'create' else 'updated'} successfully"
                    # Reload decisions from API
                    decisions_response = client.get(f"{api_base_url}/api/decisions")
                    if decisions_response.status_code == 200:
                        data = decisions_response.json()
                        state.decisions = data.get("items", data) if isinstance(data, dict) else data
                    # BUG-UI-FORMCLOSE-001: Only close form on success
                    state.show_decision_form = False
                    state.show_decision_detail = False
                    state.selected_decision = None
                else:
                    state.has_error = True
                    # BUG-389-DEC-001: Don't leak response.text (may contain internal paths/stack traces) via Trame WebSocket
                    state.error_message = f"API Error: {response.status_code}"

            state.is_loading = False
        except Exception as e:
            add_error_trace(state, f"Save decision failed: {e}", "/api/decisions")
            state.is_loading = False
            state.has_error = True
            # BUG-389-DEC-002: Don't leak httpx internals via Trame WebSocket
            state.error_message = f"Failed to save decision: {type(e).__name__}"

    @ctrl.trigger("delete_decision")
    def delete_decision():
        """Delete selected decision via REST API."""
        if not state.selected_decision:
            return
        # BUG-UI-DOUBLECLICK-001: Prevent double-click race condition
        if state.is_loading:
            return

        state.has_error = False
        # BUG-UI-UNDEF-004: Pre-initialize to avoid NameError in except handler
        decision_id = state.selected_decision.get('decision_id', 'unknown')
        try:
            state.is_loading = True
            decision_id = state.selected_decision.get('id') or state.selected_decision.get('decision_id')

            with httpx.Client(timeout=10.0) as client:
                response = client.delete(f"{api_base_url}/api/decisions/{decision_id}")

                if response.status_code == 204:
                    state.status_message = f"Decision {decision_id} deleted successfully"
                    # Reload decisions from API
                    decisions_response = client.get(f"{api_base_url}/api/decisions")
                    if decisions_response.status_code == 200:
                        data = decisions_response.json()
                        state.decisions = data.get("items", data) if isinstance(data, dict) else data
                    state.show_decision_detail = False
                    state.selected_decision = None
                else:
                    state.has_error = True
                    state.error_message = f"Failed to delete: {response.status_code}"

            state.is_loading = False
        except Exception as e:
            add_error_trace(state, f"Delete decision failed: {e}", f"/api/decisions/{decision_id}")
            state.is_loading = False
            state.has_error = True
            # BUG-389-DEC-003: Don't leak httpx internals via Trame WebSocket
            state.error_message = f"Failed to delete decision: {type(e).__name__}"
