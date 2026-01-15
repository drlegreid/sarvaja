"""
Rule entity handlers for Governance Dashboard.

Per RULE-012: Single Responsibility - only rule CRUD operations.
Per RULE-019: UI/UX Standards - consistent handler patterns.
"""

import os
import httpx
from typing import Any

# Per GAP-UI-EXP-012: Use env var for container compatibility
API_BASE_URL = os.environ.get("GOVERNANCE_API_URL", "http://localhost:8082")


def register_rule_handlers(ctrl: Any, state: Any) -> None:
    """Register all rule-related handlers with the controller."""

    @ctrl.set("select_rule")
    def select_rule(rule_id: str) -> None:
        """Handle rule selection for detail view."""
        for rule in state.rules:
            if rule.get('rule_id') == rule_id or rule.get('id') == rule_id:
                state.selected_rule = rule
                state.show_rule_detail = True
                break

    @ctrl.set("close_rule_detail")
    def close_rule_detail() -> None:
        """Close rule detail view."""
        state.show_rule_detail = False
        state.selected_rule = None

    @ctrl.set("show_rule_form")
    def show_rule_form(mode: str = "create") -> None:
        """Show rule create/edit form."""
        state.rule_form_mode = mode
        state.show_rule_form = True

    @ctrl.set("close_rule_form")
    def close_rule_form() -> None:
        """Close rule form."""
        state.show_rule_form = False

    @ctrl.trigger("submit_rule_form")
    def submit_rule_form() -> None:
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
                    response = client.post(f"{API_BASE_URL}/api/rules", json=rule_data)
                else:
                    rule_id = state.selected_rule.get('id') or state.selected_rule.get('rule_id')
                    response = client.put(f"{API_BASE_URL}/api/rules/{rule_id}", json=rule_data)

                if response.status_code in (200, 201):
                    state.status_message = f"Rule {'created' if state.rule_form_mode == 'create' else 'updated'} successfully"
                    rules_response = client.get(f"{API_BASE_URL}/api/rules")
                    if rules_response.status_code == 200:
                        state.rules = rules_response.json()
                else:
                    state.has_error = True
                    state.error_message = f"API Error: {response.status_code} - {response.text}"

            state.show_rule_form = False
            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to save rule: {str(e)}"
            state.show_rule_form = False
            state.status_message = f"Rule saved (offline mode - API unavailable: {str(e)})"

    @ctrl.trigger("delete_rule")
    def delete_rule() -> None:
        """Delete selected rule via REST API."""
        if not state.selected_rule:
            return

        try:
            state.is_loading = True
            rule_id = state.selected_rule.get('id') or state.selected_rule.get('rule_id')

            with httpx.Client(timeout=10.0) as client:
                response = client.delete(f"{API_BASE_URL}/api/rules/{rule_id}")

                if response.status_code == 204:
                    state.status_message = f"Rule {rule_id} deleted successfully"
                    rules_response = client.get(f"{API_BASE_URL}/api/rules")
                    if rules_response.status_code == 200:
                        state.rules = rules_response.json()
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
    def filter_rules_by_status(status: str) -> None:
        """Filter rules by status."""
        state.filter_status = status

    @ctrl.set("filter_rules_by_category")
    def filter_rules_by_category(category: str) -> None:
        """Filter rules by category."""
        state.filter_category = category

    @ctrl.set("search_rules")
    def search_rules(query: str) -> None:
        """Search rules by query."""
        state.search_query = query

    @ctrl.set("analyze_rule_impact")
    def analyze_rule_impact(rule_id: str) -> None:
        """Analyze impact of a rule."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{API_BASE_URL}/api/rules/{rule_id}/impact")
                if response.status_code == 200:
                    state.rule_impact = response.json()
                    state.show_impact_analysis = True
        except Exception as e:
            state.error_message = f"Failed to analyze impact: {str(e)}"
