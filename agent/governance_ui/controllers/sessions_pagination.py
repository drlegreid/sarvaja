"""
Session Pagination & Filter Controllers.

Per DOC-SIZE-01-v1: Extracted from sessions.py (397 lines).
Pagination, column filters, reactive handlers, pivot view.
"""

import httpx
from typing import Any, Callable

from agent.governance_ui.trace_bar.transforms import add_error_trace
from agent.governance_ui.utils import (
    compute_session_metrics, compute_session_duration,
    format_timestamps_in_list, compute_timeline_data, compute_pivot_data,
)
from agent.governance_ui.views.sessions.timeline import (
    compute_timeline_plotly_data, has_plotly, update_plotly_timeline,
)


def register_sessions_pagination(
    state: Any, ctrl: Any, api_base_url: str
) -> Callable:
    """Register session pagination and filter controllers.

    Returns:
        load_sessions_page function for use by CRUD handlers.
    """

    def _apply_session_metrics(items):
        """Apply session metrics to state from raw items."""
        metrics = compute_session_metrics(items)
        state.sessions_metrics_duration = metrics["duration"]
        state.sessions_metrics_avg_tasks = metrics["avg_tasks"]

    def _update_timeline_and_metrics(client, base_url):
        """Fetch all sessions for timeline + global metrics.

        BUG-UI-SESSIONS-001 fix: Metrics must be computed from ALL sessions,
        not just the current page (which may only have test sessions with 0s
        durations, showing '0h' instead of the real 14000+ hours).
        """
        try:
            resp = client.get(f"{base_url}/api/sessions", params={"limit": 200, "exclude_test": "true"})
            if resp.status_code == 200:
                data = resp.json()
                all_items = data.get("items", data) if isinstance(data, dict) else data
                # Compute metrics from ALL sessions (not just current page)
                _apply_session_metrics(all_items)
                tl_values, tl_labels = compute_timeline_data(all_items)
                state.sessions_timeline_data = tl_values
                state.sessions_timeline_labels = tl_labels
                if has_plotly():
                    plotly_data = compute_timeline_plotly_data(all_items)
                    update_plotly_timeline(plotly_data)
        except Exception as e:
            add_error_trace(state, f"Load timeline/metrics failed: {e}", "/api/sessions")

    def load_sessions_page():
        """Load sessions with pagination and filters (GAP-UI-036, F.1)."""
        try:
            state.is_loading = True
            # BUG-UI-SESSION-003: Clear stale error state on reload
            state.has_error = False
            offset = (state.sessions_page - 1) * state.sessions_per_page
            params = {"offset": offset, "limit": state.sessions_per_page}
            # F.1: Apply column filters to API query
            if getattr(state, 'sessions_filter_status', None):
                params["status"] = state.sessions_filter_status
            if getattr(state, 'sessions_filter_agent', None):
                params["agent_id"] = state.sessions_filter_agent
            if getattr(state, 'sessions_date_from', None):
                params["date_from"] = state.sessions_date_from
            if getattr(state, 'sessions_date_to', None):
                params["date_to"] = state.sessions_date_to
            # Server-side keyword search (GAP-SESSION-SEARCH-001)
            if getattr(state, 'sessions_search_query', None):
                params["search"] = state.sessions_search_query
            # Exclude test artifacts from UI by default
            params["exclude_test"] = "true"
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/sessions", params=params)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and "items" in data:
                        items = data["items"]
                        state.sessions_pagination = data.get("pagination", {
                            "total": data.get("total", 0), "offset": offset,
                            "limit": state.sessions_per_page,
                            "has_more": data.get("has_more", False),
                            "returned": len(items),
                        })
                    else:
                        items = data
                        state.sessions_pagination = {
                            "total": len(items), "offset": 0,
                            "limit": len(items), "has_more": False,
                            "returned": len(items),
                        }
                    # GAP-UI-EXP-005: Normalize date->start_time for legacy data
                    for item in items:
                        if not item.get("start_time") and item.get("date"):
                            item["start_time"] = item["date"]
                    # F.2: Add duration column to each item
                    for item in items:
                        item["duration"] = compute_session_duration(
                            item.get("start_time", ""), item.get("end_time", ""))
                    # F.3: Timeline + metrics from ALL sessions (BUG-UI-SESSIONS-001)
                    _update_timeline_and_metrics(client, api_base_url)
                    # F.1: Extract unique agent options for filter dropdown
                    agents = sorted(set(
                        s.get("agent_id") for s in items
                        if s.get("agent_id")
                    ))
                    state.sessions_agent_options = agents
                    # BUG-UI-SESSIONS-003: Derive source_type for display
                    for item in items:
                        if not item.get("source_type"):
                            sid = item.get("session_id", "")
                            if item.get("cc_session_uuid") or "-CC-" in sid:
                                item["source_type"] = "CC"
                            elif "-CHAT-" in sid or "-MCP-AUTO-" in sid:
                                item["source_type"] = "Chat"
                            else:
                                item["source_type"] = "API"
                    # Format timestamps and set state
                    items = format_timestamps_in_list(
                        items, ["start_time", "end_time"])
                    # BUG-UI-SESSIONS-005: Annotate missing end_time (after formatting)
                    for item in items:
                        if not item.get("end_time"):
                            status = (item.get("status") or "").upper()
                            if status in ("COMPLETED", "CLOSED"):
                                item["end_time"] = "(completed)"
                            elif status == "ACTIVE":
                                item["end_time"] = "ongoing"
                    state.sessions = items
            state.is_loading = False
        except Exception as e:
            add_error_trace(state, f"Load sessions page failed: {e}", "/api/sessions")
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to load sessions: {type(e).__name__}"  # BUG-476-CSP-1

    @ctrl.trigger("sessions_prev_page")
    def sessions_prev_page():
        """Go to previous page of sessions (GAP-UI-036)."""
        if state.sessions_page > 1:
            state.sessions_page -= 1
            load_sessions_page()

    @ctrl.trigger("sessions_next_page")
    def sessions_next_page():
        """Go to next page of sessions (GAP-UI-036)."""
        if state.sessions_pagination.get("has_more", False):
            state.sessions_page += 1
            load_sessions_page()

    @ctrl.trigger("sessions_change_page_size")
    def sessions_change_page_size():
        """Change sessions items per page and reload (GAP-UI-036)."""
        state.sessions_page = 1
        load_sessions_page()

    @ctrl.trigger("sessions_apply_filters")
    def sessions_apply_filters():
        """F.1: Apply column filters and reload sessions."""
        from governance.middleware.dashboard_log import log_action
        log_action("sessions", "filter", status=getattr(state, "sessions_filter_status", None),
                   agent=getattr(state, "sessions_filter_agent", None))
        state.sessions_page = 1
        load_sessions_page()

    # F.1: Reactive filter handlers
    @state.change("sessions_filter_status")
    def _on_filter_status_change(sessions_filter_status, **kwargs):
        state.sessions_page = 1
        load_sessions_page()

    @state.change("sessions_filter_agent")
    def _on_filter_agent_change(sessions_filter_agent, **kwargs):
        state.sessions_page = 1
        load_sessions_page()

    @state.change("sessions_date_from")
    def _on_date_from_change(sessions_date_from, **kwargs):
        state.sessions_page = 1
        load_sessions_page()

    @state.change("sessions_date_to")
    def _on_date_to_change(sessions_date_to, **kwargs):
        state.sessions_page = 1
        load_sessions_page()

    @state.change("sessions_search_query")
    def _on_search_query_change(sessions_search_query, **kwargs):
        """Server-side search: reset to page 1 and reload."""
        state.sessions_page = 1
        load_sessions_page()

    @ctrl.trigger("sessions_clear_date_filter")
    def sessions_clear_date_filter():
        """Clear date range filter from histogram selection."""
        state.sessions_date_from = None
        state.sessions_date_to = None

    @ctrl.trigger("sessions_set_date_filter")
    def sessions_set_date_filter(date_from=None, date_to=None):
        """Set date range filter (from histogram bar click)."""
        state.sessions_date_from = date_from
        state.sessions_date_to = date_to

    @ctrl.trigger("sessions_toggle_view")
    def sessions_toggle_view(new_value=None):
        """F.4: Toggle between table and pivot view.
        BUG-UI-SESSIONS-001: Accept new_value from VBtnToggle update event."""
        if new_value:
            state.sessions_view_mode = new_value
        if state.sessions_view_mode == "pivot":
            _compute_pivot()

    @state.change("sessions_view_mode")
    def _on_view_mode_change(sessions_view_mode, **kwargs):
        if sessions_view_mode == "pivot":
            _compute_pivot()

    @ctrl.trigger("sessions_compute_pivot")
    def sessions_compute_pivot_trigger():
        """F.4: Recompute pivot data when group-by changes."""
        _compute_pivot()

    @state.change("sessions_pivot_group_by")
    def _on_pivot_group_change(sessions_pivot_group_by, **kwargs):
        if state.sessions_view_mode == "pivot":
            _compute_pivot()

    def _compute_pivot():
        """Compute pivot aggregations from current session data."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{api_base_url}/api/sessions",
                    params={"limit": 200, "exclude_test": "true"}
                )
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", data) if isinstance(data, dict) else data
                    group_by = getattr(state, 'sessions_pivot_group_by', 'agent_id')
                    state.sessions_pivot_data = compute_pivot_data(items, group_by)
        except Exception as e:
            add_error_trace(state, f"Compute pivot failed: {e}", "/api/sessions")
            state.sessions_pivot_data = []

    return load_sessions_page
