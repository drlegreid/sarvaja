"""
Agent Backlog Controllers (GAP-FILE-005, GAP-005)
=================================================
Controller functions for agent task backlog with auto-polling.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py
Per GAP-005: Added auto-refresh polling (2026-01-11)

Created: 2024-12-28
Updated: 2026-01-11 (GAP-005 - auto-polling)
"""

import asyncio
import httpx
from typing import Any, Callable, Optional

from agent.governance_ui.utils import extract_items_from_response

# Module-level task reference for cancellation
_polling_task: Optional[asyncio.Task] = None


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
                        state.tasks = extract_items_from_response(tasks_response.json())
                else:
                    state.has_error = True
                    state.error_message = f"Failed to complete task: {response.text}"
            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Error completing task: {str(e)}"

    @ctrl.trigger("toggle_backlog_auto_refresh")
    def toggle_backlog_auto_refresh():
        """
        Toggle auto-refresh polling for backlog view.

        Per GAP-005: Implements automatic polling for task updates.
        Uses asyncio background task for periodic refresh.
        """
        global _polling_task

        state.backlog_auto_refresh = not state.backlog_auto_refresh

        if state.backlog_auto_refresh:
            # Start polling
            async def polling_loop():
                while state.backlog_auto_refresh:
                    await asyncio.sleep(state.backlog_refresh_interval)
                    if state.backlog_auto_refresh:
                        load_backlog_data()
                        state.flush()  # Force UI update

            try:
                loop = asyncio.get_event_loop()
                if _polling_task and not _polling_task.done():
                    _polling_task.cancel()
                _polling_task = loop.create_task(polling_loop())
                state.status_message = f"Auto-refresh started ({state.backlog_refresh_interval}s interval)"
            except Exception as e:
                state.backlog_auto_refresh = False
                state.error_message = f"Failed to start auto-refresh: {str(e)}"
        else:
            # Stop polling
            if _polling_task and not _polling_task.done():
                _polling_task.cancel()
                _polling_task = None
            state.status_message = "Auto-refresh stopped"
