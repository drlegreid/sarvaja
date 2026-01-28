#!/usr/bin/env python3
"""
Entropy CLI Wrapper
===================
Standalone CLI entry point for entropy monitoring.

Per GAP-ENTROPY-HOOK-001: Enables PostToolUse hook integration.

Usage:
    python entropy_cli.py --increment    # PostToolUse hook
    python entropy_cli.py --status       # Status check
    python entropy_cli.py --reset        # Reset for new session

Exit codes:
    0 - OK (no warning)
    1 - Warning issued (shown to user)
    2 - Error
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Resolve paths for direct execution
HOOKS_DIR = Path(__file__).parent
PROJECT_DIR = HOOKS_DIR.parent.parent
STATE_FILE = HOOKS_DIR / ".entropy_state.json"

# Thresholds
MEDIUM_THRESHOLD = 50
HIGH_THRESHOLD = 100
CRITICAL_THRESHOLD = 150


def load_state() -> dict:
    """Load entropy state from file."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return get_default_state()


def get_default_state() -> dict:
    """Get default entropy state."""
    return {
        "session_start": datetime.now().isoformat(),
        "session_hash": "NEW",
        "tool_count": 0,
        "check_count": 0,
        "last_save": None,
        "warnings_shown": 0,
        "last_warning_at": 0,
        "history": []
    }


def save_state(state: dict) -> None:
    """Save entropy state to file."""
    STATE_FILE.write_text(json.dumps(state, indent=2))


def get_entropy_level(tool_count: int) -> str:
    """Determine entropy level from tool count."""
    if tool_count >= CRITICAL_THRESHOLD:
        return "CRITICAL"
    elif tool_count >= HIGH_THRESHOLD:
        return "HIGH"
    elif tool_count >= MEDIUM_THRESHOLD:
        return "MEDIUM"
    return "LOW"


def increment_and_check(quiet: bool = False) -> int:
    """Increment tool count and check for warnings."""
    state = load_state()
    state["tool_count"] = state.get("tool_count", 0) + 1
    state["check_count"] = state.get("check_count", 0) + 1

    tool_count = state["tool_count"]
    warnings_shown = state.get("warnings_shown", 0)
    last_warning_at = state.get("last_warning_at", 0)

    # Determine session minutes
    try:
        start = datetime.fromisoformat(state.get("session_start", ""))
        session_minutes = int((datetime.now() - start).total_seconds() / 60)
    except Exception:
        session_minutes = 0

    warning_msg = None
    exit_code = 0

    # CRITICAL threshold - STOP and save (every 10 calls after threshold)
    # Reduced interval for aggressive warning at critical level
    # Also triggers immediately on first crossing into CRITICAL
    is_first_critical = tool_count >= CRITICAL_THRESHOLD and last_warning_at < CRITICAL_THRESHOLD
    is_critical_interval = tool_count >= CRITICAL_THRESHOLD and tool_count - last_warning_at >= 10

    if is_first_critical or is_critical_interval:
        warning_msg = (
            f"⚠️ [CONTEXT ENTROPY CRITICAL] {tool_count} tool calls, {session_minutes}m session.\n"
            f"🛑 SAVE CONTEXT NOW! Use chroma_save_session_context() before compaction.\n"
            f"💡 Run /entropy to check status, /save to preserve work."
        )
        state["last_warning_at"] = tool_count
        state["warnings_shown"] = warnings_shown + 1
        exit_code = 1

    # HIGH threshold - strong suggestion (every 15 calls, reduced from 20)
    elif tool_count >= HIGH_THRESHOLD and tool_count - last_warning_at >= 15:
        warning_msg = (
            f"[CONTEXT ENTROPY HIGH] {tool_count} tool calls, {session_minutes}m session.\n"
            f"Run /save before complex tasks to preserve context."
        )
        state["last_warning_at"] = tool_count
        state["warnings_shown"] = warnings_shown + 1
        exit_code = 1

    # MEDIUM threshold - first gentle reminder
    elif tool_count >= MEDIUM_THRESHOLD and warnings_shown == 0:
        warning_msg = (
            f"[CONTEXT CHECKPOINT] {tool_count} tool calls.\n"
            f"Consider /save at natural breakpoints."
        )
        state["warnings_shown"] = 1
        state["last_warning_at"] = tool_count
        exit_code = 1

    # Add to history if warning
    if warning_msg:
        state.setdefault("history", []).append({
            "timestamp": datetime.now().isoformat(),
            "event": f"WARNING_{get_entropy_level(tool_count)}",
            "tool_count": tool_count
        })
        # Keep history bounded
        state["history"] = state["history"][-20:]

    save_state(state)

    if warning_msg:
        print(warning_msg)
    elif not quiet:
        level = get_entropy_level(tool_count)
        print(f"[ENTROPY {level}] {tool_count} calls")

    return exit_code


def show_status() -> int:
    """Display current entropy status."""
    state = load_state()
    tool_count = state.get("tool_count", 0)
    level = get_entropy_level(tool_count)

    try:
        start = datetime.fromisoformat(state.get("session_start", ""))
        session_minutes = int((datetime.now() - start).total_seconds() / 60)
    except Exception:
        session_minutes = 0

    print(f"Entropy: {level}")
    print(f"Tool calls: {tool_count}")
    print(f"Session: {session_minutes} minutes")
    print(f"Warnings shown: {state.get('warnings_shown', 0)}")
    if state.get("last_save"):
        print(f"Last save: {state['last_save']}")

    return 0


def reset_state() -> int:
    """Reset entropy state for new session.

    Per GAP-CONTEXT-ROT-CHECK: Logs previous session stats for audit trail.
    """
    # Load previous state for audit
    prev_state = load_state()
    prev_tool_count = prev_state.get("tool_count", 0)
    prev_hash = prev_state.get("session_hash", "")

    # Create new state
    state = get_default_state()

    # Add previous session info to history for continuity tracking
    if prev_tool_count > 0:
        state["history"].append({
            "timestamp": datetime.now().isoformat(),
            "event": "PREVIOUS_SESSION_END",
            "tool_count": prev_tool_count,
            "session_hash": prev_hash
        })

    save_state(state)

    # Warn if previous session had high entropy (context rot indicator)
    if prev_tool_count >= CRITICAL_THRESHOLD:
        print(f"⚠️ Previous session had CRITICAL entropy ({prev_tool_count} calls)")
        print("Entropy state reset for new session")
        return 1  # Non-blocking warning
    elif prev_tool_count >= HIGH_THRESHOLD:
        print(f"Previous session had HIGH entropy ({prev_tool_count} calls)")
        print("Entropy state reset for new session")
        return 0

    print("Entropy state reset for new session")
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Entropy monitoring for Claude Code sessions"
    )
    parser.add_argument(
        "--increment", action="store_true",
        help="Increment tool count and check (for PostToolUse hooks)"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Show current entropy status"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Reset entropy state for new session"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="Suppress non-warning output"
    )

    args = parser.parse_args()

    try:
        if args.increment:
            sys.exit(increment_and_check(quiet=args.quiet))
        elif args.status:
            sys.exit(show_status())
        elif args.reset:
            sys.exit(reset_state())
        else:
            # Default: show status
            sys.exit(show_status())

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
