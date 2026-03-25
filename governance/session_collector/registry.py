"""
Session Registry - Global session management.

Per RULE-032: Modularized from session_collector.py (591 lines).
Per GAP-SESSION-THOUGHT-001: State file for hook integration.
Contains: Global session registry and helper functions.
"""

import json
import logging
import time
from datetime import date

logger = logging.getLogger(__name__)
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

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
    """List all active session IDs (memory only)."""
    return list(_active_sessions.keys())


# Two-hour threshold for CC JSONL "active" detection
_CC_ACTIVE_THRESHOLD_SECS = 2 * 3600


def list_all_active_sessions() -> List[Dict[str, Any]]:
    """List active sessions from all sources: memory, TypeDB, CC JSONL.

    Per FEAT-009: Merges three data sources so session_list() MCP tool
    can detect running CC sessions, not just MCP-started ones.

    Returns:
        Deduplicated list of dicts with session_id, source, status.
        Priority on collision: memory > typedb > cc_jsonl.
    """
    seen: Dict[str, Dict[str, Any]] = {}

    # Source 1: In-memory (MCP-created sessions in current process)
    for sid in _active_sessions:
        seen[sid] = {"session_id": sid, "source": "memory", "status": "ACTIVE"}

    # Source 2: TypeDB sessions with status ACTIVE
    try:
        from governance.stores import get_all_sessions_from_typedb
        for s in get_all_sessions_from_typedb(allow_fallback=True):
            if s.get("status") == "ACTIVE":
                sid = s.get("session_id")
                if sid and sid not in seen:
                    seen[sid] = {
                        "session_id": sid,
                        "source": "typedb",
                        "status": "ACTIVE",
                    }
    except Exception as e:
        logger.debug("TypeDB active session lookup failed: %s", e)

    # Source 3: CC JSONL files modified within threshold
    try:
        from governance.services.cc_session_scanner import (
            DEFAULT_CC_DIR,
            scan_jsonl_metadata,
            build_session_id,
            derive_project_slug,
        )
        now = time.time()
        if DEFAULT_CC_DIR.is_dir():
            for project_dir in DEFAULT_CC_DIR.iterdir():
                if not project_dir.is_dir():
                    continue
                slug = derive_project_slug(project_dir)
                for jsonl_file in project_dir.glob("*.jsonl"):
                    try:
                        mtime = jsonl_file.stat().st_mtime
                    except OSError:
                        continue
                    if (now - mtime) > _CC_ACTIVE_THRESHOLD_SECS:
                        continue
                    meta = scan_jsonl_metadata(jsonl_file)
                    if not meta:
                        continue
                    sid = build_session_id(meta, slug)
                    if sid not in seen:
                        seen[sid] = {
                            "session_id": sid,
                            "source": "cc_jsonl",
                            "status": "ACTIVE",
                            "cc_session_uuid": meta.get("session_uuid"),
                            "file_path": str(jsonl_file),
                        }
    except Exception as e:
        logger.debug("CC JSONL active session scan failed: %s", e)

    return list(seen.values())


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
