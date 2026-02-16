"""
Session Metrics Controllers (GAP-SESSION-METRICS-UI)
====================================================
Trame controller registration for session metrics dashboard.

Per RULE-012: DSP Semantic Code Structure
Per SESSION-METRICS-01-v1: Session analytics

Created: 2026-01-29
"""

import time
import httpx
from typing import Any

from agent.governance_ui.trace_bar.transforms import (
    add_api_trace,
    add_error_trace,
)


def register_metrics_controllers(
    state: Any,
    ctrl: Any,
    api_base_url: str,
) -> dict:
    """Register session metrics controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for REST API

    Returns:
        Dict of loader functions for view change handler
    """

    def load_metrics_data():
        """Load session metrics summary from REST API."""
        try:
            state.metrics_loading = True
            state.metrics_error = ''
            days = state.metrics_days_filter or 5

            with httpx.Client(timeout=30.0) as client:
                start = time.time()
                response = client.get(
                    f"{api_base_url}/api/metrics/summary",
                    params={"days": days},
                )
                duration_ms = int((time.time() - start) * 1000)

                response_body = None
                try:
                    response_body = response.json()
                except Exception as e:
                    # BUG-UI-SILENT-JSON-001: Log JSON parse failures
                    add_error_trace(state, f"Metrics JSON parse failed: {e}", "/api/metrics/summary")

                add_api_trace(
                    state, "/api/metrics/summary", "GET",
                    response.status_code, duration_ms,
                    response_body=response_body,
                )

                if response.status_code == 200 and response_body is not None:
                    state.metrics_data = response_body
                else:
                    state.metrics_data = None
                    state.metrics_error = f"API error: {response.status_code}"
        except Exception as e:
            add_error_trace(state, f"Load metrics failed: {e}", "/api/metrics/summary")
            state.metrics_data = None
            state.metrics_error = str(e)
        finally:
            state.metrics_loading = False

    @ctrl.trigger("load_metrics_data")
    def trigger_load_metrics_data():
        """Trigger for loading metrics data."""
        load_metrics_data()

    @ctrl.trigger("search_metrics")
    def search_metrics():
        """Search session content."""
        try:
            state.metrics_search_loading = True
            query = state.metrics_search_query or ""

            with httpx.Client(timeout=30.0) as client:
                start = time.time()
                response = client.get(
                    f"{api_base_url}/api/metrics/search",
                    params={"query": query, "max_results": 50},
                )
                duration_ms = int((time.time() - start) * 1000)

                response_body = None
                try:
                    response_body = response.json()
                except Exception as e:
                    # BUG-UI-SILENT-JSON-001: Log JSON parse failures
                    add_error_trace(state, f"Search metrics JSON parse failed: {e}", "/api/metrics/search")

                add_api_trace(
                    state, "/api/metrics/search", "GET",
                    response.status_code, duration_ms,
                    response_body=response_body,
                )

                if response.status_code == 200 and response_body:
                    state.metrics_search_results = response_body.get("results", [])
                    state.metrics_search_total = response_body.get("total_matches", 0)
                else:
                    state.metrics_search_results = []
                    state.metrics_search_total = 0
        except Exception as e:
            add_error_trace(state, f"Search metrics failed: {e}", "/api/metrics/search")
            state.metrics_search_results = []
            state.metrics_search_total = 0
        finally:
            state.metrics_search_loading = False

    @ctrl.trigger("load_metrics_timeline")
    def load_metrics_timeline():
        """Load activity timeline."""
        try:
            state.metrics_timeline_loading = True

            with httpx.Client(timeout=30.0) as client:
                start = time.time()
                response = client.get(
                    f"{api_base_url}/api/metrics/timeline",
                    params={"days": 30},
                )
                duration_ms = int((time.time() - start) * 1000)

                response_body = None
                try:
                    response_body = response.json()
                except Exception as e:
                    # BUG-UI-SILENT-JSON-001: Log JSON parse failures
                    add_error_trace(state, f"Timeline JSON parse failed: {e}", "/api/metrics/timeline")

                add_api_trace(
                    state, "/api/metrics/timeline", "GET",
                    response.status_code, duration_ms,
                    response_body=response_body,
                )

                if response.status_code == 200 and response_body:
                    state.metrics_timeline = response_body.get("timeline", [])
                else:
                    state.metrics_timeline = []
        except Exception as e:
            add_error_trace(state, f"Load timeline failed: {e}", "/api/metrics/timeline")
            state.metrics_timeline = []
        finally:
            state.metrics_timeline_loading = False

    return {
        'load_metrics_data': load_metrics_data,
    }
