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


def register_decisions_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """
    Register decision-related controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls
    """

    @ctrl.set("select_decision")
    def select_decision(decision_id):
        """Handle decision selection for detail view."""
        for decision in state.decisions:
            if decision.get('decision_id') == decision_id or decision.get('id') == decision_id:
                state.selected_decision = decision
                state.show_decision_detail = True
                break

    @ctrl.set("close_decision_detail")
    def close_decision_detail():
        """Close decision detail view."""
        state.show_decision_detail = False
        state.selected_decision = None

    @ctrl.set("show_decision_form")
    def show_decision_form(mode="create"):
        """Show decision create/edit form."""
        state.decision_form_mode = mode
        if mode == "edit" and state.selected_decision:
            # Populate form with selected decision data
            state.form_decision_id = state.selected_decision.get('decision_id') or state.selected_decision.get('id', '')
            state.form_decision_name = state.selected_decision.get('name') or state.selected_decision.get('title', '')
            state.form_decision_context = state.selected_decision.get('context', '')
            state.form_decision_rationale = state.selected_decision.get('rationale', '')
            state.form_decision_status = state.selected_decision.get('status', 'PENDING')
        else:
            # Clear form for new decision
            state.form_decision_id = ''
            state.form_decision_name = ''
            state.form_decision_context = ''
            state.form_decision_rationale = ''
            state.form_decision_status = 'PENDING'
        state.show_decision_form = True

    @ctrl.set("close_decision_form")
    def close_decision_form():
        """Close decision form."""
        state.show_decision_form = False

    @ctrl.trigger("submit_decision_form")
    def submit_decision_form():
        """Submit decision form (create/update) via REST API."""
        try:
            state.is_loading = True
            decision_data = {
                "decision_id": state.form_decision_id,
                "name": state.form_decision_name,
                "context": state.form_decision_context,
                "rationale": state.form_decision_rationale,
                "status": state.form_decision_status
            }

            with httpx.Client(timeout=10.0) as client:
                if state.decision_form_mode == "create":
                    response = client.post(f"{api_base_url}/api/decisions", json=decision_data)
                else:
                    # Edit mode - update existing decision
                    decision_id = state.selected_decision.get('id') or state.selected_decision.get('decision_id')
                    response = client.put(f"{api_base_url}/api/decisions/{decision_id}", json=decision_data)

                if response.status_code in (200, 201):
                    state.status_message = f"Decision {'created' if state.decision_form_mode == 'create' else 'updated'} successfully"
                    # Reload decisions from API
                    decisions_response = client.get(f"{api_base_url}/api/decisions")
                    if decisions_response.status_code == 200:
                        state.decisions = decisions_response.json()
                else:
                    state.has_error = True
                    state.error_message = f"API Error: {response.status_code} - {response.text}"

            state.show_decision_form = False
            state.show_decision_detail = False
            state.selected_decision = None
            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to save decision: {str(e)}"
            state.show_decision_form = False
            state.status_message = f"Decision saved (offline mode - API unavailable: {str(e)})"

    @ctrl.trigger("delete_decision")
    def delete_decision():
        """Delete selected decision via REST API."""
        if not state.selected_decision:
            return

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
                        state.decisions = decisions_response.json()
                    state.show_decision_detail = False
                    state.selected_decision = None
                else:
                    state.has_error = True
                    state.error_message = f"Failed to delete: {response.status_code}"

            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to delete decision: {str(e)}"
            state.status_message = f"Delete failed (offline mode): {str(e)}"
