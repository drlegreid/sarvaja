"""
Task CRUD Controllers
=====================
Controller functions for task select, create, delete, edit operations.

Per DOC-SIZE-01-v1: Extracted from tasks.py.
"""

import httpx as _httpx
from typing import Any

from agent.governance_ui.trace_bar.transforms import add_error_trace as _add_error_trace
from agent.governance_ui.utils import extract_items_from_response, format_timestamps_in_list
from .tasks_helpers import (
    _enrich_doc_count,
    _enrich_first_session,
    _fetch_workspace_project_map,
    _enrich_project_name,
)


def register_tasks_crud(state: Any, ctrl: Any, api_base_url: str,
                        httpx_mod=None, error_trace_fn=None) -> None:
    """Register task CRUD controllers with Trame.

    Args:
        httpx_mod: Injectable httpx module (for testability via hub's patchable reference).
        error_trace_fn: Injectable add_error_trace (for testability).
    """
    httpx = httpx_mod if httpx_mod is not None else _httpx
    add_error_trace = error_trace_fn if error_trace_fn is not None else _add_error_trace

    @ctrl.trigger("select_task")
    def select_task(task_id):
        """Handle task selection for detail view."""
        # BUG-UI-STALE-DETAIL-004: Clear prior task detail state before loading
        state.edit_task_mode = False
        state.task_execution_log = []
        state.show_task_execution = False  # Close chat dialog if open
        state.show_task_execution_inline = False  # BUG-TASK-POPUP-001
        state.task_evidence_files = []  # SRVJ-FEAT-009: Clear evidence
        state.task_evidence_loading = False
        state.nav_source_view = None
        state.nav_source_id = None
        state.nav_source_label = None
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/tasks/{task_id}")
                if response.status_code == 200:
                    state.selected_task = response.json()
                    state.show_task_detail = True
                    _auto_load_task_execution(task_id)
                    _auto_load_task_evidence(task_id)
                    return
        except Exception as e:
            add_error_trace(state, f"Load task detail failed: {e}", f"/api/tasks/{task_id}")

        for task in state.tasks:
            if task.get('task_id') == task_id or task.get('id') == task_id:
                state.selected_task = task
                state.show_task_detail = True
                break
        _auto_load_task_execution(task_id)
        _auto_load_task_evidence(task_id)

    def _auto_load_task_execution(task_id):
        """Auto-load execution log when a task is selected."""
        try:
            state.task_execution_loading = True
            state.task_execution_log = []
            state.show_task_execution_inline = True  # BUG-TASK-POPUP-001: Use inline, not dialog
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/tasks/{task_id}/execution")
                if response.status_code == 200:
                    data = response.json()
                    state.task_execution_log = data.get("events", [])
        except Exception as e:
            add_error_trace(state, f"Load task execution failed: {e}", f"/api/tasks/{task_id}/execution")
            state.task_execution_log = []
        finally:
            state.task_execution_loading = False

    def _auto_load_task_evidence(task_id):
        """Auto-load evidence preview when a task is selected (SRVJ-FEAT-009)."""
        try:
            state.task_evidence_loading = True
            state.task_evidence_files = []
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{api_base_url}/api/tasks/{task_id}/evidence/rendered"
                )
                if response.status_code == 200:
                    data = response.json()
                    state.task_evidence_files = data.get("evidence_files", [])
        except Exception:
            state.task_evidence_files = []
        finally:
            state.task_evidence_loading = False

    @ctrl.trigger("close_task_detail")
    def close_task_detail():
        """Close task detail view and reset all detail state."""
        state.show_task_detail = False
        state.selected_task = None
        state.edit_task_mode = False
        state.edit_task_description = ''
        state.edit_task_phase = 'P10'
        state.edit_task_status = 'TODO'
        state.edit_task_agent = ''
        state.edit_task_body = ''
        state.task_execution_log = []
        state.show_task_execution = False
        state.show_task_execution_inline = False  # BUG-TASK-POPUP-001
        state.nav_source_view = None
        state.nav_source_id = None
        state.nav_source_label = None

    @ctrl.trigger("delete_task")
    def delete_task():
        """Delete selected task via REST API."""
        if not state.selected_task:
            return
        # BUG-UI-DOUBLECLICK-001: Prevent double-click race condition
        if state.is_loading:
            return
        state.has_error = False
        # BUG-UI-UNDEF-002: Pre-initialize to avoid NameError in except handler
        task_id = state.selected_task.get('task_id', 'unknown')
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
                    # BUG-UI-PAGINATION-003: Reset page if current page is now empty
                    if not state.tasks and getattr(state, 'tasks_page', 1) > 1:
                        state.tasks_page = max(1, state.tasks_page - 1)
                        offset = (state.tasks_page - 1) * page_size
                        tasks_response = client.get(f"{api_base_url}/api/tasks", params={"limit": page_size, "offset": offset})
                        if tasks_response.status_code == 200:
                            data = tasks_response.json()
                            if isinstance(data, dict) and "items" in data:
                                state.tasks = data["items"]
                                state.tasks_pagination = data.get("pagination", {})
                    _ws_map = _fetch_workspace_project_map(api_base_url)
                    state.tasks = _enrich_project_name(
                        _enrich_first_session(_enrich_doc_count(format_timestamps_in_list(
                            state.tasks, ["created_at", "completed_at", "claimed_at"]
                        ))),
                        _ws_map,
                    )
                    state.show_task_detail = False
                    state.selected_task = None
                else:
                    state.has_error = True
                    state.error_message = f"Failed to delete: {response.status_code}"
            state.is_loading = False
        except Exception as e:
            add_error_trace(state, f"Delete task failed: {e}", f"/api/tasks/{task_id}")
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to delete task: {type(e).__name__}"  # BUG-476-CTK-1

    @ctrl.trigger("edit_task")
    def edit_task():
        """Enter task edit mode."""
        if state.selected_task:
            state.edit_task_mode = True
            state.edit_task_description = state.selected_task.get('description') or state.selected_task.get('title') or ''
            state.edit_task_phase = state.selected_task.get('phase') or 'P10'
            state.edit_task_status = state.selected_task.get('status') or 'TODO'
            state.edit_task_agent = state.selected_task.get('agent_id') or ''
            state.edit_task_body = state.selected_task.get('body') or ''

    @ctrl.trigger("cancel_task_edit")
    def cancel_task_edit():
        """Cancel task edit mode."""
        state.edit_task_mode = False

    @ctrl.trigger("submit_task_edit")
    def submit_task_edit():
        """Submit task edit via REST API."""
        if not state.selected_task:
            return
        # BUG-UI-DOUBLECLICK-001: Prevent double-click race condition
        if state.is_loading:
            return
        state.has_error = False
        # BUG-UI-VALIDATION-001: Validate required fields before API call
        description = (state.edit_task_description or "").strip()
        if not description:
            state.has_error = True
            state.error_message = "Description is required"
            return
        # BUG-UI-UNDEF-007: Pre-initialize to avoid NameError in except handler
        task_id = state.selected_task.get('task_id', 'unknown')
        try:
            state.is_loading = True
            task_id = state.selected_task.get('id') or state.selected_task.get('task_id')
            update_data = {
                "description": description,
                "phase": (state.edit_task_phase or "P10").strip(),
                "status": (state.edit_task_status or "TODO").strip(),
                "agent_id": (state.edit_task_agent or "").strip() or None,
                "body": (getattr(state, 'edit_task_body', '') or "").strip() or None,
                "summary": (getattr(state, 'edit_task_summary', '') or "").strip() or None,
                "priority": getattr(state, 'edit_task_priority', None) or None,
                "task_type": getattr(state, 'edit_task_type', None) or None,
            }
            with httpx.Client(timeout=10.0) as client:
                response = client.put(
                    f"{api_base_url}/api/tasks/{task_id}",
                    json=update_data
                )
                if response.status_code == 200:
                    state.status_message = f"Task {task_id} updated successfully"
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
                    _ws_map = _fetch_workspace_project_map(api_base_url)
                    state.tasks = _enrich_project_name(
                        _enrich_first_session(_enrich_doc_count(format_timestamps_in_list(
                            state.tasks, ["created_at", "completed_at", "claimed_at"]
                        ))),
                        _ws_map,
                    )
                    updated_task = response.json()
                    state.selected_task = updated_task
                    state.edit_task_mode = False
                else:
                    state.has_error = True
                    state.error_message = f"Failed to update: {response.status_code}"
            state.is_loading = False
        except Exception as e:
            add_error_trace(state, f"Update task failed: {e}", f"/api/tasks/{task_id}")
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to update task: {type(e).__name__}"  # BUG-476-CTK-4

    @ctrl.trigger("create_task")
    def create_task():
        """Create a new task via REST API. BUG-UI-TASKS-001: validate before submit."""
        # BUG-UI-DOUBLECLICK-001: Prevent double-click race condition
        if state.is_loading:
            return
        state.has_error = False
        try:
            # BUG-UI-TASKS-001: Validate required fields before API call
            task_id = getattr(state, 'form_task_id', '') or ''
            description = getattr(state, 'form_task_description', '') or ''
            phase = getattr(state, 'form_task_phase', '') or ''
            task_type = getattr(state, 'form_task_type', None)
            # META-TAXON-01-v1: Allow empty task_id if task_type is set (auto-generate)
            if not task_id.strip() and not task_type:
                state.has_error = True
                state.error_message = "Task ID or Task Type is required"
                return
            if not description.strip():
                state.has_error = True
                state.error_message = "Description is required"
                return

            state.is_loading = True
            task_data = {
                "description": description.strip(),
                "phase": phase.strip() or "P10",
                "status": "TODO",
                "agent_id": getattr(state, 'form_task_agent', '') or None,
                "body": getattr(state, 'form_task_body', '') or None,
                "priority": getattr(state, 'form_task_priority', None),
                "task_type": task_type,
            }
            # Only include task_id if user provided one
            if task_id.strip():
                task_data["task_id"] = task_id.strip()

            with httpx.Client(timeout=10.0) as client:
                response = client.post(f"{api_base_url}/api/tasks", json=task_data)
                if response.status_code == 201:
                    # P16: Check for duplicate warnings in response
                    resp_data = response.json()
                    dup_warnings = resp_data.get("warnings") if isinstance(resp_data, dict) else None
                    if dup_warnings:
                        state.status_message = (
                            "Task created. Warning: " + "; ".join(dup_warnings)
                        )
                        state.has_warning = True
                        state.warning_message = "; ".join(dup_warnings)
                    else:
                        state.status_message = "Task created successfully"
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
                    _ws_map = _fetch_workspace_project_map(api_base_url)
                    state.tasks = _enrich_project_name(
                        _enrich_first_session(_enrich_doc_count(format_timestamps_in_list(
                            state.tasks, ["created_at", "completed_at", "claimed_at"]
                        ))),
                        _ws_map,
                    )
                    # BUG-UI-FORMCLOSE-002: Only close form on success
                    state.show_task_form = False
                    state.form_task_id = ""
                    state.form_task_description = ""
                    state.form_task_body = ""
                    state.form_task_phase = "P10"
                    state.form_task_agent = ""
                    state.form_task_priority = None
                    state.form_task_type = None
                else:
                    state.has_error = True
                    state.error_message = f"Failed to create task: {response.status_code}"

            state.is_loading = False
        except Exception as e:
            add_error_trace(state, f"Create task failed: {e}", "/api/tasks")
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Task creation failed: {type(e).__name__}"  # BUG-476-CTK-5
