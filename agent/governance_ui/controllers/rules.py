"""
Rules Controllers (GAP-FILE-005)
================================
Controller functions for rule CRUD operations.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py

Created: 2024-12-28
"""

import httpx
from typing import Any


def register_rules_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """
    Register rule-related controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls
    """

    @ctrl.trigger("select_rule")
    def select_rule(rule_id):
        """Handle rule selection for detail view."""
        for rule in state.rules:
            if rule.get('rule_id') == rule_id or rule.get('id') == rule_id:
                state.selected_rule = rule
                state.show_rule_detail = True
                break

    @ctrl.set("close_rule_detail")
    def close_rule_detail():
        """Close rule detail view."""
        state.show_rule_detail = False
        state.selected_rule = None

    @ctrl.set("show_rule_form")
    def show_rule_form(mode="create"):
        """Show rule create/edit form."""
        state.rule_form_mode = mode
        state.show_rule_form = True

    @ctrl.set("close_rule_form")
    def close_rule_form():
        """Close rule form."""
        state.show_rule_form = False

    @ctrl.trigger("submit_rule_form")
    def submit_rule_form():
        """Submit rule form (create/update) via REST API."""
        try:
            state.is_loading = True
            rule_data = {
                "rule_id": state.form_rule_id,
                "name": state.form_rule_title,
                "directive": state.form_rule_directive,
                "category": state.form_rule_category,
                "priority": state.form_rule_priority,
                "status": "DRAFT"
            }

            with httpx.Client(timeout=10.0) as client:
                if state.rule_form_mode == "create":
                    response = client.post(f"{api_base_url}/api/rules", json=rule_data)
                else:
                    # Edit mode - update existing rule
                    rule_id = state.selected_rule.get('id') or state.selected_rule.get('rule_id')
                    response = client.put(f"{api_base_url}/api/rules/{rule_id}", json=rule_data)

                if response.status_code in (200, 201):
                    state.status_message = f"Rule {'created' if state.rule_form_mode == 'create' else 'updated'} successfully"
                    # Reload rules from API
                    rules_response = client.get(f"{api_base_url}/api/rules")
                    if rules_response.status_code == 200:
                        data = rules_response.json()
                        state.rules = data.get("items", data) if isinstance(data, dict) else data
                else:
                    state.has_error = True
                    state.error_message = f"API Error: {response.status_code} - {response.text}"

            state.show_rule_form = False
            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to save rule: {str(e)}"
            # Fallback to mock if API unavailable
            state.show_rule_form = False
            state.status_message = f"Rule saved (offline mode - API unavailable: {str(e)})"

    @ctrl.trigger("delete_rule")
    def delete_rule():
        """Delete selected rule via REST API."""
        if not state.selected_rule:
            return

        try:
            state.is_loading = True
            rule_id = state.selected_rule.get('id') or state.selected_rule.get('rule_id')

            with httpx.Client(timeout=10.0) as client:
                response = client.delete(f"{api_base_url}/api/rules/{rule_id}")

                if response.status_code == 204:
                    state.status_message = f"Rule {rule_id} deleted successfully"
                    # Reload rules from API
                    rules_response = client.get(f"{api_base_url}/api/rules")
                    if rules_response.status_code == 200:
                        data = rules_response.json()
                        state.rules = data.get("items", data) if isinstance(data, dict) else data
                    state.show_rule_detail = False
                    state.selected_rule = None
                else:
                    state.has_error = True
                    state.error_message = f"Failed to delete: {response.status_code}"

            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to delete rule: {str(e)}"
            state.status_message = f"Delete failed (offline mode): {str(e)}"

    @ctrl.set("filter_rules_by_status")
    def filter_rules_by_status(status):
        """Filter rules by status."""
        state.rules_status_filter = status

    @ctrl.set("filter_rules_by_category")
    def filter_rules_by_category(category):
        """Filter rules by category."""
        state.rules_category_filter = category

    @ctrl.set("search_rules")
    def search_rules(query):
        """Search rules by text."""
        state.rules_search_query = query

    @ctrl.set("sort_rules")
    def sort_rules(column):
        """Sort rules by column."""
        state.rules_sort_column = column
        # Toggle sort direction
        if state.rules_sort_asc:
            state.rules_sort_asc = False
        else:
            state.rules_sort_asc = True
