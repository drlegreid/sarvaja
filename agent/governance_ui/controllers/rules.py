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

from agent.governance_ui.trace_bar.transforms import add_error_trace


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
        # BUG-UI-STALE-DETAIL-005: Clear prior rule detail state before loading
        state.rule_implementing_tasks = []
        state.rule_implementing_tasks_loading = False
        for rule in state.rules:
            if rule.get('rule_id') == rule_id or rule.get('id') == rule_id:
                state.selected_rule = rule
                state.show_rule_detail = True
                break

    @ctrl.trigger("close_rule_detail")
    def close_rule_detail():
        """Close rule detail view and reset associated state."""
        state.show_rule_detail = False
        state.selected_rule = None
        state.rule_implementing_tasks = []
        state.rule_implementing_tasks_loading = False

    @ctrl.trigger("open_rule_form")
    def open_rule_form(mode="create"):
        """Show rule create/edit form."""
        state.rule_form_mode = mode
        if mode == "edit" and state.selected_rule:
            state.form_rule_id = state.selected_rule.get('rule_id') or state.selected_rule.get('id') or ''
            state.form_rule_title = state.selected_rule.get('name') or ''
            state.form_rule_directive = state.selected_rule.get('directive') or ''
            state.form_rule_category = state.selected_rule.get('category') or 'governance'
            state.form_rule_priority = state.selected_rule.get('priority') or 'HIGH'
            state.form_rule_applicability = state.selected_rule.get('applicability') or 'MANDATORY'
        else:
            state.form_rule_id = ''
            state.form_rule_title = ''
            state.form_rule_directive = ''
            state.form_rule_category = 'governance'
            state.form_rule_priority = 'HIGH'
            state.form_rule_applicability = 'MANDATORY'
        state.show_rule_form = True

    @ctrl.trigger("edit_rule")
    def edit_rule():
        """Populate form with selected rule's data for editing (GAP-RULE-EDIT-001)."""
        if state.selected_rule:
            state.form_rule_id = state.selected_rule.get('rule_id') or state.selected_rule.get('id') or ''
            state.form_rule_title = state.selected_rule.get('name') or ''
            state.form_rule_directive = state.selected_rule.get('directive') or ''
            state.form_rule_category = state.selected_rule.get('category') or 'governance'
            state.form_rule_priority = state.selected_rule.get('priority') or 'HIGH'
            state.form_rule_applicability = state.selected_rule.get('applicability') or 'MANDATORY'
            state.rule_form_mode = 'edit'
            state.show_rule_form = True

    @ctrl.trigger("close_rule_form")
    def close_rule_form():
        """Close rule form."""
        state.show_rule_form = False

    @ctrl.trigger("submit_rule_form")
    def submit_rule_form():
        """Submit rule form (create/update) via REST API."""
        # BUG-UI-DOUBLECLICK-001: Prevent double-click race condition
        if state.is_loading:
            return
        state.has_error = False
        # BUG-UI-VALIDATION-001: Validate required fields
        rule_id_val = (state.form_rule_id or "").strip()
        title_val = (state.form_rule_title or "").strip()
        directive_val = (state.form_rule_directive or "").strip()
        if not rule_id_val:
            state.has_error = True
            state.error_message = "Rule ID is required"
            return
        if not title_val:
            state.has_error = True
            state.error_message = "Rule name is required"
            return
        if not directive_val:
            state.has_error = True
            state.error_message = "Rule directive is required"
            return
        try:
            state.is_loading = True
            rule_data = {
                "rule_id": rule_id_val,
                "name": title_val,
                "directive": directive_val,
                "category": state.form_rule_category,
                "priority": state.form_rule_priority,
                "applicability": getattr(state, 'form_rule_applicability', 'MANDATORY'),
                "status": "DRAFT"
            }

            with httpx.Client(timeout=10.0) as client:
                if state.rule_form_mode == "create":
                    response = client.post(f"{api_base_url}/api/rules", json=rule_data)
                else:
                    # Edit mode - update existing rule
                    # BUG-UI-RULE-EDIT-GUARD-001: Guard against None selected_rule
                    if not state.selected_rule:
                        state.has_error = True
                        state.error_message = "No rule selected for editing"
                        return
                    rule_id = state.selected_rule.get('id') or state.selected_rule.get('rule_id')
                    response = client.put(f"{api_base_url}/api/rules/{rule_id}", json=rule_data)

                if response.status_code in (200, 201):
                    state.status_message = f"Rule {'created' if state.rule_form_mode == 'create' else 'updated'} successfully"
                    # Reload rules from API
                    rules_response = client.get(f"{api_base_url}/api/rules")
                    if rules_response.status_code == 200:
                        data = rules_response.json()
                        state.rules = data.get("items", data) if isinstance(data, dict) else data
                    # BUG-UI-FORMCLOSE-001: Only close form on success
                    state.show_rule_form = False
                else:
                    state.has_error = True
                    state.error_message = f"API Error: {response.status_code} - {response.text}"

            state.is_loading = False
        except Exception as e:
            add_error_trace(state, f"Save rule failed: {e}", "/api/rules")
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to save rule: {str(e)}"

    @ctrl.trigger("delete_rule")
    def delete_rule():
        """Delete selected rule via REST API."""
        if not state.selected_rule:
            return
        # BUG-UI-DOUBLECLICK-001: Prevent double-click race condition
        if state.is_loading:
            return

        state.has_error = False
        # BUG-UI-UNDEF-003: Pre-initialize to avoid NameError in except handler
        rule_id = state.selected_rule.get('rule_id', 'unknown')
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
            add_error_trace(state, f"Delete rule failed: {e}", f"/api/rules/{rule_id}")
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to delete rule: {str(e)}"

    def load_rules():
        """Load rules from API with current filters (BUG-UI-RULES-001 fix)."""
        try:
            params = {}
            rules_status_filter = getattr(state, 'rules_status_filter', None)
            rules_category_filter = getattr(state, 'rules_category_filter', None)
            if rules_status_filter:
                params["status"] = rules_status_filter
            if rules_category_filter:
                params["category"] = rules_category_filter

            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/rules", params=params)
                if response.status_code == 200:
                    data = response.json()
                    state.rules = data.get("items", data) if isinstance(data, dict) else data
        except Exception as e:
            add_error_trace(state, f"Load rules failed: {e}", "/api/rules")
            state.has_error = True
            state.error_message = f"Failed to load rules: {str(e)}"

    # Reactive filter handlers — @state.change pattern (BUG-UI-RULES-001 fix)
    @state.change("rules_status_filter")
    def _on_rules_status_filter(rules_status_filter, **kwargs):
        if state.active_view == "rules":
            load_rules()

    @state.change("rules_category_filter")
    def _on_rules_category_filter(rules_category_filter, **kwargs):
        if state.active_view == "rules":
            load_rules()

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

    # BUG-UI-RULES-001: Return load_rules for auto-load wiring in on_view_change
    return {"load_rules": load_rules}
