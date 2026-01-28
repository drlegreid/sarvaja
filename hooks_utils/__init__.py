"""
Hooks Utilities Package.

Per GAP-SESSION-THOUGHT-001: Shared utilities for Claude Code hooks.
"""

from .session_tool_logger import (
    parse_tool_input,
    get_tool_name,
    get_active_session_id,
    log_tool_call,
    main
)

__all__ = [
    "parse_tool_input",
    "get_tool_name",
    "get_active_session_id",
    "log_tool_call",
    "main"
]
