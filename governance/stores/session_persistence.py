"""
Session Store Disk Persistence (GAP-SESSION-TRANSCRIPT-001).

Persists _sessions_store tool_calls and thoughts to disk so they
survive container restarts. Uses JSON sidecar files per session.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

_STORE_DIR = Path(__file__).parent.parent.parent / "data" / "session_store"

# Keys worth persisting (skip transient metadata already in TypeDB)
_PERSIST_KEYS = {"tool_calls", "thoughts", "topic", "session_type", "intent"}


def _get_path(session_id: str) -> Path:
    """Get the JSON file path for a session."""
    # Sanitize session_id for filesystem safety
    safe = session_id.replace("/", "_").replace("..", "_")
    return _STORE_DIR / f"{safe}.json"


def persist_session(session_id: str, session_data: Dict[str, Any]) -> None:
    """Persist session tool_calls/thoughts to disk.

    Only writes keys in _PERSIST_KEYS to avoid duplicating TypeDB data.
    Silently skips on error to never block the hot path.
    """
    try:
        _STORE_DIR.mkdir(parents=True, exist_ok=True)
        subset = {k: v for k, v in session_data.items() if k in _PERSIST_KEYS and v}
        if not subset:
            return
        path = _get_path(session_id)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(subset, default=str), encoding="utf-8")
        try:
            tmp.rename(path)  # Atomic on same filesystem
        except OSError:
            # BUG-PERSIST-TMP-001: Cleanup orphaned .tmp file on rename failure
            try:
                tmp.unlink(missing_ok=True)
            except OSError as ue:
                logger.debug(f"Failed to cleanup .tmp for {session_id}: {ue}")
            raise
    except Exception as e:
        logger.debug(f"Session persist skipped for {session_id}: {e}")


def load_persisted_sessions(sessions_store: Dict[str, Dict[str, Any]]) -> int:
    """Load persisted session data into _sessions_store on startup.

    Merges tool_calls/thoughts into existing entries (TypeDB data takes
    priority for metadata fields). Returns count of sessions loaded.
    """
    if not _STORE_DIR.is_dir():
        return 0

    loaded = 0
    for path in _STORE_DIR.glob("*.json"):
        session_id = path.stem
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue

            if session_id not in sessions_store:
                sessions_store[session_id] = {"session_id": session_id}

            entry = sessions_store[session_id]
            # Merge persisted arrays — don't overwrite if store already has data
            for key in ("tool_calls", "thoughts"):
                if key in data and not entry.get(key):
                    entry[key] = data[key]
            # Restore bridge-specific fields
            for key in ("topic", "session_type", "intent"):
                if key in data and key not in entry:
                    entry[key] = data[key]

            loaded += 1
        except Exception as e:
            logger.warning(f"Failed to load persisted session {path.name}: {e}")

    if loaded:
        logger.info(f"Loaded {loaded} persisted session(s) from disk")
    return loaded


def cleanup_persisted(session_id: str) -> None:
    """Remove persisted file for a completed session (optional housekeeping)."""
    try:
        path = _get_path(session_id)
        if path.exists():
            path.unlink()
    except Exception as e:
        # BUG-PERSIST-001: Log cleanup failures instead of silently swallowing
        logger.debug(f"Failed to cleanup persisted session {session_id}: {e}")
