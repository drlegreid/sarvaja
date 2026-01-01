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


def register_tasks_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """
    Register task-related controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls
    """

    @ctrl.set("select_task")
    def select_task(task_id):
        """Handle task selection for detail view."""
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
                    tasks_response = client.get(f"{api_base_url}/api/tasks")
                    if tasks_response.status_code == 200:
                        state.tasks = tasks_response.json()
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
                    # Refresh tasks list
                    tasks_response = client.get(f"{api_base_url}/api/tasks")
                    if tasks_response.status_code == 200:
                        state.tasks = tasks_response.json()
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
                    # Reload tasks
                    tasks_response = client.get(f"{api_base_url}/api/tasks")
                    if tasks_response.status_code == 200:
                        state.tasks = tasks_response.json()
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
