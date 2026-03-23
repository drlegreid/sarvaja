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

from agent.governance_ui.trace_bar.transforms import add_error_trace
from agent.governance_ui.utils import extract_items_from_response, format_timestamps_in_list
from agent.governance_ui.views.tasks.histogram import (
    compute_histogram_data as _compute_histogram,
    update_plotly_histogram as _update_histogram,
    has_plotly as _has_task_plotly,
    extract_filter_from_click as _extract_histogram_filter,
)
from .tasks_navigation import register_tasks_navigation  # noqa: F401


def _enrich_doc_count(tasks):
    """Add doc_count field to each task for the Docs column."""
    for t in tasks:
        docs = t.get("linked_documents") or []
        t["doc_count"] = len(docs)
    return tasks


def _enrich_first_session(tasks):
    """Add first_session field to each task for the Session column. Phase 9d."""
    for t in tasks:
        sessions = t.get("linked_sessions") or []
        t["first_session"] = sessions[0] if sessions else ""
    return tasks


def _fetch_workspace_project_map(api_base_url):
    """Fetch workspace_id → project_id map from API. FIX-HIER-001."""
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{api_base_url}/api/workspaces")
            if resp.status_code == 200:
                return {
                    ws["workspace_id"]: ws.get("project_id", "")
                    for ws in resp.json()
                }
    except Exception:
        pass
    return {}


def _enrich_project_name(tasks, ws_project_map):
    """Add project_name field from workspace→project_id mapping. FIX-HIER-001."""
    for t in tasks:
        ws_id = t.get("workspace_id")
        t["project_name"] = ws_project_map.get(ws_id, "") if ws_id else ""
    return tasks


# Phase 4: Test task prefix patterns
_TEST_PREFIXES = ("CRUD-", "INTTEST-", "TEST-")


def _filter_test_tasks(tasks):
    """FIX-FILT-001: Remove test tasks from display list.

    Filters out tasks where task_type='test' or task_id starts
    with test prefixes (CRUD-*, INTTEST-*, TEST-*).
    """
    return [
        t for t in tasks
        if t.get("task_type") != "test"
        and not any(
            (t.get("task_id") or "").startswith(pfx)
            for pfx in _TEST_PREFIXES
        )
    ]




