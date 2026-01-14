"""
Trace Bar Module.

Per GAP-UI-048: Bottom bar with technical traces.
Per DOC-SIZE-01-v1: File Size Limit (< 300 lines).

Created: 2026-01-14
"""

from .trace_event import TraceEvent, TraceType
from .trace_store import TraceStore, get_initial_trace_state
from .transforms import (
    add_api_trace,
    add_ui_action_trace,
    add_error_trace,
    clear_traces,
    toggle_trace_bar,
)

__all__ = [
    'TraceEvent',
    'TraceType',
    'TraceStore',
    'get_initial_trace_state',
    'add_api_trace',
    'add_ui_action_trace',
    'add_error_trace',
    'clear_traces',
    'toggle_trace_bar',
]
