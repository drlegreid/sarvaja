"""
Task Lifecycle Controllers
==========================
Controller functions for task claim, complete, cancel operations.

Per DOC-SIZE-01-v1: Extracted from tasks.py.
"""

import httpx as _httpx
from typing import Any

from agent.governance_ui.trace_bar.transforms import add_error_trace as _add_error_trace


def register_tasks_lifecycle(state: Any, ctrl: Any, api_base_url: str,
                             httpx_mod=None, error_trace_fn=None) -> None:
    """Register task lifecycle controllers with Trame.

    Args:
        httpx_mod: Injectable httpx module (for testability via hub's patchable reference).
        error_trace_fn: Injectable add_error_trace (for testability).
    """
    httpx = httpx_mod if httpx_mod is not None else _httpx
    add_error_trace = error_trace_fn if error_trace_fn is not None else _add_error_trace

    @ctrl.trigger("claim_selected_task")
    def claim_selected_task():
        """Claim selected task via REST API (EPIC-UI-VALUE-001)."""
        if not state.selected_task:
            return
        state.has_error = False
        # BUG-UI-UNDEF-005: Pre-initialize to avoid NameError in except handler
        task_id = state.selected_task.get('task_id', 'unknown')
        try:
            state.is_loading = True
            task_id = state.selected_task.get('id') or state.selected_task.get('task_id')
            with httpx.Client(timeout=10.0) as client:
                response = client.post(f"{api_base_url}/api/tasks/{task_id}/claim")
                if response.status_code == 200:
                    state.status_message = f"Task {task_id} claimed"
                    state.selected_task = response.json()
                else:
                    state.has_error = True
                    state.error_message = f"Claim failed: {response.status_code}"
            state.is_loading = False
        except Exception as e:
            add_error_trace(state, f"Claim task failed: {e}", f"/api/tasks/{task_id}/claim")
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Claim failed: {type(e).__name__}"  # BUG-476-CTK-2

    @ctrl.trigger("complete_selected_task")
    def complete_selected_task():
        """Complete selected task via REST API (EPIC-UI-VALUE-001)."""
        if not state.selected_task:
            return
        state.has_error = False
        # BUG-UI-UNDEF-006: Pre-initialize to avoid NameError in except handler
        task_id = state.selected_task.get('task_id', 'unknown')
        try:
            state.is_loading = True
            task_id = state.selected_task.get('id') or state.selected_task.get('task_id')
            with httpx.Client(timeout=10.0) as client:
                response = client.post(f"{api_base_url}/api/tasks/{task_id}/complete")
                if response.status_code == 200:
                    state.status_message = f"Task {task_id} completed"
                    state.selected_task = response.json()
                else:
                    state.has_error = True
                    state.error_message = f"Complete failed: {response.status_code}"
            state.is_loading = False
        except Exception as e:
            add_error_trace(state, f"Complete task failed: {e}", f"/api/tasks/{task_id}/complete")
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Complete failed: {type(e).__name__}"  # BUG-476-CTK-3

    @ctrl.trigger("cancel_selected_task")
    def cancel_selected_task():
        """Cancel selected task — sets status to CANCELED (P14: soft cancel)."""
        if not state.selected_task:
            return
        state.has_error = False
        task_id = state.selected_task.get('task_id', 'unknown')
        try:
            state.is_loading = True
            task_id = state.selected_task.get('id') or state.selected_task.get('task_id')
            with httpx.Client(timeout=10.0) as client:
                response = client.put(
                    f"{api_base_url}/api/tasks/{task_id}",
                    json={"status": "CANCELED"},
                )
                if response.status_code == 200:
                    state.status_message = f"Task {task_id} canceled"
                    state.selected_task = response.json()
                else:
                    state.has_error = True
                    state.error_message = f"Cancel failed: {response.status_code}"
            state.is_loading = False
        except Exception as e:
            add_error_trace(state, f"Cancel task failed: {e}", f"/api/tasks/{task_id}")
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Cancel failed: {type(e).__name__}"
