"""
Agent Task Backlog State (TODO-6)
=================================
State transforms and helpers for task backlog management.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-004: Extracted from state.py

Created: 2024-12-28
"""

from typing import Dict, List, Any, Optional

from .constants import TASK_STATUS_COLORS


# =============================================================================
# STATE TRANSFORMS
# =============================================================================

def with_available_tasks(
    state: Dict[str, Any],
    tasks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Pure transform: add available tasks to state.

    Args:
        state: Current state
        tasks: List of available tasks

    Returns:
        New state with available_tasks
    """
    return {**state, 'available_tasks': tasks}


def with_claimed_tasks(
    state: Dict[str, Any],
    tasks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Pure transform: add claimed tasks to state.

    Args:
        state: Current state
        tasks: List of tasks claimed by current agent

    Returns:
        New state with claimed_tasks
    """
    return {**state, 'claimed_tasks': tasks}


def with_selected_task(
    state: Dict[str, Any],
    task: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Pure transform: select a task for detail view.

    Args:
        state: Current state
        task: Task to select, or None to deselect

    Returns:
        New state with selected_task and show_task_detail
    """
    return {
        **state,
        'selected_task': task,
        'show_task_detail': task is not None,
    }


def with_current_agent(
    state: Dict[str, Any],
    agent_id: Optional[str]
) -> Dict[str, Any]:
    """
    Pure transform: set current agent for claiming tasks.

    Args:
        state: Current state
        agent_id: Agent ID or None

    Returns:
        New state with current_agent_id
    """
    return {**state, 'current_agent_id': agent_id}


# =============================================================================
# UI HELPERS
# =============================================================================

def get_task_status_color(status: str) -> str:
    """
    Get color for task status.

    Args:
        status: Task status (TODO, IN_PROGRESS, DONE, BLOCKED)

    Returns:
        Vuetify color string
    """
    return TASK_STATUS_COLORS.get(status.upper(), 'grey')


def format_backlog_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format task for backlog display.

    Pure function: same input -> same output.

    Args:
        task: Task dict from API

    Returns:
        Formatted task for UI
    """
    status = task.get('status', 'TODO')
    return {
        'task_id': task.get('task_id', 'Unknown'),
        'description': task.get('description', ''),
        'body': task.get('body', ''),
        'phase': task.get('phase', ''),
        'status': status,
        'status_color': get_task_status_color(status),
        'agent_id': task.get('agent_id'),
        'claimed_at': task.get('claimed_at'),
        'completed_at': task.get('completed_at'),
        'linked_rules': task.get('linked_rules', []),
        'linked_sessions': task.get('linked_sessions', []),
        'gap_id': task.get('gap_id'),
        'evidence': task.get('evidence'),
    }
