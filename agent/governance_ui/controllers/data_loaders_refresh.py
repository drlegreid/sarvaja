"""
Data Loader Refresh Controller
==============================
Full data refresh and traced GET helper for the dashboard.

Per DOC-SIZE-01-v1: Extracted from data_loaders.py.
"""

import time
import httpx
from typing import Any

from agent.governance_ui.trace_bar.transforms import (
    add_api_trace,
    add_error_trace,
)
from agent.governance_ui.utils import (
    format_timestamps_in_list,
    compute_session_duration,
    compute_session_metrics,
    compute_timeline_data,
)


def register_refresh_controllers(
    state: Any,
    ctrl: Any,
    api_base_url: str,
    infra_loaders: dict,
) -> dict:
    """Register refresh + sessions-list controllers.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls
        infra_loaders: Dict with 'load_infra_status' function

    Returns:
        Dict with 'load_sessions_list' function
    """

    def _traced_get(client: httpx.Client, endpoint: str) -> tuple:
        """Make a traced GET request. Returns (response, duration_ms)."""
        start = time.time()
        try:
            response = client.get(f"{api_base_url}{endpoint}")
            duration_ms = int((time.time() - start) * 1000)

            response_body = None
            try:
                response_body = response.json()
            except Exception:
                text = response.text[:500] if response.text else None
                if text:
                    response_body = {"_raw_text": text}

            add_api_trace(
                state, endpoint, "GET", response.status_code, duration_ms,
                request_body=None,
                response_body=response_body
            )
            return response, duration_ms
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            add_error_trace(state, f"GET {endpoint} failed: {str(e)}", endpoint)
            raise

    @ctrl.trigger("refresh_data")
    def refresh_data():
        """Refresh all data from REST API."""
        try:
            state.is_loading = True
            with httpx.Client(timeout=10.0) as client:
                try:
                    response, _ = _traced_get(client, "/api/rules")
                    if response.status_code == 200:
                        data = response.json()
                        rules = data.get("items", data) if isinstance(data, dict) else data
                        for r in rules:
                            r.setdefault("linked_tasks_count", r.get("linked_tasks_count", 0))
                            r.setdefault("linked_sessions_count", r.get("linked_sessions_count", 0))
                        state.rules = rules
                except Exception as e:
                    add_error_trace(state, f"Refresh rules failed: {e}", "/api/rules")

                try:
                    response, _ = _traced_get(client, "/api/decisions")
                    if response.status_code == 200:
                        data = response.json()
                        state.decisions = data.get("items", data) if isinstance(data, dict) else data
                except Exception as e:
                    add_error_trace(state, f"Refresh decisions failed: {e}", "/api/decisions")

                try:
                    page_size = getattr(state, 'tasks_per_page', 20)
                    response, _ = _traced_get(client, f"/api/tasks?limit={page_size}&offset=0")
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, dict) and "items" in data:
                            state.tasks = format_timestamps_in_list(
                                data["items"], ["created_at", "claimed_at", "completed_at"])
                            state.tasks_pagination = data.get("pagination", {})
                        else:
                            # BUG-REFRESH-001: Guard against non-list data (e.g. dict without "items")
                            items_list = data if isinstance(data, list) else []
                            state.tasks = items_list[:page_size] if len(items_list) > page_size else items_list
                            state.tasks_pagination = {
                                "total": len(items_list),
                                "offset": 0,
                                "limit": page_size,
                                "has_more": len(items_list) > page_size,
                                "returned": min(len(items_list), page_size),
                            }
                        # BUG-UI-TASKS-004: Enrich doc_count for Docs column
                        from agent.governance_ui.controllers.tasks import _enrich_doc_count
                        state.tasks = _enrich_doc_count(state.tasks)
                    state.tasks_page = 1
                except Exception as e:
                    add_error_trace(state, f"Refresh tasks failed: {e}", "/api/tasks")

                try:
                    response, _ = _traced_get(client, "/api/sessions?limit=100")
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get("items", data) if isinstance(data, dict) else data
                        # F.2: Compute duration + metrics before formatting
                        metrics = compute_session_metrics(items)
                        state.sessions_metrics_duration = metrics["duration"]
                        state.sessions_metrics_avg_tasks = metrics["avg_tasks"]
                        # P0-2: Prefer server-computed duration, fallback to local
                        for item in items:
                            if not item.get("duration"):
                                item["duration"] = compute_session_duration(
                                    item.get("start_time", ""), item.get("end_time", ""))
                        tl_vals, tl_labels = compute_timeline_data(items)
                        state.sessions_timeline_data = tl_vals
                        state.sessions_timeline_labels = tl_labels
                        agents = sorted(set(
                            s.get("agent_id") for s in items if s.get("agent_id")))
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
                        state.sessions = format_timestamps_in_list(
                            items, ["start_time", "end_time"])
                except Exception as e:
                    add_error_trace(state, f"Refresh sessions failed: {e}", "/api/sessions")

                try:
                    response, _ = _traced_get(client, "/api/agents")
                    if response.status_code == 200:
                        data = response.json()
                        state.agents = data.get("items", data) if isinstance(data, dict) else data
                except Exception as e:
                    add_error_trace(state, f"Refresh agents failed: {e}", "/api/agents")

            # Also refresh infra health for toolbar indicator
            try:
                infra_loaders['load_infra_status']()
            except Exception as e:
                add_error_trace(state, f"Refresh infra failed: {e}", "infra_status")

            state.is_loading = False
            state.status_message = "Data refreshed from API"
        except Exception as e:
            state.is_loading = False
            # BUG-UI-SILENT-FAIL-001: Use error_message not status_message for failures
            state.has_error = True
            state.error_message = f"API unavailable: {type(e).__name__}"  # BUG-476-CDR-1

    def load_sessions_list():
        """Load sessions list for dropdowns. Per UI-AUDIT-007."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/sessions?limit=100")
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", data) if isinstance(data, dict) else data
                    # F.2: Add duration to each session item
                    # P0-2: Prefer server-computed duration, fallback to local
                    for item in items:
                        if not item.get("duration"):
                            item["duration"] = compute_session_duration(
                                item.get("start_time", ""), item.get("end_time", ""))
                        # BUG-UI-SESSIONS-003: Derive source_type
                        if not item.get("source_type"):
                            sid = item.get("session_id", "")
                            if item.get("cc_session_uuid") or "-CC-" in sid:
                                item["source_type"] = "CC"
                            elif "-CHAT-" in sid or "-MCP-AUTO-" in sid:
                                item["source_type"] = "Chat"
                            else:
                                item["source_type"] = "API"
                    state.sessions = format_timestamps_in_list(
                        items, ["start_time", "end_time"])
        except Exception as e:
            add_error_trace(state, f"Load sessions list failed: {e}", "/api/sessions")
            if not state.sessions:
                state.sessions = []

    @ctrl.trigger("load_sessions_list")
    def trigger_load_sessions_list():
        """Trigger for loading sessions list."""
        load_sessions_list()

    return {
        'load_sessions_list': load_sessions_list,
    }
