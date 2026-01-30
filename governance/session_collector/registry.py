"""
Session Registry - Global session management.

Per RULE-032: Modularized from session_collector.py (591 lines).
Per GAP-SESSION-THOUGHT-001: State file for hook integration.
Contains: Global session registry and helper functions.
"""

import json
import logging
from datetime import date

logger = logging.getLogger(__name__)
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .collector import SessionCollector


# Global session registry for active sessions
_active_sessions: Dict[str, "SessionCollector"] = {}

# State file for hook integration (per GAP-SESSION-THOUGHT-001)
STATE_FILE = Path(__file__).parent.parent.parent / ".claude" / "hooks" / ".session_state.json"


def _persist_state() -> None:
    """Persist active session state to file for hook integration."""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "active_sessions": list(_active_sessions.keys()),
            "last_session": list(_active_sessions.keys())[-1] if _active_sessions else None,
            "count": len(_active_sessions)
        }
        STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception as e:
        logger.debug(f"Failed to save session state: {e}")


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
        _persist_state()  # Update state file for hooks

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
        _persist_state()  # Update state file for hooks
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
    _persist_state()  # Update state file for hooks
    return count
