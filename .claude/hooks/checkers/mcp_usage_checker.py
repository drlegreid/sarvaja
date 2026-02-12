"""
MCP Usage Pattern Checker.

Per GOV-MCP-FIRST-01-v1: Warn when MCP tools are underused.
Per WORKFLOW-AUTO-01-v1: Never block, only warn via stderr.

Tracks which MCP tool categories have been used this session.
Warns if TodoWrite used without corresponding gov-tasks calls.

Created: 2026-02-12
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

STATE_FILE = Path(__file__).parent.parent / ".mcp_usage_state.json"

# MCP tool prefixes that indicate governance usage
GOV_TOOL_PREFIXES: Dict[str, list] = {
    "gov-tasks": [
        "task_create", "task_update", "task_get", "tasks_list",
        "task_verify", "session_sync_todos", "task_delete",
    ],
    "gov-sessions": [
        "session_start", "session_end", "session_decision",
        "session_task", "session_tool_call", "session_thought",
    ],
    "gov-core": [
        "rule_create", "rule_update", "rules_query",
        "rule_get", "health_check", "wisdom_get",
    ],
}

# Minimum tool calls before checking patterns
MIN_TOOL_COUNT = 10

# Maximum warnings per session to avoid noise
MAX_WARNINGS = 2


def _default_state() -> Dict[str, Any]:
    return {
        "session_start": datetime.now().isoformat(),
        "tool_count": 0,
        "todowrite_count": 0,
        "mcp_categories_used": {},
        "last_warning": None,
        "warnings_issued": 0,
    }


def load_state() -> Dict[str, Any]:
    """Load MCP usage tracking state."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return _default_state()


def save_state(state: Dict[str, Any]) -> None:
    """Save state to file."""
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception:
        pass


def track_tool(tool_name: str) -> Optional[str]:
    """Track a tool call and return warning message if needed.

    Returns a warning string if MCP-first pattern is violated,
    or None if everything is fine.
    """
    state = load_state()
    state["tool_count"] = state.get("tool_count", 0) + 1

    # Track TodoWrite usage
    if tool_name == "TodoWrite":
        state["todowrite_count"] = state.get("todowrite_count", 0) + 1

    # Track MCP tool usage by category
    for category, tools in GOV_TOOL_PREFIXES.items():
        for t in tools:
            if t in (tool_name or ""):
                cats = state.setdefault("mcp_categories_used", {})
                cats[category] = cats.get(category, 0) + 1
                break

    warning = None

    # Check if warning needed (after minimum tool count)
    if (state["tool_count"] >= MIN_TOOL_COUNT
            and state.get("todowrite_count", 0) >= 2
            and "gov-tasks" not in state.get("mcp_categories_used", {})
            and state.get("warnings_issued", 0) < MAX_WARNINGS):
        warning = (
            "[MCP-FIRST] TodoWrite used but gov-tasks MCP not yet called. "
            "Per GOV-MCP-FIRST-01-v1: Use mcp__gov-tasks__task_create() "
            "for persistent task management. TodoWrite is display-only."
        )
        state["last_warning"] = datetime.now().isoformat()
        state["warnings_issued"] = state.get("warnings_issued", 0) + 1

    save_state(state)
    return warning


def reset() -> None:
    """Reset state for new session."""
    save_state(_default_state())


def get_summary() -> Dict[str, Any]:
    """Get current MCP usage summary for healthcheck display."""
    state = load_state()
    return {
        "tool_count": state.get("tool_count", 0),
        "todowrite_count": state.get("todowrite_count", 0),
        "mcp_categories": state.get("mcp_categories_used", {}),
        "warnings_issued": state.get("warnings_issued", 0),
    }
