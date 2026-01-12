"""
State management for Claude Code hooks.

Per EPIC-006: Provides hash computation and state persistence.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def compute_frankel_hash(data: Dict[str, Any]) -> str:
    """
    Compute Frankel-style hash (first 8 chars of SHA256, uppercase).

    Used for master state hashing to detect changes.
    """
    serialized = json.dumps(data, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()[:8].upper()


def compute_component_hash(status: str, port: int = 0) -> str:
    """
    Compute hash for individual component (4 chars for drill-down).

    Includes hour to provide temporal context.
    """
    data = f"{status}:{port}:{datetime.now().strftime('%Y%m%d%H')}"
    return hashlib.sha256(data.encode()).hexdigest()[:4].upper()


def compute_session_hash(session_start: str, tool_count: int) -> str:
    """
    Generate a 4-character hash for session tracking.

    Used by entropy monitor for session identification.
    """
    data = f"{session_start}-{tool_count}"
    return hashlib.md5(data.encode()).hexdigest()[:4].upper()


class StateManager:
    """
    Manages hook state persistence with history tracking.

    Supports:
    - Loading/saving state to JSON files
    - History tracking with configurable limit
    - Atomic state updates
    """

    def __init__(self, state_file: Path, history_limit: int = 10):
        """
        Initialize state manager.

        Args:
            state_file: Path to state JSON file
            history_limit: Maximum history entries to keep
        """
        self.state_file = state_file
        self.history_limit = history_limit
        self._state: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """Load state from file, returning empty dict on error."""
        try:
            if self.state_file.exists():
                with open(self.state_file, "r") as f:
                    self._state = json.load(f)
                    return self._state
        except Exception:
            pass
        self._state = {}
        return {}

    def save(self, state: Dict[str, Any], add_history: bool = False,
             history_entry: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save state to file with optional history entry.

        Args:
            state: State dictionary to save
            add_history: Whether to add a history entry
            history_entry: Custom history entry (auto-generated if None)

        Returns:
            True if save succeeded
        """
        try:
            # Ensure history exists
            if "history" not in state:
                state["history"] = []

            # Add history entry if requested
            if add_history:
                history = state.get("history", [])

                if history_entry:
                    entry = history_entry
                else:
                    # Auto-generate history entry
                    entry = {
                        "timestamp": datetime.now().isoformat(),
                        "hash": state.get("master_hash", state.get("session_hash", "????")),
                    }

                history.append(entry)
                state["history"] = history[-self.history_limit:]

            # Save atomically
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)

            self._state = state
            return True

        except Exception:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from current state."""
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set value in current state (doesn't persist until save)."""
        self._state[key] = value

    def increment(self, key: str, amount: int = 1) -> int:
        """Increment a numeric value and return new value."""
        current = self._state.get(key, 0)
        new_value = current + amount
        self._state[key] = new_value
        return new_value

    @property
    def state(self) -> Dict[str, Any]:
        """Get current state dictionary."""
        return self._state


class HealthcheckState(StateManager):
    """Specialized state manager for healthcheck with audit trail support."""

    def __init__(self, state_file: Path):
        super().__init__(state_file, history_limit=10)

    def get_default_state(self) -> Dict[str, Any]:
        """Get default healthcheck state."""
        return {
            "master_hash": "",
            "check_count": 0,
            "last_check": None,
            "unchanged_since": 0,
            "components": {},
            "component_hashes": {},
            "history": []
        }

    def save_check(self, services: Dict[str, Any], master_hash: str,
                   component_hashes: Dict[str, str],
                   recovery_actions: Optional[List[str]] = None) -> None:
        """
        Save a healthcheck result with history tracking.
        """
        prev_state = self.load()
        prev_hash = prev_state.get("master_hash", "")
        unchanged_since = prev_state.get("unchanged_since", 0)
        check_count = prev_state.get("check_count", 0) + 1

        import time
        now = time.time()

        # Track state change timing
        if master_hash != prev_hash:
            new_unchanged_since = now
            add_history = True
        else:
            new_unchanged_since = unchanged_since if unchanged_since > 0 else now
            add_history = False

        state = {
            "master_hash": master_hash,
            "check_count": check_count,
            "last_check": datetime.now().isoformat(),
            "unchanged_since": new_unchanged_since,
            "components": {name: data.get("status", "UNKNOWN") for name, data in services.items()},
            "component_hashes": component_hashes
        }

        if recovery_actions:
            state["last_recovery"] = now
            state["recovery_actions"] = recovery_actions

        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "hash": master_hash,
            "components": state["components"],
            "component_hashes": component_hashes
        }

        self.save(state, add_history=add_history, history_entry=history_entry)


class EntropyState(StateManager):
    """Specialized state manager for entropy tracking with event history."""

    def __init__(self, state_file: Path):
        super().__init__(state_file, history_limit=50)

    def get_default_state(self) -> Dict[str, Any]:
        """Get default entropy state."""
        return {
            "session_start": datetime.now().isoformat(),
            "session_hash": "0000",
            "tool_count": 0,
            "check_count": 0,
            "last_save": None,
            "warnings_shown": 0,
            "last_warning_at": 0,
            "history": []
        }

    def reset_session(self) -> Dict[str, Any]:
        """Reset state for a new session."""
        session_start = datetime.now().isoformat()
        state = self.get_default_state()
        state["session_hash"] = compute_session_hash(session_start, 0)

        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "SESSION_RESET",
            "tool_count": 0,
            "session_hash": state["session_hash"]
        }

        self.save(state, add_history=True, history_entry=history_entry)
        return state

    def record_event(self, event: str) -> None:
        """Record an event to history."""
        state = self.load()

        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "tool_count": state.get("tool_count", 0),
            "session_hash": state.get("session_hash", "0000")
        }

        self.save(state, add_history=True, history_entry=history_entry)

    def increment_tool_count(self) -> int:
        """Increment tool count and return new value."""
        state = self.load()
        state["tool_count"] = state.get("tool_count", 0) + 1
        state["check_count"] = state.get("check_count", 0) + 1
        self.save(state)
        return state["tool_count"]

    def mark_saved(self) -> None:
        """Mark that a context save was performed."""
        state = self.load()
        state["last_save"] = datetime.now().isoformat()
        state["warnings_shown"] = 0  # Reset warnings after save

        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "CONTEXT_SAVED",
            "tool_count": state.get("tool_count", 0),
            "session_hash": state.get("session_hash", "0000")
        }

        self.save(state, add_history=True, history_entry=history_entry)
