"""
Tasks Controllers (GAP-FILE-005)
================================
Controller functions for task CRUD operations.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py

Created: 2024-12-28
"""

import httpx
from typing import Any

from agent.governance_ui.utils import extract_items_from_response


def register_tasks_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """
    Register task-related controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls
    """

    @ctrl.trigger("select_task")
    def select_task(task_id):
        """Handle task selection for detail view.

        Per GAP-UI-TASK-SESSION-001: Fetch full task details including
        linked_sessions, linked_commits, linked_rules from API.
        """
        # Fetch full task details from API to get linked fields
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/tasks/{task_id}")
                if response.status_code == 200:
                    state.selected_task = response.json()
                    state.show_task_detail = True
                    return
        except Exception:
            pass  # Fall back to cached data

        # Fallback to cached list data if API fails
        for task in state.tasks:
            if task.get('task_id') == task_id or task.get('id') == task_id:
                state.selected_task = task
                state.show_task_detail = True
                break

    @ctrl.set("close_task_detail")
    def close_task_detail():
        """Close task detail view."""
        state.show_task_detail = False
        state.selected_task = None

    @ctrl.trigger("navigate_to_task")
    def navigate_to_task(task_id, source_view=None, source_id=None, source_label=None):
        """Navigate to task from another view (e.g., session detail).

        Per GAP-DATA-INTEGRITY-001 Phase 3: UI navigation for relationships.
        Per UI-NAV-01-v1: Entity Navigation - preserve source for back button.
        Switches to tasks view and selects the specified task.

        Args:
            task_id: Task to navigate to
            source_view: View we came from ('sessions', 'rules', etc.)
            source_id: ID of source entity (session_id, rule_id, etc.)
            source_label: Human-readable label for back button
        """
        if not task_id:
            return

        # Capture navigation source for back button (UI-NAV-01-v1)
        if source_view:
            state.nav_source_view = source_view
            state.nav_source_id = source_id
            state.nav_source_label = source_label or f"Back to {source_view}"
        else:
            # Clear navigation source when navigating directly
            state.nav_source_view = None
            state.nav_source_id = None
            state.nav_source_label = None

        # Switch to tasks view
        state.active_view = 'tasks'
        state.show_session_detail = False
        state.show_decision_detail = False

        # Try to find task in existing list
        found = False
        for task in state.tasks:
            if task.get('task_id') == task_id or task.get('id') == task_id:
                state.selected_task = task
                state.show_task_detail = True
                found = True
                break

        # If not found, try to load it from API
        if not found:
            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(f"{api_base_url}/api/tasks/{task_id}")
                    if response.status_code == 200:
                        state.selected_task = response.json()
                        state.show_task_detail = True
                    else:
                        state.error_message = f"Task {task_id} not found"
            except Exception:
                state.error_message = f"Failed to load task {task_id}"

    @ctrl.trigger("navigate_back_to_source")
    def navigate_back_to_source():
        """Navigate back to the source entity (UI-NAV-01-v1).

        Handles back navigation to sessions, rules, or other entity views.
        """
        source_view = state.nav_source_view
        source_id = state.nav_source_id

        # Clear current detail view
        state.show_task_detail = False
        state.selected_task = None

        # Clear navigation context
        state.nav_source_view = None
        state.nav_source_id = None
        state.nav_source_label = None

        if source_view == 'sessions' and source_id:
            # Navigate back to session detail
            state.active_view = 'sessions'
            # Find and select the session
            for session in state.sessions:
                sid = session.get('session_id') or session.get('id')
                if sid == source_id:
                    state.selected_session = session
                    state.show_session_detail = True
                    return
            # If not found in list, try to load from API
            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(f"{api_base_url}/api/sessions/{source_id}")
                    if response.status_code == 200:
                        state.selected_session = response.json()
                        state.show_session_detail = True
            except Exception:
                pass  # Just go to sessions view without selection
        elif source_view == 'rules' and source_id:
            # Navigate back to rule detail
            state.active_view = 'rules'
            for rule in state.rules:
                rid = rule.get('rule_id') or rule.get('id')
                if rid == source_id:
                    state.selected_rule = rule
                    state.show_rule_detail = True
                    return
        elif source_view:
            # Just switch to the view without selecting
            state.active_view = source_view

    @ctrl.trigger("delete_task")
    def delete_task():
        """Delete selected task via REST API."""
        if not state.selected_task:
            return
        try:
            state.is_loading = True
            task_id = state.selected_task.get('id') or state.selected_task.get('task_id')
            with httpx.Client(timeout=10.0) as client:
                response = client.delete(f"{api_base_url}/api/tasks/{task_id}")
                if response.status_code == 204:
                    state.status_message = f"Task {task_id} deleted successfully"
                    page_size = getattr(state, 'tasks_per_page', 20)
                    offset = (getattr(state, 'tasks_page', 1) - 1) * page_size
                    tasks_response = client.get(f"{api_base_url}/api/tasks", params={"limit": page_size, "offset": offset})
                    if tasks_response.status_code == 200:
                        data = tasks_response.json()
                        if isinstance(data, dict) and "items" in data:
                            state.tasks = data["items"]
                            state.tasks_pagination = data.get("pagination", {})
                        else:
                            state.tasks = extract_items_from_response(data)
                    state.show_task_detail = False
                    state.selected_task = None
                else:
                    state.has_error = True
                    state.error_message = f"Failed to delete: {response.status_code}"
            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to delete task: {str(e)}"

    @ctrl.set("edit_task")
    def edit_task():
        """Enter task edit mode."""
        if state.selected_task:
            state.edit_task_mode = True
            state.edit_task_description = state.selected_task.get('description') or state.selected_task.get('title') or ''
            state.edit_task_phase = state.selected_task.get('phase') or 'P10'
            state.edit_task_status = state.selected_task.get('status') or 'TODO'
            state.edit_task_agent = state.selected_task.get('agent_id') or ''

    @ctrl.set("cancel_task_edit")
    def cancel_task_edit():
        """Cancel task edit mode."""
        state.edit_task_mode = False

    @ctrl.trigger("submit_task_edit")
    def submit_task_edit():
        """Submit task edit via REST API."""
        if not state.selected_task:
            return
        try:
            state.is_loading = True
            task_id = state.selected_task.get('id') or state.selected_task.get('task_id')
            update_data = {
                "description": state.edit_task_description,
                "phase": state.edit_task_phase,
                "status": state.edit_task_status,
                "agent_id": state.edit_task_agent or None
            }
            with httpx.Client(timeout=10.0) as client:
                response = client.put(
                    f"{api_base_url}/api/tasks/{task_id}",
                    json=update_data
                )
                if response.status_code == 200:
                    state.status_message = f"Task {task_id} updated successfully"
                    # Refresh tasks list with pagination
                    page_size = getattr(state, 'tasks_per_page', 20)
                    offset = (getattr(state, 'tasks_page', 1) - 1) * page_size
                    tasks_response = client.get(f"{api_base_url}/api/tasks", params={"limit": page_size, "offset": offset})
                    if tasks_response.status_code == 200:
                        data = tasks_response.json()
                        if isinstance(data, dict) and "items" in data:
                            state.tasks = data["items"]
                            state.tasks_pagination = data.get("pagination", {})
                        else:
                            state.tasks = extract_items_from_response(data)
                    # Update selected task
                    updated_task = response.json()
                    state.selected_task = updated_task
                    state.edit_task_mode = False
                else:
                    state.has_error = True
                    state.error_message = f"Failed to update: {response.status_code}"
            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to update task: {str(e)}"

    @ctrl.set("create_task")
    def create_task():
        """Create a new task via REST API."""
        try:
            state.is_loading = True
            task_data = {
                "task_id": state.form_task_id,
                "description": state.form_task_description,
                "phase": state.form_task_phase,
                "status": "TODO",
                "agent_id": state.form_task_agent
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.post(f"{api_base_url}/api/tasks", json=task_data)
                if response.status_code == 201:
                    state.status_message = "Task created successfully"
                    # Reload tasks preserving current page
                    page_size = getattr(state, 'tasks_per_page', 20)
                    current_page = getattr(state, 'tasks_page', 1)
                    offset = (current_page - 1) * page_size
                    tasks_response = client.get(f"{api_base_url}/api/tasks", params={"limit": page_size, "offset": offset})
                    if tasks_response.status_code == 200:
                        data = tasks_response.json()
                        if isinstance(data, dict) and "items" in data:
                            state.tasks = data["items"]
                            state.tasks_pagination = data.get("pagination", {})
                        else:
                            state.tasks = extract_items_from_response(data)
                else:
                    state.has_error = True
                    state.error_message = f"Failed to create task: {response.status_code}"

            state.show_task_form = False
            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.status_message = f"Task creation failed: {str(e)}"
            state.show_task_form = False

    def load_tasks_page():
        """
        Load tasks with pagination (EPIC-DR-005).

        Fetches tasks from API with offset/limit based on current page.
        """
        try:
            state.is_loading = True
            offset = (state.tasks_page - 1) * state.tasks_per_page
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{api_base_url}/api/tasks",
                    params={"offset": offset, "limit": state.tasks_per_page}
                )
                if response.status_code == 200:
                    data = response.json()
                    # Handle paginated response
                    if isinstance(data, dict) and "items" in data:
                        state.tasks = data["items"]
                        state.tasks_pagination = data.get("pagination", {
                            "total": 0,
                            "offset": offset,
                            "limit": state.tasks_per_page,
                            "has_more": False,
                            "returned": len(data["items"]),
                        })
                    else:
                        # Backward compatibility: direct array
                        state.tasks = data
                        state.tasks_pagination = {
                            "total": len(data),
                            "offset": 0,
                            "limit": len(data),
                            "has_more": False,
                            "returned": len(data),
                        }
                    state.status_message = f"Loaded {len(state.tasks)} tasks"
            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to load tasks: {str(e)}"

    @ctrl.trigger("tasks_prev_page")
    def tasks_prev_page():
        """Go to previous page of tasks (EPIC-DR-005)."""
        if state.tasks_page > 1:
            state.tasks_page -= 1
            load_tasks_page()

    @ctrl.trigger("tasks_next_page")
    def tasks_next_page():
        """Go to next page of tasks (EPIC-DR-005)."""
        if state.tasks_pagination.get("has_more", False):
            state.tasks_page += 1
            load_tasks_page()

    @ctrl.trigger("tasks_change_page_size")
    def tasks_change_page_size():
        """Change items per page and reload (EPIC-DR-005)."""
        # Reset to page 1 when changing page size
        state.tasks_page = 1
        load_tasks_page()

    @ctrl.trigger("tasks_go_to_page")
    def tasks_go_to_page(page: int):
        """Go to specific page (EPIC-DR-005)."""
        total_pages = max(
            1,
            (state.tasks_pagination.get("total", 0) + state.tasks_per_page - 1)
            // state.tasks_per_page
        )
        if 1 <= page <= total_pages:
            state.tasks_page = page
            load_tasks_page()