def register_tasks_controllers(state: Any, ctrl: Any, api_base_url: str) -> dict:
    """Register task-related controllers with Trame."""

    # Register navigation handlers
    register_tasks_navigation(state, ctrl, api_base_url)

    def _populate_filter_options(ws_map):
        """Phase 4: Populate workspace and project dropdown options from ws_map."""
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{api_base_url}/api/workspaces")
                if resp.status_code == 200:
                    workspaces = resp.json()
                    state.task_workspace_options = [
                        {"title": ws.get("name", ws["workspace_id"]),
                         "value": ws["workspace_id"]}
                        for ws in workspaces
                    ]
                    # Unique projects from workspaces
                    projects = {}
                    for ws in workspaces:
                        pid = ws.get("project_id")
                        if pid and pid not in projects:
                            projects[pid] = pid
                    state.task_project_options = [
                        {"title": pid, "value": pid}
                        for pid in sorted(projects.keys())
                    ]
        except Exception:
            pass

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
        # BUG-UI-UNDEF-008: Pre-initialize to avoid NameError in except handler
        task_id = state.selected_task.get('task_id', 'unknown')
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
            add_error_trace(state, f"Attach document failed: {e}", f"/api/tasks/{task_id}/documents")
            state.has_error = True
            state.error_message = f"Attach failed: {type(e).__name__}"  # BUG-476-CTK-6
        finally:
            state.show_attach_document_dialog = False
            state.attach_document_path = ""

    # --- Link Session dialog handlers (SRVJ-FEAT-011) ---

    @ctrl.trigger("open_link_session_dialog")
    def open_link_session_dialog():
        """Open the link session picker dialog. Fetches available sessions."""
        state.link_session_loading = True
        state.link_session_search = ""
        state.show_link_session_dialog = True
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{api_base_url}/api/sessions",
                    params={"limit": 100}
                )
                if response.status_code == 200:
                    data = response.json()
                    items = data if isinstance(data, list) else data.get("items", data.get("sessions", []))
                    state.link_session_items = items
                else:
                    state.link_session_items = []
        except Exception as e:
            add_error_trace(state, f"Fetch sessions for link dialog failed: {e}", "/api/sessions")
            state.link_session_items = []
        finally:
            state.link_session_loading = False

    @ctrl.trigger("link_session_to_task")
    def link_session_to_task(session_id):
        """Link a session to the selected task via REST API."""
        if not state.selected_task or not session_id:
            return
        task_id = state.selected_task.get('id') or state.selected_task.get('task_id')
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{api_base_url}/api/tasks/{task_id}/sessions/{session_id}"
                )
                if response.status_code == 201:
                    state.status_message = f"Session {session_id} linked to {task_id}"
                    # Refresh task detail to show new linked session
                    detail_resp = client.get(f"{api_base_url}/api/tasks/{task_id}")
                    if detail_resp.status_code == 200:
                        state.selected_task = detail_resp.json()
                else:
                    state.has_error = True
                    state.error_message = f"Link session failed: {response.status_code}"
        except Exception as e:
            add_error_trace(state, f"Link session failed: {e}", f"/api/tasks/{task_id}/sessions/{session_id}")
            state.has_error = True
            state.error_message = f"Link session failed: {type(e).__name__}"

    # --- Link Document dialog handlers (SRVJ-FEAT-012) ---

    @ctrl.trigger("open_link_document_dialog")
    def open_link_document_dialog():
        """Open the link document browser dialog. Fetches available documents."""
        state.link_document_loading = True
        state.link_document_search = ""
        state.link_document_selected = []
        state.show_link_document_dialog = True
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{api_base_url}/api/documents",
                    params={"limit": 200}
                )
                if response.status_code == 200:
                    data = response.json()
                    items = data if isinstance(data, list) else data.get("items", data.get("documents", []))
                    # Normalize to [{path: ...}] format
                    normalized = []
                    for item in items:
                        if isinstance(item, str):
                            normalized.append({"path": item})
                        elif isinstance(item, dict):
                            path = item.get("path") or item.get("document_path") or item.get("id", "")
                            normalized.append({"path": path, **item})
                        else:
                            normalized.append({"path": str(item)})
                    state.link_document_items = normalized
                else:
                    state.link_document_items = []
        except Exception as e:
            add_error_trace(state, f"Fetch documents for link dialog failed: {e}", "/api/documents")
            state.link_document_items = []
        finally:
            state.link_document_loading = False

    @ctrl.trigger("link_documents_to_task")
    def link_documents_to_task():
        """Batch link selected documents to the selected task."""
        if not state.selected_task:
            return
        selected = getattr(state, 'link_document_selected', [])
        if not selected:
            return
        task_id = state.selected_task.get('id') or state.selected_task.get('task_id')
        linked_count = 0
        try:
            with httpx.Client(timeout=10.0) as client:
                for doc_path in selected:
                    response = client.post(
                        f"{api_base_url}/api/tasks/{task_id}/documents",
                        json={"document_path": doc_path}
                    )
                    if response.status_code == 201:
                        linked_count += 1
                if linked_count > 0:
                    state.status_message = f"{linked_count} document(s) linked to {task_id}"
                    # Refresh task detail
                    detail_resp = client.get(f"{api_base_url}/api/tasks/{task_id}")
                    if detail_resp.status_code == 200:
                        state.selected_task = detail_resp.json()
        except Exception as e:
            add_error_trace(state, f"Batch link documents failed: {e}", f"/api/tasks/{task_id}/documents")
            state.has_error = True
            state.error_message = f"Link documents failed: {type(e).__name__}"
        finally:
            state.show_link_document_dialog = False
            state.link_document_selected = []
            state.link_document_search = ""

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

    # Phase 9: Reactive handlers for new filters
    @state.change("tasks_type_filter")
    def _on_tasks_type_filter(tasks_type_filter, **kwargs):
        if state.active_view == "tasks":
            state.tasks_page = 1
            load_tasks_page()

    @state.change("tasks_priority_filter")
    def _on_tasks_priority_filter(tasks_priority_filter, **kwargs):
        if state.active_view == "tasks":
            state.tasks_page = 1
            load_tasks_page()

    @state.change("tasks_created_after")
    def _on_tasks_created_after(tasks_created_after, **kwargs):
        if state.active_view == "tasks":
            state.tasks_page = 1
            load_tasks_page()

    @state.change("tasks_created_before")
    def _on_tasks_created_before(tasks_created_before, **kwargs):
        if state.active_view == "tasks":
            state.tasks_page = 1
            load_tasks_page()

    @state.change("tasks_completed_after")
    def _on_tasks_completed_after(tasks_completed_after, **kwargs):
        if state.active_view == "tasks":
            state.tasks_page = 1
            load_tasks_page()

    @state.change("tasks_completed_before")
    def _on_tasks_completed_before(tasks_completed_before, **kwargs):
        if state.active_view == "tasks":
            state.tasks_page = 1
            load_tasks_page()

    # Phase 9d: Session filter handler
    @state.change("tasks_session_filter")
    def _on_tasks_session_filter(tasks_session_filter, **kwargs):
        if state.active_view == "tasks":
            state.tasks_page = 1
            load_tasks_page()

    # Phase 9d: Server-side search handler (debounced via state.change)
    @state.change("tasks_search_query")
    def _on_tasks_search_query(tasks_search_query, **kwargs):
        if state.active_view == "tasks":
            state.tasks_page = 1
            load_tasks_page()

    # Phase 4: Workspace + Project + Hide Test filter handlers
    @state.change("tasks_workspace_filter")
    def _on_tasks_workspace_filter(tasks_workspace_filter, **kwargs):
        if state.active_view == "tasks":
            state.tasks_page = 1
            load_tasks_page()

    @state.change("tasks_project_filter")
    def _on_tasks_project_filter(tasks_project_filter, **kwargs):
        if state.active_view == "tasks":
            state.tasks_page = 1
            load_tasks_page()

    @state.change("tasks_hide_test")
    def _on_tasks_hide_test(tasks_hide_test, **kwargs):
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
            # Phase 9: Pass new filter params to API
            for param_name, state_key in [
                ("task_type", "tasks_type_filter"),
                ("priority", "tasks_priority_filter"),
                ("created_after", "tasks_created_after"),
                ("created_before", "tasks_created_before"),
                ("completed_after", "tasks_completed_after"),
                ("completed_before", "tasks_completed_before"),
                ("session_id", "tasks_session_filter"),
            ]:
                val = getattr(state, state_key, None)
                if val:
                    params[param_name] = val
            # Phase 4: Workspace filter (server-side via API)
            workspace_filter = getattr(state, 'tasks_workspace_filter', None)
            if workspace_filter:
                params["workspace_id"] = workspace_filter
            # Phase 4: Project filter → resolve to workspace_ids
            project_filter = getattr(state, 'tasks_project_filter', None)
            if project_filter and not workspace_filter:
                # Find all workspaces matching this project_id
                ws_map = _fetch_workspace_project_map(api_base_url)
                matching_ws = [
                    ws_id for ws_id, proj in ws_map.items()
                    if proj == project_filter
                ]
                if matching_ws:
                    params["workspace_id"] = matching_ws[0]
            # Phase 9d: Server-side search
            search_query = getattr(state, 'tasks_search_query', '') or ''
            if search_query.strip():
                params["search"] = search_query.strip()

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
                    _ws_map = _fetch_workspace_project_map(api_base_url)
                    enriched = _enrich_project_name(
                        _enrich_first_session(_enrich_doc_count(format_timestamps_in_list(
                            state.tasks, ["created_at", "completed_at", "claimed_at"]
                        ))),
                        _ws_map,
                    )
                    # Phase 4: Client-side hide test tasks filter
                    hide_test = getattr(state, 'tasks_hide_test', True)
                    if hide_test:
                        enriched = _filter_test_tasks(enriched)
                    state.tasks = enriched
                    # Phase 4: Populate workspace/project dropdown options
                    _populate_filter_options(_ws_map)
                    state.status_message = f"Loaded {len(state.tasks)} tasks"
                    # Phase 9e: Update histogram from loaded tasks
                    if _has_task_plotly():
                        hdata = _compute_histogram(state.tasks)
                        state.tasks_histogram_data = hdata
                        _update_histogram(hdata)
            state.is_loading = False
        except Exception as e:
            add_error_trace(state, f"Load tasks page failed: {e}", "/api/tasks")
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to load tasks: {type(e).__name__}"  # BUG-476-CTK-7

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
        # BUG-UI-DIV-001: Guard against division by zero
        per_page = state.tasks_per_page or 20
        total_pages = max(
            1,
            (state.tasks_pagination.get("total", 0) + per_page - 1)
            // per_page
        )
        if 1 <= page <= total_pages:
            state.tasks_page = page
            load_tasks_page()

    @ctrl.trigger("histogram_bar_click")
    def histogram_bar_click(click_data=None):
        """Phase 9e: Handle histogram bar click to filter table."""
        payload = _extract_histogram_filter(click_data)
        if payload:
            state.tasks_type_filter = payload.get("task_type")
            state.tasks_status_filter = payload.get("status")
            # Reactive handlers auto-trigger load_tasks_page()

    return {'load_tasks_page': load_tasks_page}
