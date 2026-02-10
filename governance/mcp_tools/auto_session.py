"""
MCP Auto-Session Capture (GAP-GOVSESS-CAPTURE-001).

Automatically captures non-chat MCP tool calls into governance sessions.
When MCP tools are called directly (not through the chat endpoint),
this module creates and manages sessions to track the activity.

Usage in MCP servers:
    from governance.mcp_tools.auto_session import track_mcp_tool_call
    track_mcp_tool_call("rule_create", "gov-core")

Created: 2026-02-11
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

# Default inactivity timeout before auto-ending a session
_DEFAULT_TIMEOUT_SECONDS = 300  # 5 minutes

# Global tracker instance (one per MCP server process)
_global_tracker: Optional["MCPAutoSessionTracker"] = None


class MCPAutoSessionTracker:
    """Tracks MCP tool calls and auto-manages governance sessions.

    Creates a session on first tool call, records subsequent calls,
    and auto-ends after a configurable inactivity timeout.
    """

    def __init__(self, timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS):
        self.timeout_seconds = timeout_seconds
        self.active_session_id: Optional[str] = None
        self.tool_calls: List[Dict[str, Any]] = []
        self._last_activity: Optional[datetime] = None
        self._session_start: Optional[datetime] = None

    def _is_expired(self) -> bool:
        """Check if the current session has timed out."""
        if not self._last_activity:
            return True
        return (datetime.now() - self._last_activity).total_seconds() > self.timeout_seconds

    def _create_session(self, server_name: str) -> str:
        """Create a new auto-session."""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        short_id = uuid.uuid4().hex[:6].upper()
        session_id = f"SESSION-{date_str}-MCP-AUTO-{short_id}"
        self.active_session_id = session_id
        self.tool_calls = []
        self._session_start = now
        self._last_activity = now
        logger.info(f"MCP auto-session created: {session_id} (server={server_name})")
        return session_id

    def track(
        self,
        tool_name: str,
        server_name: str,
        persist: bool = False,
    ) -> str:
        """Record an MCP tool call.

        Creates a new session if none active or expired.

        Args:
            tool_name: Name of the MCP tool called
            server_name: MCP server name (gov-core, gov-tasks, etc.)
            persist: If True, persist to _sessions_store

        Returns:
            Active session ID.
        """
        # Check if we need a new session
        if self.active_session_id is None or self._is_expired():
            if self.active_session_id and self._is_expired():
                self.end_session(persist=persist)
            self._create_session(server_name)
            if persist:
                self._persist_session_start(server_name)

        self._last_activity = datetime.now()

        call_record = {
            "tool_name": tool_name,
            "server": server_name,
            "timestamp": self._last_activity.isoformat(),
        }
        self.tool_calls.append(call_record)

        if persist:
            self._persist_tool_call(call_record)

        return self.active_session_id

    def end_session(self, persist: bool = False) -> Optional[Dict[str, Any]]:
        """End the current auto-session.

        Returns:
            Summary of the ended session, or None if no active session.
        """
        if not self.active_session_id:
            return None

        summary = {
            "session_id": self.active_session_id,
            "tool_call_count": len(self.tool_calls),
            "servers": list(set(tc["server"] for tc in self.tool_calls)),
            "started_at": self._session_start.isoformat() if self._session_start else None,
            "ended_at": datetime.now().isoformat(),
        }

        if persist:
            self._persist_session_end()

        logger.info(
            f"MCP auto-session ended: {self.active_session_id} "
            f"({len(self.tool_calls)} tool calls)"
        )

        self.active_session_id = None
        self.tool_calls = []
        self._session_start = None
        self._last_activity = None

        return summary

    def _persist_session_start(self, server_name: str) -> None:
        """Persist session start to _sessions_store."""
        try:
            from governance.stores import _sessions_store
            _sessions_store[self.active_session_id] = {
                "session_id": self.active_session_id,
                "start_time": self._session_start.isoformat(),
                "status": "ACTIVE",
                "tasks_completed": 0,
                "description": f"MCP auto-session ({server_name})",
                "agent_id": "code-agent",
                "tool_calls": [],
            }
        except Exception as e:
            logger.warning(f"Failed to persist MCP session start: {e}")

    def _persist_tool_call(self, call_record: Dict) -> None:
        """Persist a tool call to _sessions_store."""
        try:
            from governance.stores import _sessions_store
            sid = self.active_session_id
            if sid in _sessions_store:
                if "tool_calls" not in _sessions_store[sid]:
                    _sessions_store[sid]["tool_calls"] = []
                _sessions_store[sid]["tool_calls"].append(call_record)
        except Exception as e:
            logger.warning(f"Failed to persist MCP tool call: {e}")

    def _persist_session_end(self) -> None:
        """Persist session end to _sessions_store."""
        try:
            from governance.stores import _sessions_store
            sid = self.active_session_id
            if sid in _sessions_store:
                _sessions_store[sid]["status"] = "COMPLETED"
                _sessions_store[sid]["end_time"] = datetime.now().isoformat()
                _sessions_store[sid]["tasks_completed"] = len(self.tool_calls)
        except Exception as e:
            logger.warning(f"Failed to persist MCP session end: {e}")


# ---- Module-level convenience functions ----

def track_mcp_tool_call(
    tool_name: str,
    server_name: str,
    persist: bool = False,
) -> str:
    """Track an MCP tool call using the global tracker.

    Creates the global tracker on first use.

    Returns:
        Active session ID.
    """
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = MCPAutoSessionTracker()
    return _global_tracker.track(tool_name, server_name, persist=persist)


def end_mcp_session(persist: bool = False) -> Optional[Dict[str, Any]]:
    """End the current MCP auto-session.

    Returns:
        Summary or None.
    """
    global _global_tracker
    if _global_tracker is None:
        return None
    return _global_tracker.end_session(persist=persist)
