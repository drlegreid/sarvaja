"""
Agent Chat State (ORCH-006)
===========================
State transforms and helpers for agent chat interface.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-004: Extracted from state.py

Created: 2024-12-28
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from .constants import CHAT_ROLE_COLORS, CHAT_STATUS_ICONS


# =============================================================================
# STATE TRANSFORMS
# =============================================================================

def with_chat_messages(
    state: Dict[str, Any],
    messages: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Pure transform: set chat messages.

    Args:
        state: Current state
        messages: List of chat messages

    Returns:
        New state with chat_messages
    """
    return {**state, 'chat_messages': messages}


def with_chat_message(
    state: Dict[str, Any],
    message: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Pure transform: append a chat message.

    Args:
        state: Current state
        message: Message to append

    Returns:
        New state with message appended
    """
    messages = list(state.get('chat_messages', []))
    messages.append(message)
    return {**state, 'chat_messages': messages}


def with_chat_loading(
    state: Dict[str, Any],
    loading: bool = True
) -> Dict[str, Any]:
    """
    Pure transform: set chat loading state.

    Args:
        state: Current state
        loading: Loading state

    Returns:
        New state with chat_loading
    """
    return {**state, 'chat_loading': loading}


def with_chat_input(
    state: Dict[str, Any],
    input_text: str
) -> Dict[str, Any]:
    """
    Pure transform: set chat input text.

    Args:
        state: Current state
        input_text: Input text

    Returns:
        New state with chat_input
    """
    return {**state, 'chat_input': input_text}


def with_chat_agent(
    state: Dict[str, Any],
    agent_id: Optional[str]
) -> Dict[str, Any]:
    """
    Pure transform: set selected chat agent.

    Args:
        state: Current state
        agent_id: Agent ID or None for auto

    Returns:
        New state with chat_selected_agent
    """
    return {**state, 'chat_selected_agent': agent_id}


def with_chat_session(
    state: Dict[str, Any],
    session_id: Optional[str]
) -> Dict[str, Any]:
    """
    Pure transform: set chat session ID.

    Args:
        state: Current state
        session_id: Session ID

    Returns:
        New state with chat_session_id
    """
    return {**state, 'chat_session_id': session_id}


def with_chat_task(
    state: Dict[str, Any],
    task_id: Optional[str]
) -> Dict[str, Any]:
    """
    Pure transform: set active task from chat.

    Args:
        state: Current state
        task_id: Task ID

    Returns:
        New state with chat_task_id
    """
    return {**state, 'chat_task_id': task_id}


# =============================================================================
# UI HELPERS
# =============================================================================

def get_chat_role_color(role: str) -> str:
    """
    Get color for chat message role.

    Args:
        role: Message role (user, agent, system, error)

    Returns:
        Vuetify color string
    """
    return CHAT_ROLE_COLORS.get(role.lower(), 'grey')


def get_chat_status_icon(status: str) -> str:
    """
    Get icon for chat message status.

    Args:
        status: Message status

    Returns:
        MDI icon string
    """
    return CHAT_STATUS_ICONS.get(status.lower(), 'mdi-help-circle')


def format_chat_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format chat message for display.

    Pure function: same input -> same output.

    Args:
        message: Message dict

    Returns:
        Formatted message for UI
    """
    role = message.get('role', 'user')
    status = message.get('status', 'complete')

    return {
        'id': message.get('id', ''),
        'role': role,
        'content': message.get('content', ''),
        'timestamp': message.get('timestamp', ''),
        'agent_id': message.get('agent_id'),
        'agent_name': message.get('agent_name', 'Agent'),
        'task_id': message.get('task_id'),
        'status': status,
        'role_color': get_chat_role_color(role),
        'status_icon': get_chat_status_icon(status),
        'is_user': role == 'user',
        'is_agent': role == 'agent',
    }


# =============================================================================
# MESSAGE FACTORIES
# =============================================================================

def create_user_message(content: str, timestamp: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a user message dict.

    Args:
        content: Message content
        timestamp: Optional timestamp (defaults to now)

    Returns:
        User message dict
    """
    return {
        'id': f"MSG-{uuid.uuid4().hex[:8].upper()}",
        'role': 'user',
        'content': content,
        'timestamp': timestamp or datetime.now().isoformat(),
        'status': 'complete',
    }


def create_agent_message(
    content: str,
    agent_id: str,
    agent_name: str = 'Agent',
    task_id: Optional[str] = None,
    status: str = 'complete',
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an agent message dict.

    Args:
        content: Message content
        agent_id: Agent ID
        agent_name: Agent display name
        task_id: Optional task ID
        status: Message status
        timestamp: Optional timestamp

    Returns:
        Agent message dict
    """
    return {
        'id': f"MSG-{uuid.uuid4().hex[:8].upper()}",
        'role': 'agent',
        'content': content,
        'timestamp': timestamp or datetime.now().isoformat(),
        'agent_id': agent_id,
        'agent_name': agent_name,
        'task_id': task_id,
        'status': status,
    }


def create_system_message(content: str, timestamp: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a system message dict.

    Args:
        content: Message content
        timestamp: Optional timestamp

    Returns:
        System message dict
    """
    return {
        'id': f"MSG-{uuid.uuid4().hex[:8].upper()}",
        'role': 'system',
        'content': content,
        'timestamp': timestamp or datetime.now().isoformat(),
        'status': 'complete',
    }
