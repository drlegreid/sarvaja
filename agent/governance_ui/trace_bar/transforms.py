"""
Trace Bar State Transform Functions.

Per GAP-UI-048: Bottom bar with technical traces.
Per DOC-SIZE-01-v1: File Size Limit (< 300 lines).

Created: 2026-01-14
"""

from datetime import datetime
from typing import Any, Optional

from .trace_event import TraceEvent, TraceType


MAX_TRACE_EVENTS = 100


def add_api_trace(
    state: Any,
    endpoint: str,
    method: str = "GET",
    status_code: int = 200,
    duration_ms: int = 0
) -> None:
    """
    Add an API call trace event.

    Args:
        state: Trame state object
        endpoint: API endpoint called
        method: HTTP method
        status_code: Response status code
        duration_ms: Request duration in milliseconds
    """
    event = TraceEvent(
        event_type=TraceType.API_CALL,
        message=f"{method} {endpoint}",
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        duration_ms=duration_ms,
    )

    _add_trace_event(state, event)


def add_ui_action_trace(
    state: Any,
    action: str,
    component: str,
    target: str = ""
) -> None:
    """
    Add a UI action trace event.

    Args:
        state: Trame state object
        action: Action type (click, input, navigate, etc.)
        component: Component name
        target: Target element/view
    """
    event = TraceEvent(
        event_type=TraceType.UI_ACTION,
        message=f"{action} on {component}",
        action=action,
        component=component,
        target=target,
    )

    _add_trace_event(state, event)


def add_error_trace(
    state: Any,
    error_message: str,
    endpoint: Optional[str] = None,
    status_code: Optional[int] = None
) -> None:
    """
    Add an error trace event.

    Args:
        state: Trame state object
        error_message: Error description
        endpoint: Optional endpoint that caused the error
        status_code: Optional HTTP status code
    """
    event = TraceEvent(
        event_type=TraceType.ERROR,
        message=error_message,
        error_message=error_message,
        endpoint=endpoint,
        status_code=status_code,
    )

    _add_trace_event(state, event)


def add_mcp_trace(
    state: Any,
    tool_name: str,
    duration_ms: int = 0,
    success: bool = True
) -> None:
    """
    Add an MCP tool call trace event.

    Args:
        state: Trame state object
        tool_name: MCP tool name
        duration_ms: Call duration
        success: Whether the call succeeded
    """
    status = "OK" if success else "ERROR"
    event = TraceEvent(
        event_type=TraceType.MCP_CALL,
        message=f"{tool_name} - {status}",
        duration_ms=duration_ms,
        status_code=200 if success else 500,
    )

    _add_trace_event(state, event)


def _add_trace_event(state: Any, event: TraceEvent) -> None:
    """
    Internal: Add trace event to state.

    Maintains max event limit and updates summary.
    """
    # Get current events
    events = list(getattr(state, 'trace_events', []) or [])

    # Add new event
    events.append(event.to_dict())

    # Limit to max events
    if len(events) > MAX_TRACE_EVENTS:
        events = events[-MAX_TRACE_EVENTS:]

    # Count errors (handle None status_code)
    def is_error_event(e: dict) -> bool:
        status_code = e.get('status_code')
        if status_code is not None and status_code >= 400:
            return True
        return e.get('event_type') == 'error'

    error_count = sum(1 for e in events if is_error_event(e))

    # Update state
    setattr(state, 'trace_events', events)
    setattr(state, 'trace_events_count', len(events))
    setattr(state, 'trace_error_count', error_count)
    setattr(state, 'trace_last_event', event.format_display())

    # Update summary
    summary = {
        "total": len(events),
        "errors": error_count,
        "api_calls": sum(1 for e in events if e.get('event_type') == 'api_call'),
        "ui_actions": sum(1 for e in events if e.get('event_type') == 'ui_action'),
    }
    setattr(state, 'trace_summary', summary)


def clear_traces(state: Any) -> None:
    """Clear all trace events."""
    setattr(state, 'trace_events', [])
    setattr(state, 'trace_events_count', 0)
    setattr(state, 'trace_error_count', 0)
    setattr(state, 'trace_last_event', None)
    setattr(state, 'trace_summary', {
        "total": 0,
        "errors": 0,
        "api_calls": 0,
        "ui_actions": 0,
    })


def toggle_trace_bar(state: Any) -> None:
    """Toggle trace bar expanded/collapsed state."""
    current = getattr(state, 'trace_bar_expanded', False)
    setattr(state, 'trace_bar_expanded', not current)


def set_trace_filter(state: Any, filter_type: Optional[str]) -> None:
    """
    Set trace event filter.

    Args:
        state: Trame state object
        filter_type: 'api_call', 'ui_action', 'error', 'mcp_call', or None for all
    """
    setattr(state, 'trace_filter', filter_type)


def get_filtered_traces(state: Any) -> list:
    """
    Get trace events filtered by current filter.

    Returns:
        List of trace event dictionaries
    """
    events = getattr(state, 'trace_events', []) or []
    filter_type = getattr(state, 'trace_filter', None)

    if filter_type is None:
        return events

    return [e for e in events if e.get('event_type') == filter_type]
