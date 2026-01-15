"""
Task entity handlers for Governance Dashboard.

Per RULE-012: Single Responsibility - only task CRUD operations.
Per RULE-019: UI/UX Standards - consistent handler patterns.
"""

import os
import httpx
from typing import Any

# Per GAP-UI-EXP-012: Use env var for container compatibility
API_BASE_URL = os.environ.get("GOVERNANCE_API_URL", "http://localhost:8082")


def register_task_handlers(ctrl: Any, state: Any) -> None:
    """Register all task-related handlers with the controller."""

    @ctrl.set("select_task")
    def select_task(task_id: str) -> None:
        """Handle task selection for detail view."""
        for task in state.tasks:
            if task.get('task_id') == task_id or task.get('id') == task_id:
                state.selected_task = task
                state.show_task_detail = True
                break

    @ctrl.set("close_task_detail")
    def close_task_detail() -> None:
        """Close task detail view."""
        state.show_task_detail = False
        state.selected_task = None

    @ctrl.trigger("delete_task")
    def delete_task() -> None:
        """Delete selected task via REST API."""
        if not state.selected_task:
            return
        try:
            state.is_loading = True
            task_id = state.selected_task.get('id') or state.selected_task.get('task_id')
            with httpx.Client(timeout=10.0) as client:
                response = client.delete(f"{API_BASE_URL}/api/tasks/{task_id}")
                if response.status_code == 204:
                    state.status_message = f"Task {task_id} deleted successfully"
                    tasks_response = client.get(f"{API_BASE_URL}/api/tasks")
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
    def edit_task() -> None:
        """Enter task edit mode."""
        if state.selected_task:
            state.edit_task_mode = True
            state.edit_task_description = state.selected_task.get('description') or state.selected_task.get('title') or ''
            state.edit_task_phase = state.selected_task.get('phase') or 'P10'
            state.edit_task_status = state.selected_task.get('status') or 'TODO'
            state.edit_task_agent = state.selected_task.get('agent_id') or ''

    @ctrl.set("cancel_task_edit")
    def cancel_task_edit() -> None:
        """Cancel task edit mode."""
        state.edit_task_mode = False

    @ctrl.trigger("submit_task_edit")
    def submit_task_edit() -> None:
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
                    f"{API_BASE_URL}/api/tasks/{task_id}",
                    json=update_data
                )
                if response.status_code == 200:
                    state.status_message = f"Task {task_id} updated successfully"
                    tasks_response = client.get(f"{API_BASE_URL}/api/tasks")
                    if tasks_response.status_code == 200:
                        state.tasks = tasks_response.json()
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

    @ctrl.trigger("create_task")
    def create_task() -> None:
        """Create a new task via REST API."""
        try:
            state.is_loading = True
            task_data = {
                "task_id": state.new_task_id or f"TASK-{len(state.tasks) + 1:03d}",
                "description": state.new_task_description,
                "phase": state.new_task_phase or "P10",
                "status": "TODO",
            }
            with httpx.Client(timeout=10.0) as client:
                response = client.post(f"{API_BASE_URL}/api/tasks", json=task_data)
                if response.status_code == 201:
                    state.status_message = f"Task created successfully"
                    tasks_response = client.get(f"{API_BASE_URL}/api/tasks")
                    if tasks_response.status_code == 200:
                        state.tasks = tasks_response.json()
                    state.show_task_form = False
                else:
                    state.has_error = True
                    state.error_message = f"Failed to create: {response.status_code}"
            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to create task: {str(e)}"
