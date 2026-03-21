"""
MCP Usage Pattern Checker with Health-Aware Enforcement.

Per GOV-MCP-FIRST-01-v1 (MANDATORY): Enforce MCP-first task management.
Per WORKFLOW-AUTO-01-v1: Never block, only warn via stderr.

When gov-tasks MCP is healthy: warn if TodoWrite used without MCP calls.
When gov-tasks MCP is down: fallback mode — TodoWrite is legitimate.

Created: 2026-02-12
Updated: 2026-03-21 (Phase 8 — health-aware enforcement)
"""

import json
import sys
import time
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

# Health check cache TTL in seconds
HEALTH_CHECK_INTERVAL = 60

# API base for health check
_API_BASE = "http://localhost:8082"

# In-memory health cache (per-process)
_health_cache: Dict[str, Any] = {"healthy": None, "timestamp": 0}


def _default_state() -> Dict[str, Any]:
    return {
        "session_start": datetime.now().isoformat(),
        "tool_count": 0,
        "todowrite_count": 0,
        "mcp_categories_used": {},
        "last_warning": None,
        "warnings_issued": 0,
        "mcp_healthy": None,
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


def check_mcp_health() -> bool:
    """Check if gov-tasks MCP/API is reachable.

    Caches result for HEALTH_CHECK_INTERVAL seconds to avoid
    hitting the API on every tool call (hooks run frequently).
    """
    now = time.time()
    if now - _health_cache.get("timestamp", 0) < HEALTH_CHECK_INTERVAL:
        return _health_cache.get("healthy", False)

    try:
        import httpx
        resp = httpx.get(f"{_API_BASE}/api/health", timeout=1.5)
        healthy = resp.status_code == 200
    except Exception:
        healthy = False

    _health_cache["healthy"] = healthy
    _health_cache["timestamp"] = now
    return healthy


def is_fallback_mode() -> bool:
    """Return True when MCP is down and TodoWrite is legitimate."""
    return not check_mcp_health()


def track_tool(tool_name: str) -> Optional[str]:
    """Track a tool call and return warning message if needed.

    Health-aware enforcement (Phase 8):
    - MCP healthy + TodoWrite without gov-tasks → warning
    - MCP down → fallback mode, no warning
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
        # Health-aware: only warn when MCP is available
        mcp_healthy = check_mcp_health()
        state["mcp_healthy"] = mcp_healthy

        if mcp_healthy:
            warning = (
                "[MCP-FIRST] MANDATORY: TodoWrite used but gov-tasks MCP is "
                "available and not yet called. Per GOV-MCP-FIRST-01-v1: Use "
                "mcp__gov-tasks__task_create() for persistent task management. "
                "TodoWrite is display-only."
            )
            state["last_warning"] = datetime.now().isoformat()
            state["warnings_issued"] = state.get("warnings_issued", 0) + 1
        # else: MCP down → fallback mode, no warning
    else:
        # Still record health status periodically for diagnostics
        if state["tool_count"] % 20 == 0:
            state["mcp_healthy"] = check_mcp_health()

    save_state(state)
    return warning


def reset() -> None:
    """Reset state for new session."""
    _health_cache["healthy"] = None
    _health_cache["timestamp"] = 0
    save_state(_default_state())


def get_summary() -> Dict[str, Any]:
    """Get current MCP usage summary for healthcheck display."""
    state = load_state()
    mcp_healthy = state.get("mcp_healthy")
    return {
        "tool_count": state.get("tool_count", 0),
        "todowrite_count": state.get("todowrite_count", 0),
        "mcp_categories": state.get("mcp_categories_used", {}),
        "warnings_issued": state.get("warnings_issued", 0),
        "mcp_healthy": mcp_healthy,
        "mode": "enforce" if mcp_healthy else "fallback",
    }
