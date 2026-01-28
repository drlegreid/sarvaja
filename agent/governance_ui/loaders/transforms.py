"""
Loader State Transform Functions.

Per GAP-UI-047: Reactive loaders with trace status.
Per DOC-SIZE-01-v1: File Size Limit (< 300 lines).

Provides pure functions to transform loading state:
- set_loading_start: Begin loading with trace
- set_loading_complete: Mark loading complete
- set_loading_error: Record loading error
- get_loader_state: Extract loader state from global state

Created: 2026-01-14
"""

from datetime import datetime
from typing import Any, Optional
import time
import uuid

from .loader_state import LoaderState, APITrace, ProgressInfo


def set_loading_start(
    state: Any,
    component: str,
    endpoint: str,
    method: str = "GET"
) -> None:
    """
    Set loading start state for a component.

    Updates the Trame state with loading=True and trace metadata.

    Args:
        state: Trame state object
        component: Component name (e.g., "rules", "sessions")
        endpoint: API endpoint being called
        method: HTTP method (default: GET)
    """
    trace = APITrace(
        endpoint=endpoint,
        method=method,
        status="loading",
        start_time=datetime.now(),
        request_id=str(uuid.uuid4())[:8],
    )

    loader_state = LoaderState(
        is_loading=True,
        trace=trace,
    )

    # Update state
    setattr(state, f"{component}_loading", True)
    setattr(state, f"{component}_loader", loader_state.to_dict())


def set_loading_complete(
    state: Any,
    component: str,
    status_code: int = 200,
    items_count: int = 0,
    start_time: Optional[float] = None
) -> None:
    """
    Set loading complete state for a component.

    Updates the Trame state with loading=False, success status, and duration.

    Args:
        state: Trame state object
        component: Component name
        status_code: HTTP response status code
        items_count: Number of items loaded
        start_time: Optional start time (timestamp) for duration calculation
    """
    end_time = datetime.now()

    # Get existing loader state
    existing = getattr(state, f"{component}_loader", {}) or {}
    trace_data = existing.get("trace", {}) or {}

    # Calculate duration if start_time provided
    duration_ms = 0
    if start_time:
        duration_ms = int((time.time() - start_time) * 1000)
    elif trace_data.get("start_time"):
        # Try to parse from existing trace
        try:
            start_dt = datetime.fromisoformat(trace_data["start_time"])
            duration_ms = int((end_time - start_dt).total_seconds() * 1000)
        except (ValueError, TypeError):
            pass

    # Build updated trace
    trace = APITrace(
        endpoint=trace_data.get("endpoint", ""),
        method=trace_data.get("method", "GET"),
        status="success" if status_code < 400 else "error",
        status_code=status_code,
        end_time=end_time,
        duration_ms=duration_ms,
        request_id=trace_data.get("request_id", ""),
    )

    loader_state = LoaderState(
        is_loading=False,
        has_error=(status_code >= 400),
        trace=trace,
        last_loaded=end_time,
        items_count=items_count,
    )

    # Update state
    setattr(state, f"{component}_loading", False)
    setattr(state, f"{component}_loader", loader_state.to_dict())


def set_loading_error(
    state: Any,
    component: str,
    error_message: str,
    status_code: int = 500,
    start_time: Optional[float] = None
) -> None:
    """
    Set loading error state for a component.

    Updates the Trame state with error information.

    Args:
        state: Trame state object
        component: Component name
        error_message: Error description
        status_code: HTTP error status code
        start_time: Optional start time for duration calculation
    """
    end_time = datetime.now()

    # Get existing loader state
    existing = getattr(state, f"{component}_loader", {}) or {}
    trace_data = existing.get("trace", {}) or {}

    # Calculate duration
    duration_ms = 0
    if start_time:
        duration_ms = int((time.time() - start_time) * 1000)

    # Build error trace
    trace = APITrace(
        endpoint=trace_data.get("endpoint", ""),
        method=trace_data.get("method", "GET"),
        status="error",
        status_code=status_code,
        end_time=end_time,
        duration_ms=duration_ms,
        request_id=trace_data.get("request_id", ""),
        error_message=error_message,
    )

    loader_state = LoaderState(
        is_loading=False,
        has_error=True,
        error_message=error_message,
        trace=trace,
    )

    # Update state
    setattr(state, f"{component}_loading", False)
    setattr(state, f"{component}_loader", loader_state.to_dict())


def get_loader_state(state: Any, component: str) -> LoaderState:
    """
    Get the LoaderState for a component.

    Extracts and parses loader state from Trame state.

    Args:
        state: Trame state object
        component: Component name

    Returns:
        LoaderState object
    """
    loader_dict = getattr(state, f"{component}_loader", {}) or {}
    return LoaderState.from_dict(loader_dict)


def update_progress(
    state: Any,
    component: str,
    progress_percent: int,
    items_loaded: int,
    total_items: Optional[int] = None
) -> None:
    """
    Update loading progress for a component.

    Used for paginated or streaming data loads.

    Args:
        state: Trame state object
        component: Component name
        progress_percent: Current progress (0-100)
        items_loaded: Number of items loaded so far
        total_items: Total expected items (if known)
    """
    existing = getattr(state, f"{component}_loader", {}) or {}

    progress = ProgressInfo(
        progress_percent=progress_percent,
        items_loaded=items_loaded,
        total_items=total_items,
    )

    loader_state = LoaderState.from_dict(existing)
    loader_state.progress = progress

    setattr(state, f"{component}_loader", loader_state.to_dict())


def format_trace_status(loader_state: LoaderState) -> str:
    """
    Format trace status for display.

    Returns human-readable trace status string.

    Args:
        loader_state: LoaderState object

    Returns:
        Formatted status string (e.g., "GET /api/rules - 150ms - 200 OK")
    """
    if not loader_state.trace:
        return ""

    trace = loader_state.trace
    parts = [trace.method, trace.endpoint]

    if trace.duration_ms > 0:
        parts.append(f"{trace.duration_ms}ms")

    if trace.status_code:
        status_text = "OK" if trace.status_code < 400 else "ERROR"
        parts.append(f"{trace.status_code} {status_text}")

    return " - ".join(parts)
