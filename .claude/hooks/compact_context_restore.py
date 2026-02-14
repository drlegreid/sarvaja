#!/usr/bin/env python3
"""
Compact Context Restore Hook.

Fires after Claude Code automatic/manual compaction to re-inject
critical context that may have been lost during context compression.

Per RECOVER-AMNES-01-v1: Autonomous context recovery without user input.
Per RECOVER-CRASH-01-v1: Save context before risk.

Reads entropy state + session state to produce a recovery summary.
Uses JSON additionalContext output for reliable injection.

Created: 2026-02-14
"""

import json
import sys
from datetime import datetime
from pathlib import Path

HOOKS_DIR = Path(__file__).parent
PROJECT_DIR = HOOKS_DIR.parent.parent
ENTROPY_STATE = HOOKS_DIR / ".entropy_state.json"
SESSION_STATE = HOOKS_DIR / ".session_state.json"
MEMORY_FILE = PROJECT_DIR / ".claude" / "projects" / "-home-oderid-Documents-Vibe-sarvaja-platform" / "memory" / "MEMORY.md"
CLAUDE_MD = PROJECT_DIR / "CLAUDE.md"


def _read_json(path: Path) -> dict:
    """Read JSON file, return empty dict on failure."""
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


def _get_recent_git_info() -> str:
    """Get recent git branch and last commit."""
    import subprocess
    try:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=3, cwd=str(PROJECT_DIR)
        ).stdout.strip()
        log = subprocess.run(
            ["git", "log", "--oneline", "-3"],
            capture_output=True, text=True, timeout=3, cwd=str(PROJECT_DIR)
        ).stdout.strip()
        return f"Branch: {branch}\nRecent commits:\n{log}"
    except Exception:
        return "Git info unavailable"


def _get_active_todos() -> str:
    """Read TodoWrite state if available."""
    try:
        # TodoWrite state is ephemeral (in-memory), not persisted to disk.
        # Best we can do is check the .dsm_state.json for workflow state.
        dsm = PROJECT_DIR / ".dsm_state.json"
        if dsm.exists():
            state = json.loads(dsm.read_text())
            phase = state.get("current_phase", "unknown")
            return f"DSM phase: {phase}"
    except Exception:
        pass
    return ""


def main():
    """Generate context recovery output after compaction."""
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        hook_input = {}

    source = hook_input.get("source", "")
    session_id = hook_input.get("session_id", "unknown")

    # Only handle compact events
    if source != "compact":
        sys.exit(0)

    # Gather state
    entropy = _read_json(ENTROPY_STATE)
    session = _read_json(SESSION_STATE)
    tool_count = entropy.get("tool_count", 0)
    active_sessions = session.get("active_sessions", [])

    # Build recovery context
    parts = []
    parts.append("## Context Restored After Compaction")
    parts.append("")
    parts.append(f"- **Compaction detected** at {datetime.now().strftime('%H:%M:%S')}")
    parts.append(f"- **Tool calls before compaction**: {tool_count}")
    if active_sessions:
        parts.append(f"- **Active governance sessions**: {', '.join(active_sessions)}")

    # Git context
    git_info = _get_recent_git_info()
    if git_info:
        parts.append(f"- **{git_info}**")

    # DSM/workflow state
    todos = _get_active_todos()
    if todos:
        parts.append(f"- **{todos}**")

    # Recovery instructions
    parts.append("")
    parts.append("### Recovery Protocol")
    parts.append("1. CLAUDE.md is already loaded (survives compaction)")
    parts.append("2. Check your todo list above for in-progress tasks")
    parts.append("3. If todo list is empty, read TODO.md for current tasks")
    parts.append("4. Continue working autonomously - do NOT ask user what you were doing")

    context = "\n".join(parts)

    # Log compaction event to entropy state
    entropy["history"] = entropy.get("history", [])
    entropy["history"].append({
        "timestamp": datetime.now().isoformat(),
        "event": "COMPACTION",
        "tool_count": tool_count,
    })
    entropy["history"] = entropy["history"][-20:]
    try:
        ENTROPY_STATE.write_text(json.dumps(entropy, indent=2))
    except Exception:
        pass

    # Output as plain text (shown as system-reminder to Claude)
    print(context)
    sys.exit(0)


if __name__ == "__main__":
    main()
