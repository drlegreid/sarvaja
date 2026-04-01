"""
Task CRUD Controllers
=====================
Controller functions for task select, create, delete, edit operations.

Per DOC-SIZE-01-v1: Extracted from tasks.py.
Per EPIC-PERF-TELEM-V1 P4: select_task uses ThreadPoolExecutor for parallel
sub-loaders. Fixes early-return bug (timeline+comments skipped in success path).
Per EPIC-PERF-TELEM-V1 P5: All HTTP calls traced via traced_http; log_action
for select/create/update/delete.
"""

import httpx as _httpx
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from agent.governance_ui.trace_bar.transforms import add_error_trace as _add_error_trace
from agent.governance_ui.controllers.traced_http import (
    traced_get as _traced_get,
    traced_post as _traced_post,
    traced_put as _traced_put,
    traced_delete as _traced_delete,
)
from governance.middleware.dashboard_log import log_action
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

    # ── Parallel fetch helpers (pure HTTP, traced via P5) ──────

    def _fetch_task_execution(task_id):
        """Fetch execution log. Returns data dict. Traced via traced_http."""
        try:
            with httpx.Client(timeout=10.0) as client:
                resp, _ = _traced_get(
                    state, client, api_base_url,
                    f"/api/tasks/{task_id}/execution")
                if resp.status_code == 200:
                    return {"events": resp.json().get("events", [])}
        except Exception:
            pass  # traced_get already called add_error_trace
        return {}

    def _fetch_task_evidence(task_id):
        """Fetch evidence files. Returns data dict. Traced via traced_http."""
        try:
            with httpx.Client(timeout=10.0) as client:
                resp, _ = _traced_get(
                    state, client, api_base_url,
                    f"/api/tasks/{task_id}/evidence/rendered")
                if resp.status_code == 200:
                    return {"evidence_files": resp.json().get("evidence_files", [])}
        except Exception:
            pass  # traced_get already called add_error_trace
        return {}

    def _fetch_task_timeline(task_id):
        """Fetch timeline entries. Returns data dict. Traced via traced_http."""
        try:
            with httpx.Client(timeout=15.0) as client:
                resp, _ = _traced_get(
                    state, client, api_base_url,
                    f"/api/tasks/{task_id}/timeline",
                    params={"per_page": 50})
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "entries": data.get("entries", []),
                        "total": data.get("total", 0),
                        "has_more": data.get("has_more", False),
                    }
        except Exception:
            pass  # traced_get already called add_error_trace
        return {}

    def _fetch_task_comments(task_id):
        """Fetch comments. Returns data dict. Traced via traced_http."""
        try:
            with httpx.Client(timeout=10.0) as client:
                resp, _ = _traced_get(
                    state, client, api_base_url,
                    f"/api/tasks/{task_id}/comments")
                if resp.status_code == 200:
                    return {"comments": resp.json().get("comments", [])}
        except Exception:
            pass  # traced_get already called add_error_trace
        return {}

    def _fetch_task_audit(task_id, page=1, per_page=20, action_type=None):
        """Fetch audit trail entries. Returns data list. Traced via traced_http."""
        try:
            params = {"limit": per_page, "offset": (page - 1) * per_page}
            if action_type:
                params["action_type"] = action_type
            with httpx.Client(timeout=10.0) as client:
                resp, _ = _traced_get(
                    state, client, api_base_url,
                    f"/api/audit/{task_id}", params=params)
                if resp.status_code == 200:
                    return {"entries": resp.json()}
        except Exception:
            pass  # traced_get already called add_error_trace
        return {}

    @ctrl.trigger("select_task")
    def select_task(task_id):
        """Handle task selection for detail view.

        P4: Parallel sub-loaders via ThreadPoolExecutor.
        Bugfix: Always loads ALL 4 sub-loaders (execution, evidence,
        timeline, comments) — fixes early-return that skipped timeline+comments.
        """
        # BUG-UI-STALE-DETAIL-004: Clear prior task detail state before loading
        state.edit_task_mode = False
        state.task_execution_log = []
        state.show_task_execution = False
        state.show_task_execution_inline = False  # BUG-TASK-POPUP-001
        state.task_evidence_files = []
        state.task_evidence_loading = True
        state.task_execution_loading = True
        state.task_timeline_loading = True
        state.task_comments_loading = True
        state.task_audit_entries = []
        state.task_audit_loading = True
        state.task_audit_page = 1
        state.task_audit_filter_action = None
        state.nav_source_view = None
        state.nav_source_id = None
        state.nav_source_label = None

        log_action("tasks", "select", task_id=task_id)

        # Step 1: Synchronous detail fetch (sets selected_task for UI)
        detail_ok = False
        try:
            with httpx.Client(timeout=10.0) as client:
                response, _ = _traced_get(
                    state, client, api_base_url, f"/api/tasks/{task_id}")
                if response.status_code == 200:
                    state.selected_task = response.json()
                    state.show_task_detail = True
                    detail_ok = True
        except Exception:
            pass  # traced_get already called add_error_trace

        if not detail_ok:
            for task in state.tasks:
                if task.get('task_id') == task_id or task.get('id') == task_id:
                    state.selected_task = task
                    state.show_task_detail = True
                    break

        # Step 2: Fire 5 sub-loaders in parallel (ALWAYS — fixes early-return bug)
        with ThreadPoolExecutor(max_workers=5) as executor:
            f_exec = executor.submit(_fetch_task_execution, task_id)
            f_evid = executor.submit(_fetch_task_evidence, task_id)
            f_time = executor.submit(_fetch_task_timeline, task_id)
            f_comm = executor.submit(_fetch_task_comments, task_id)
            f_audit = executor.submit(_fetch_task_audit, task_id)

        # Step 3: Apply results on main thread (Trame state NOT thread-safe)
        exec_result = f_exec.result()
        state.task_execution_log = exec_result.get("events", [])
        state.show_task_execution_inline = True  # BUG-TASK-POPUP-001
        state.task_execution_loading = False

        evid_result = f_evid.result()
        state.task_evidence_files = evid_result.get("evidence_files", [])
        state.task_evidence_loading = False

        time_result = f_time.result()
        state.task_timeline_entries = time_result.get("entries", [])
        state.task_timeline_total = time_result.get("total", 0)
        state.task_timeline_has_more = time_result.get("has_more", False)
        state.task_timeline_page = 1
        state.show_task_timeline_inline = False
        state.task_timeline_loading = False

        comm_result = f_comm.result()
        state.task_comments = comm_result.get("comments", [])
        state.task_comments_loading = False

        audit_result = f_audit.result()
        state.task_audit_entries = audit_result.get("entries", [])
        state.show_task_audit_inline = True
        state.task_audit_loading = False

    @ctrl.trigger("load_task_audit")
    def load_task_audit(task_id):
        """Explicit reload of task audit trail (refresh / filter / page change)."""
        if not task_id:
            return
        try:
            state.task_audit_loading = True
            page = state.task_audit_page or 1
            per_page = state.task_audit_per_page or 20
            action_filter = state.task_audit_filter_action or None
            result = _fetch_task_audit(task_id, page, per_page, action_filter)
            state.task_audit_entries = result.get("entries", [])
        except Exception:
            state.task_audit_entries = []
        finally:
            state.task_audit_loading = False

    @ctrl.trigger("load_task_timeline")
    def load_task_timeline(task_id):
        """Explicit reload of task timeline (refresh button / filter change)."""
        if not task_id:
            return
        try:
            state.task_timeline_loading = True
            page = state.task_timeline_page or 1
            params = {"page": page, "per_page": 50}
            filter_types = state.task_timeline_filter_types or []
            if filter_types:
                params["entry_types"] = ",".join(filter_types)
            with httpx.Client(timeout=15.0) as client:
                response, _ = _traced_get(
                    state, client, api_base_url,
                    f"/api/tasks/{task_id}/timeline", params=params)
                if response.status_code == 200:
                    data = response.json()
                    state.task_timeline_entries = data.get("entries", [])
                    state.task_timeline_total = data.get("total", 0)
                    state.task_timeline_has_more = data.get("has_more", False)
        except Exception:
            pass  # traced_get already called add_error_trace
        finally:
            state.task_timeline_loading = False

    def _auto_load_task_comments(task_id):
        """Auto-load comments when a task is selected (P19)."""
        try:
            state.task_comments_loading = True
            state.task_comments = []
            with httpx.Client(timeout=10.0) as client:
                response, _ = _traced_get(
                    state, client, api_base_url,
                    f"/api/tasks/{task_id}/comments")
                if response.status_code == 200:
                    state.task_comments = response.json().get("comments", [])
        except Exception:
            state.task_comments = []
        finally:
            state.task_comments_loading = False

    @ctrl.trigger("load_task_comments")
    def load_task_comments(task_id):
        """Explicit reload of task comments."""
        _auto_load_task_comments(task_id)

    @ctrl.trigger("post_task_comment")
    def post_task_comment(task_id, body):
        """Post a new comment to a task."""
        if not task_id or not body or not body.strip():
            return
        try:
            state.task_comment_submitting = True
            with httpx.Client(timeout=10.0) as client:
                response, _ = _traced_post(
                    state, client, api_base_url,
                    f"/api/tasks/{task_id}/comments",
                    json={"body": body.strip(), "author": "code-agent"})
                if response.status_code == 201:
                    state.task_comment_input = ""
                    _auto_load_task_comments(task_id)
        except Exception:
            pass  # traced_post already called add_error_trace
        finally:
            state.task_comment_submitting = False

    @ctrl.trigger("delete_task_comment")
    def delete_task_comment(task_id, comment_id):
        """Delete a comment from a task."""
        if not task_id or not comment_id:
            return
        try:
            with httpx.Client(timeout=10.0) as client:
                response, _ = _traced_delete(
                    state, client, api_base_url,
                    f"/api/tasks/{task_id}/comments/{comment_id}")
                if response.status_code == 200:
                    _auto_load_task_comments(task_id)
        except Exception:
            pass  # traced_delete already called add_error_trace

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
        state.task_timeline_entries = []
        state.show_task_timeline_inline = False
        state.task_timeline_page = 1
        state.task_comments = []
        state.task_comment_input = ''
        state.task_audit_entries = []
        state.task_audit_loading = False
        state.show_task_audit_inline = False
        state.task_audit_page = 1
        state.task_audit_filter_action = None
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
            log_action("tasks", "delete", task_id=task_id)
            with httpx.Client(timeout=10.0) as client:
                response, _ = _traced_delete(
                    state, client, api_base_url, f"/api/tasks/{task_id}")
                if response.status_code == 204:
                    state.status_message = f"Task {task_id} deleted successfully"
                    page_size = getattr(state, 'tasks_per_page', 20)
                    offset = (getattr(state, 'tasks_page', 1) - 1) * page_size
                    tasks_response, _ = _traced_get(
                        state, client, api_base_url, "/api/tasks",
                        params={"limit": page_size, "offset": offset})
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
                        tasks_response, _ = _traced_get(
                            state, client, api_base_url, "/api/tasks",
                            params={"limit": page_size, "offset": offset})
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
            # EPIC-TASK-TAXONOMY-V2: Populate tag fields
            state.edit_task_layer = state.selected_task.get('layer') or None
            state.edit_task_concern = state.selected_task.get('concern') or None
            state.edit_task_method = state.selected_task.get('method') or None

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
            log_action("tasks", "update", task_id=task_id)
            update_data = {
                "description": description,
                "phase": (state.edit_task_phase or "P10").strip(),
                "status": (state.edit_task_status or "TODO").strip(),
                "agent_id": (state.edit_task_agent or "").strip() or None,
                "body": (getattr(state, 'edit_task_body', '') or "").strip() or None,
                "summary": (getattr(state, 'edit_task_summary', '') or "").strip() or None,
                "priority": getattr(state, 'edit_task_priority', None) or None,
                "task_type": getattr(state, 'edit_task_type', None) or None,
                "resolution_notes": (getattr(state, 'edit_task_resolution_notes', '') or "").strip() or None,
                # EPIC-TASK-TAXONOMY-V2: Orthogonal tag dimensions
                "layer": getattr(state, 'edit_task_layer', None) or None,
                "concern": getattr(state, 'edit_task_concern', None) or None,
                "method": getattr(state, 'edit_task_method', None) or None,
            }
            with httpx.Client(timeout=10.0) as client:
                response, _ = _traced_put(
                    state, client, api_base_url,
                    f"/api/tasks/{task_id}", json=update_data)
                if response.status_code == 200:
                    state.status_message = f"Task {task_id} updated successfully"
                    page_size = getattr(state, 'tasks_per_page', 20)
                    offset = (getattr(state, 'tasks_page', 1) - 1) * page_size
                    tasks_response, _ = _traced_get(
                        state, client, api_base_url, "/api/tasks",
                        params={"limit": page_size, "offset": offset})
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
            log_action("tasks", "create")
            task_data = {
                "description": description.strip(),
                "phase": phase.strip() or "P10",
                "status": "TODO",
                "agent_id": getattr(state, 'form_task_agent', '') or None,
                "body": getattr(state, 'form_task_body', '') or None,
                "priority": getattr(state, 'form_task_priority', None),
                "task_type": task_type,
                # EPIC-TASK-TAXONOMY-V2: Orthogonal tag dimensions
                "layer": getattr(state, 'form_task_layer', None) or None,
                "concern": getattr(state, 'form_task_concern', None) or None,
                "method": getattr(state, 'form_task_method', None) or None,
            }
            # Only include task_id if user provided one
            if task_id.strip():
                task_data["task_id"] = task_id.strip()

            with httpx.Client(timeout=10.0) as client:
                response, _ = _traced_post(
                    state, client, api_base_url, "/api/tasks", json=task_data)
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
                    tasks_response, _ = _traced_get(
                        state, client, api_base_url, "/api/tasks",
                        params={"limit": page_size, "offset": offset})
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
