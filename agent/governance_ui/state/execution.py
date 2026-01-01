"""
Task Execution State (ORCH-007)
===============================
State transforms and helpers for task execution log.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-004: Extracted from state.py

Created: 2024-12-28
"""

from typing import Dict, List, Any

from .constants import EXECUTION_EVENT_TYPES


# =============================================================================
# STATE TRANSFORMS
# =============================================================================

def with_task_execution_log(
    state: Dict[str, Any],
    log: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Set task execution log."""
    return {
        **state,
        'task_execution_log': log,
        'task_execution_loading': False,
        'show_task_execution': True,
    }


def with_task_execution_loading(state: Dict[str, Any]) -> Dict[str, Any]:
    """Set task execution loading state."""
    return {
        **state,
        'task_execution_loading': True,
        'task_execution_log': [],
    }


def with_task_execution_event(
    state: Dict[str, Any],
    event: Dict[str, Any]
) -> Dict[str, Any]:
    """Add event to task execution log."""
    new_log = [*state.get('task_execution_log', []), event]
    return {
        **state,
        'task_execution_log': new_log,
    }


def clear_task_execution(state: Dict[str, Any]) -> Dict[str, Any]:
    """Clear task execution log."""
    return {
        **state,
        'task_execution_log': [],
        'task_execution_loading': False,
        'show_task_execution': False,
    }


# =============================================================================
# UI HELPERS
# =============================================================================

def get_execution_event_style(event_type: str) -> Dict[str, str]:
    """Get icon and color for execution event type."""
    return EXECUTION_EVENT_TYPES.get(
        event_type,
        {'icon': 'mdi-circle', 'color': 'grey'}
    )


def format_execution_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Format execution event for display."""
    style = get_execution_event_style(event.get('event_type', 'unknown'))
    return {
        **event,
        'icon': style['icon'],
        'color': style['color'],
        'formatted_time': event.get('timestamp', '')[:19].replace('T', ' '),
    }
