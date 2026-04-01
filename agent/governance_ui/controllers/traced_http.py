"""
Shared Traced HTTP Utilities.

Per EPIC-PERF-TELEM-V1 P5: Extracted from data_loaders_refresh.py.
Every dashboard HTTP call is wrapped to record duration + status in the
trace bar via add_api_trace / add_error_trace.

Usage:
    from agent.governance_ui.controllers.traced_http import traced_get
    with httpx.Client(timeout=10.0) as client:
        resp, dur = traced_get(state, client, api_base_url, "/api/tasks")
"""

import time
from typing import Any, Optional

from agent.governance_ui.trace_bar.transforms import add_api_trace, add_error_trace


def _safe_json(response) -> Optional[dict]:
    """Extract JSON body safely, falling back to truncated text."""
    try:
        body = response.json()
        # Validate it's actually JSON-serializable (guards against mock objects)
        if not isinstance(body, (dict, list, str, int, float, bool, type(None))):
            return None
        return body
    except Exception:
        try:
            text = response.text[:500] if response.text else None
            if text and isinstance(text, str):
                return {"_raw_text": text}
        except Exception:
            pass
        return None


def traced_get(
    state: Any,
    client: Any,
    api_base_url: str,
    endpoint: str,
    params: Optional[dict] = None,
) -> tuple:
    """Make a traced GET request. Returns (response, duration_ms)."""
    start = time.time()
    try:
        response = client.get(f"{api_base_url}{endpoint}", params=params)
        duration_ms = int((time.time() - start) * 1000)
        add_api_trace(
            state, endpoint, "GET", response.status_code, duration_ms,
            request_body=None, response_body=_safe_json(response),
        )
        return response, duration_ms
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        add_error_trace(state, f"GET {endpoint} failed: {e}", endpoint)
        raise


def traced_post(
    state: Any,
    client: Any,
    api_base_url: str,
    endpoint: str,
    json: Optional[dict] = None,
) -> tuple:
    """Make a traced POST request. Returns (response, duration_ms)."""
    start = time.time()
    try:
        response = client.post(f"{api_base_url}{endpoint}", json=json)
        duration_ms = int((time.time() - start) * 1000)
        add_api_trace(
            state, endpoint, "POST", response.status_code, duration_ms,
            request_body=json, response_body=_safe_json(response),
        )
        return response, duration_ms
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        add_error_trace(state, f"POST {endpoint} failed: {e}", endpoint)
        raise


def traced_put(
    state: Any,
    client: Any,
    api_base_url: str,
    endpoint: str,
    json: Optional[dict] = None,
) -> tuple:
    """Make a traced PUT request. Returns (response, duration_ms)."""
    start = time.time()
    try:
        response = client.put(f"{api_base_url}{endpoint}", json=json)
        duration_ms = int((time.time() - start) * 1000)
        add_api_trace(
            state, endpoint, "PUT", response.status_code, duration_ms,
            request_body=json, response_body=_safe_json(response),
        )
        return response, duration_ms
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        add_error_trace(state, f"PUT {endpoint} failed: {e}", endpoint)
        raise


def traced_delete(
    state: Any,
    client: Any,
    api_base_url: str,
    endpoint: str,
) -> tuple:
    """Make a traced DELETE request. Returns (response, duration_ms)."""
    start = time.time()
    try:
        response = client.delete(f"{api_base_url}{endpoint}")
        duration_ms = int((time.time() - start) * 1000)
        add_api_trace(
            state, endpoint, "DELETE", response.status_code, duration_ms,
            request_body=None, response_body=_safe_json(response),
        )
        return response, duration_ms
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        add_error_trace(state, f"DELETE {endpoint} failed: {e}", endpoint)
        raise
