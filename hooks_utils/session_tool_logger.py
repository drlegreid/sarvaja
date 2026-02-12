"""
Session Tool Logger - Auto-log tool calls to governance sessions.

Per GAP-SESSION-THOUGHT-001: Hook integration for session_thought auto-logging.
Per DOC-SIZE-01-v1: Single responsibility, < 300 lines.

Architecture:
    PostToolUse Hook → Read STDIN/ENV → Write to TypeDB → Silent fail if unavailable

Usage:
    Called by Claude Code PostToolUse hook:
    python3 "$PROJECT_DIR/hooks_utils/session_tool_logger.py"

Environment Variables:
    CLAUDE_TOOL_NAME: Tool that was used (e.g., "Bash", "Read")
    CLAUDE_TOOL_INPUT: JSON string of tool input arguments
    CLAUDE_TOOL_RESULT: JSON string of tool result (optional)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Session state file location
HOOKS_DIR = Path(__file__).parent.parent / ".claude" / "hooks"
SESSION_STATE_FILE = HOOKS_DIR / ".session_state.json"


def parse_tool_input() -> Dict[str, Any]:
    """Parse tool input from CLAUDE_TOOL_INPUT environment variable.

    Returns:
        Dict with parsed input, or empty dict if unavailable.
    """
    raw_input = os.environ.get("CLAUDE_TOOL_INPUT", "")

    if not raw_input:
        return {}

    try:
        return json.loads(raw_input)
    except json.JSONDecodeError:
        return {"raw": raw_input}


def get_tool_name() -> str:
    """Get tool name from CLAUDE_TOOL_NAME environment variable.

    Returns:
        Tool name string, or "unknown" if not set.
    """
    return os.environ.get("CLAUDE_TOOL_NAME", "unknown")


def load_session_state() -> Dict[str, Any]:
    """Load session state from file.

    Returns:
        Session state dict, or empty dict if not found.
    """
    if not SESSION_STATE_FILE.exists():
        return {}

    try:
        return json.loads(SESSION_STATE_FILE.read_text())
    except (json.JSONDecodeError, IOError):
        return {}


def get_active_session_id() -> Optional[str]:
    """Get active session ID from state.

    Checks for active sessions in the session collector state.

    Returns:
        Session ID string, or None if no active session.
    """
    state = load_session_state()

    # Check for active sessions
    active_sessions = state.get("active_sessions", [])
    if active_sessions:
        return active_sessions[-1]

    # Fallback to last_session
    return state.get("last_session")


def get_session_collector() -> Optional[Any]:
    """Get session collector for active session.

    Returns:
        SessionCollector instance, or None if unavailable.
    """
    try:
        from governance.session_collector import get_or_create_session, list_active_sessions
    except ImportError:
        return None

    try:
        sessions = list_active_sessions()
        if not sessions:
            return None

        # Get the most recent session
        topic = sessions[-1].split("-")[-1].lower()
        return get_or_create_session(topic)
    except Exception:
        return None


def log_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    duration_ms: int = 0,
    success: bool = True,
    correlation_id: Optional[str] = None,
    applied_rules: Optional[list] = None
) -> bool:
    """Log tool call to active session.

    Silent fail if session unavailable or TypeDB down.

    Args:
        tool_name: Name of the tool used
        arguments: Tool input arguments
        duration_ms: Execution duration in milliseconds
        success: Whether tool call succeeded
        correlation_id: Optional correlation ID for tracing
        applied_rules: Optional list of rules that applied

    Returns:
        True if logged successfully, False otherwise.
    """
    collector = get_session_collector()

    if collector is None:
        return False

    try:
        collector.capture_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            result=None,  # Result is often too large
            duration_ms=duration_ms,
            success=success,
            correlation_id=correlation_id,
            applied_rules=applied_rules or []
        )
        return True
    except Exception:
        # Silent fail - don't block the main workflow
        return False


# Tools to skip logging (avoid recursion + reduce noise)
SKIP_TOOLS = frozenset({
    "session_tool_call", "session_thought", "TodoWrite",
})


def main() -> int:
    """Main entry point for PostToolUse hook.

    Returns:
        Exit code (always 0 - never block main workflow).
    """
    # Get tool info from environment
    tool_name = get_tool_name()
    arguments = parse_tool_input()

    if tool_name in SKIP_TOOLS:
        return 0

    # Log the tool call
    logged = log_tool_call(
        tool_name=tool_name,
        arguments=arguments,
        duration_ms=0,  # Duration not available in hook
        success=True  # Assume success (hook is PostToolUse)
    )

    # Output nothing - silent operation
    # The hook should be invisible to the user
    return 0


if __name__ == "__main__":
    sys.exit(main())
