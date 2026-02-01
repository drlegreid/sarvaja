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

        # Auto-link evidence and rules to session in TypeDB
        _auto_link_session_evidence(session_id, log_path, collector)

        return log_path

    return None


def _auto_link_session_evidence(
    session_id: str, log_path: str, collector: "SessionCollector"
) -> None:
    """
    Auto-link evidence file and applied rules to session in TypeDB.

    Called after session_end to populate has-evidence and
    session-applied-rule relations automatically.
    """
    try:
        from governance.client import get_client
        client = get_client()
        if not client or not client.is_connected():
            logger.debug("TypeDB not available for auto-linking")
            return

        # Link the generated evidence file
        if log_path:
            try:
                client.link_evidence_to_session(session_id, log_path)
                logger.info(f"Auto-linked evidence {log_path} to {session_id}")
            except Exception as e:
                logger.debug(f"Failed to link evidence: {e}")

        # Link rules referenced in session decisions/events
        linked_rules = set()
        for decision in getattr(collector, 'decisions', []):
            rule_id = decision.get('rule_id') if isinstance(decision, dict) else None
            if rule_id:
                linked_rules.add(rule_id)
        for event in getattr(collector, 'events', []):
            rule_id = event.get('rule_id') if isinstance(event, dict) else None
            if rule_id:
                linked_rules.add(rule_id)

        for rule_id in linked_rules:
            try:
                client.link_rule_to_session(session_id, rule_id)
                logger.info(f"Auto-linked rule {rule_id} to {session_id}")
            except Exception as e:
                logger.debug(f"Failed to link rule {rule_id}: {e}")

    except Exception as e:
        logger.debug(f"Auto-link failed (non-critical): {e}")


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
