"""
Session Registry - Global session management.

Per RULE-032: Modularized from session_collector.py (591 lines).
Contains: Global session registry and helper functions.
"""

from datetime import date
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .collector import SessionCollector


# Global session registry for active sessions
_active_sessions: Dict[str, "SessionCollector"] = {}


def get_or_create_session(topic: str, session_type: str = "general") -> "SessionCollector":
    """
    Get existing session or create new one.

    Args:
        topic: Session topic
        session_type: Type of session

    Returns:
        SessionCollector instance
    """
    # Import here to avoid circular imports
    from .collector import SessionCollector

    session_id = f"SESSION-{date.today()}-{topic.upper()}"

    if session_id not in _active_sessions:
        _active_sessions[session_id] = SessionCollector(topic, session_type)

    return _active_sessions[session_id]


def end_session(topic: str) -> Optional[str]:
    """
    End session and generate log.

    Args:
        topic: Session topic

    Returns:
        Path to generated log file, or None if session not found
    """
    session_id = f"SESSION-{date.today()}-{topic.upper()}"

    if session_id in _active_sessions:
        collector = _active_sessions.pop(session_id)
        log_path = collector.generate_session_log()
        collector.sync_to_chromadb()
        return log_path

    return None


def list_active_sessions() -> List[str]:
    """List all active session IDs."""
    return list(_active_sessions.keys())


def get_session(session_id: str) -> Optional["SessionCollector"]:
    """
    Get a specific session by ID.

    Args:
        session_id: Full session ID

    Returns:
        SessionCollector instance or None
    """
    return _active_sessions.get(session_id)


def clear_all_sessions() -> int:
    """
    Clear all active sessions (for testing).

    Returns:
        Number of sessions cleared
    """
    count = len(_active_sessions)
    _active_sessions.clear()
    return count
