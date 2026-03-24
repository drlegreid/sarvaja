"""
Tasks Controllers (GAP-FILE-005)
================================
Hub module for task controller registration.

Per DOC-SIZE-01-v1: CRUD in tasks_crud.py, lifecycle in tasks_lifecycle.py,
linking in tasks_linking.py, navigation in tasks_navigation.py,
helpers in tasks_helpers.py.

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
from .tasks_helpers import (  # noqa: F401 — re-export for backward compat
    _enrich_doc_count,
    _enrich_first_session,
    _fetch_workspace_project_map,
    _enrich_project_name,
    _TEST_PREFIXES,
    _filter_test_tasks,
)
from .tasks_crud import register_tasks_crud  # noqa: F401
from .tasks_lifecycle import register_tasks_lifecycle  # noqa: F401
from .tasks_linking import register_tasks_linking  # noqa: F401


def register_tasks_controllers(state: Any, ctrl: Any, api_base_url: str) -> dict:
    """Register task-related controllers with Trame."""

    # Register navigation handlers
    register_tasks_navigation(state, ctrl, api_base_url)

    # Register sub-modules (DI: hub's httpx/add_error_trace are patchable by tests)
    register_tasks_crud(
        state, ctrl, api_base_url,
        httpx_mod=httpx, error_trace_fn=add_error_trace,
    )
    register_tasks_lifecycle(
        state, ctrl, api_base_url,
        httpx_mod=httpx, error_trace_fn=add_error_trace,
    )
    register_tasks_linking(
        state, ctrl, api_base_url,
        httpx_mod=httpx, error_trace_fn=add_error_trace,
    )

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

    # BUG-P14.5: Return loader so dashboard can call it on initial tab switch
    return {'load_tasks_page': load_tasks_page}
