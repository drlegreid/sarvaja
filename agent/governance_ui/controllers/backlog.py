"""
Agent Backlog Controllers (GAP-FILE-005)
========================================
Controller functions for agent task backlog (TODO-6).

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py

Created: 2024-12-28
"""

import httpx
from typing import Any, Callable


def register_backlog_controllers(
    state: Any,
    ctrl: Any,
    api_base_url: str,
    load_backlog_data: Callable
) -> None:
    """
    Register agent backlog controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls
        load_backlog_data: Function to reload backlog data
    """

    @ctrl.trigger("claim_backlog_task")
    def claim_backlog_task(task_id):
        """Agent claims a task from the backlog."""
        if not state.backlog_agent_id:
            state.has_error = True
            state.error_message = "Please enter an Agent ID to claim tasks"
            return

        try:
            state.is_loading = True
            with httpx.Client(timeout=10.0) as client:
                response = client.put(
                    f"{api_base_url}/api/tasks/{task_id}/claim",
                    params={"agent_id": state.backlog_agent_id}
                )
                if response.status_code == 200:
                    state.status_message = f"Task {task_id} claimed successfully"
                    load_backlog_data()
                else:
                    state.has_error = True
                    state.error_message = f"Failed to claim task: {response.text}"
            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Error claiming task: {str(e)}"

    @ctrl.trigger("complete_backlog_task")
    def complete_backlog_task(task_id):
        """Mark a claimed task as complete."""
        try:
            state.is_loading = True
            with httpx.Client(timeout=10.0) as client:
                response = client.put(f"{api_base_url}/api/tasks/{task_id}/complete")
                if response.status_code == 200:
                    state.status_message = f"Task {task_id} completed successfully"
                    load_backlog_data()
                    # Also refresh the main tasks list
                    tasks_response = client.get(f"{api_base_url}/api/tasks")
                    if tasks_response.status_code == 200:
                        state.tasks = tasks_response.json()
                else:
                    state.has_error = True
                    state.error_message = f"Failed to complete task: {response.text}"
            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Error completing task: {str(e)}"
