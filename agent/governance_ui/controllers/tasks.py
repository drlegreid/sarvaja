"""
Tasks Controllers (GAP-FILE-005)
================================
Controller functions for task CRUD operations.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py
Per DOC-SIZE-01-v1: Navigation in tasks_navigation.py.

Created: 2024-12-28
"""

import httpx
from typing import Any

from agent.governance_ui.utils import extract_items_from_response, format_timestamps_in_list
from .tasks_navigation import register_tasks_navigation  # noqa: F401


def _enrich_doc_count(tasks):
    """Add doc_count field to each task for the Docs column."""
    for t in tasks:
        docs = t.get("linked_documents") or []
        t["doc_count"] = len(docs)
    return tasks


def register_tasks_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """Register task-related controllers with Trame."""

    # Register navigation handlers
    register_tasks_navigation(state, ctrl, api_base_url)

    @ctrl.trigger("select_task")
    def select_task(task_id):
        """Handle task selection for detail view."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/tasks/{task_id}")
                if response.status_code == 200:
                    state.selected_task = response.json()
                    state.show_task_detail = True
                    _auto_load_task_execution(task_id)
                    return
        except Exception:
            pass

        for task in state.tasks:
            if task.get('task_id') == task_id or task.get('id') == task_id:
                state.selected_task = task
                state.show_task_detail = True
                break
        _auto_load_task_execution(task_id)

    def _auto_load_task_execution(task_id):
        """Auto-load execution log when a task is selected."""
        try:
            state.task_execution_loading = True
            state.task_execution_log = []
            state.show_task_execution = True
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/tasks/{task_id}/execution")
                if response.status_code == 200:
                    data = response.json()
                    state.task_execution_log = data.get("events", [])
        except Exception:
            state.task_execution_log = []
        finally:
            state.task_execution_loading = False

    @ctrl.trigger("close_task_detail")
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
                    state.tasks = _enrich_doc_count(format_timestamps_in_list(
                        state.tasks, ["created_at", "completed_at", "claimed_at"]
                    ))
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

    @ctrl.trigger("claim_task")
    def claim_task():
        """Claim selected task via REST API (EPIC-UI-VALUE-001)."""
        if not state.selected_task:
            return
        try:
            task_id = state.selected_task.get('id') or state.selected_task.get('task_id')
            with httpx.Client(timeout=10.0) as client:
                response = client.post(f"{api_base_url}/api/tasks/{task_id}/claim")
                if response.status_code == 200:
                    state.status_message = f"Task {task_id} claimed"
                    state.selected_task = response.json()
                else:
                    state.has_error = True
                    state.error_message = f"Claim failed: {response.status_code}"
        except Exception as e:
            state.has_error = True
            state.error_message = f"Claim failed: {str(e)}"

    @ctrl.trigger("complete_task")
    def complete_task():
        """Complete selected task via REST API (EPIC-UI-VALUE-001)."""
        if not state.selected_task:
            return
        try:
            task_id = state.selected_task.get('id') or state.selected_task.get('task_id')
            with httpx.Client(timeout=10.0) as client:
                response = client.post(f"{api_base_url}/api/tasks/{task_id}/complete")
                if response.status_code == 200:
                    state.status_message = f"Task {task_id} completed"
                    state.selected_task = response.json()
                else:
                    state.has_error = True
                    state.error_message = f"Complete failed: {response.status_code}"
        except Exception as e:
            state.has_error = True
            state.error_message = f"Complete failed: {str(e)}"

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
        try:
            state.is_loading = True
            task_id = state.selected_task.get('id') or state.selected_task.get('task_id')
            update_data = {
                "description": state.edit_task_description,
                "phase": state.edit_task_phase,
                "status": state.edit_task_status,
                "agent_id": state.edit_task_agent or None,
                "body": getattr(state, 'edit_task_body', '') or None,
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
                    state.tasks = _enrich_doc_count(format_timestamps_in_list(
                        state.tasks, ["created_at", "completed_at", "claimed_at"]
                    ))
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
    def create_task():
        """Create a new task via REST API. BUG-UI-TASKS-001: validate before submit."""
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
                    state.tasks = _enrich_doc_count(format_timestamps_in_list(
                        state.tasks, ["created_at", "completed_at", "claimed_at"]
                    ))
                else:
                    state.has_error = True
                    state.error_message = f"Failed to create task: {response.status_code}"

            state.show_task_form = False
            state.form_task_id = ""
            state.form_task_description = ""
            state.form_task_body = ""
            state.form_task_phase = "P10"
            state.form_task_agent = ""
            state.form_task_priority = None
            state.form_task_type = None
            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Task creation failed: {str(e)}"

    @ctrl.trigger("attach_document")
    def attach_document():
        """Attach a document to the selected task via REST API."""
        if not state.selected_task:
            return
        doc_path = getattr(state, 'attach_document_path', '')
        if not doc_path:
            state.has_error = True
            state.error_message = "Document path is required"
            return
        try:
            task_id = state.selected_task.get('id') or state.selected_task.get('task_id')
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{api_base_url}/api/tasks/{task_id}/documents",
                    json={"document_path": doc_path}
                )
                if response.status_code == 201:
                    state.status_message = f"Document attached to {task_id}"
                    # Refresh task detail
                    detail_resp = client.get(f"{api_base_url}/api/tasks/{task_id}")
                    if detail_resp.status_code == 200:
                        state.selected_task = detail_resp.json()
                else:
                    state.has_error = True
                    state.error_message = f"Attach failed: {response.status_code}"
        except Exception as e:
            state.has_error = True
            state.error_message = f"Attach failed: {str(e)}"
        finally:
            state.show_attach_document_dialog = False
            state.attach_document_path = ""

    @ctrl.trigger("tasks_apply_filters")
    def tasks_apply_filters():
        """Apply task filters and reload page 1."""
        state.tasks_page = 1
        load_tasks_page()

    # Reactive filter handlers — @state.change pattern (BUG-UI-TASKS-002 fix)
    @state.change("tasks_status_filter")
    def _on_tasks_status_filter(tasks_status_filter, **kwargs):
        if state.active_view == "tasks":
            state.tasks_page = 1
            load_tasks_page()

    @state.change("tasks_phase_filter")
    def _on_tasks_phase_filter(tasks_phase_filter, **kwargs):
        if state.active_view == "tasks":
            state.tasks_page = 1
            load_tasks_page()

    @state.change("tasks_filter_type")
    def _on_tasks_filter_type(tasks_filter_type, **kwargs):
        """Map tab selection to status filter (cascades to _on_tasks_status_filter)."""
        if state.active_view != "tasks":
            return
        tab_to_status = {
            "all": None,
            "available": "TODO",
            "mine": "IN_PROGRESS",
            "completed": "DONE",
        }
        new_status = tab_to_status.get(tasks_filter_type)
        state.tasks_status_filter = new_status

    def load_tasks_page():
        """Load tasks with pagination and filters."""
        try:
            state.is_loading = True
            offset = (state.tasks_page - 1) * state.tasks_per_page
            params = {"offset": offset, "limit": state.tasks_per_page}

            tasks_status_filter = getattr(state, 'tasks_status_filter', None)
            tasks_phase_filter = getattr(state, 'tasks_phase_filter', None)
            if tasks_status_filter:
                params["status"] = tasks_status_filter
            if tasks_phase_filter:
                params["phase"] = tasks_phase_filter

            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/tasks", params=params)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and "items" in data:
                        state.tasks = data["items"]
                        state.tasks_pagination = data.get("pagination", {
                            "total": 0, "offset": offset,
                            "limit": state.tasks_per_page,
                            "has_more": False,
                            "returned": len(data["items"]),
                        })
                    else:
                        state.tasks = data
                        state.tasks_pagination = {
                            "total": len(data), "offset": 0,
                            "limit": len(data), "has_more": False,
                            "returned": len(data),
                        }
                    state.tasks = _enrich_doc_count(format_timestamps_in_list(
                        state.tasks, ["created_at", "completed_at", "claimed_at"]
                    ))
                    state.status_message = f"Loaded {len(state.tasks)} tasks"
            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to load tasks: {str(e)}"

    @ctrl.trigger("tasks_prev_page")
    def tasks_prev_page():
        """Go to previous page of tasks."""
        if state.tasks_page > 1:
            state.tasks_page -= 1
            load_tasks_page()

    @ctrl.trigger("tasks_next_page")
    def tasks_next_page():
        """Go to next page of tasks."""
        if state.tasks_pagination.get("has_more", False):
            state.tasks_page += 1
            load_tasks_page()

    @ctrl.trigger("tasks_change_page_size")
    def tasks_change_page_size():
        """Change items per page and reload."""
        state.tasks_page = 1
        load_tasks_page()

    @ctrl.trigger("tasks_go_to_page")
    def tasks_go_to_page(page: int):
        """Go to specific page."""
        total_pages = max(
            1,
            (state.tasks_pagination.get("total", 0) + state.tasks_per_page - 1)
            // state.tasks_per_page
        )
        if 1 <= page <= total_pages:
            state.tasks_page = page
            load_tasks_page()
