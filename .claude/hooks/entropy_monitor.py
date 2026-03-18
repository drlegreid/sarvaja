#!/usr/bin/env python3
"""
Entropy Monitor - Session Context Tracking for SLEEP Mode Automation

Per EPIC-006, RULE-024: Track session entropy to suggest context saves.

Since Claude Code does NOT expose context usage APIs, this uses heuristics:
- Tool call count (proxy for context accumulation)
- Session duration (time-based accumulation)
- Transcript size estimation

Thresholds:
- 50 tool calls: First warning
- 100 tool calls: Strong suggestion to save
- 60 minutes: Time-based reminder

CRITICAL: Non-blocking, always returns valid JSON, exit 0.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration
STATE_FILE = Path(__file__).parent / ".entropy_state.json"
LOW_THRESHOLD = 50      # First gentle reminder
HIGH_THRESHOLD = 100    # Strong save suggestion
TIME_THRESHOLD = 60     # Minutes before time-based reminder
CHECKPOINT_INTERVAL = 10  # Record audit checkpoint every N tool calls


def generate_session_hash(state: Dict[str, Any]) -> str:
    """Generate a 4-character hash for session tracking."""
    import hashlib
    data = f"{state.get('session_start', '')}-{state.get('tool_count', 0)}"
    return hashlib.md5(data.encode()).hexdigest()[:4].upper()


def load_state() -> Dict[str, Any]:
    """Load entropy tracking state."""
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
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


def save_state(state: Dict[str, Any], add_history: bool = False, event: str = "", extra: Optional[Dict[str, Any]] = None) -> None:
    """Save entropy tracking state with optional history entry.

    Args:
        state: Current state dict
        add_history: Whether to add a history entry
        event: Event type for history (e.g., CHECKPOINT, WARNING_HIGH)
        extra: Additional fields to include in history entry
    """
    try:
        # Add history entry if requested
        if add_history and event:
            history = state.get("history", [])
            entry = {
                "timestamp": datetime.now().isoformat(),
                "event": event,
                "tool_count": state.get("tool_count", 0),
                "session_hash": state.get("session_hash", "0000")
            }
            # Add extra fields if provided
            if extra:
                entry.update(extra)
            history.append(entry)
            # Keep last 50 history entries (FIFO)
            state["history"] = history[-50:]

        # Update check count
        state["check_count"] = state.get("check_count", 0) + 1

        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass  # Non-critical


def get_session_minutes(state: Dict[str, Any]) -> float:
    """Calculate session duration in minutes."""
    try:
        start = datetime.fromisoformat(state.get("session_start", datetime.now().isoformat()))
        return (datetime.now() - start).total_seconds() / 60
    except Exception:
        return 0


def format_output(context: str) -> None:
    """Output valid JSON for Claude Code context injection."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": context
        }
    }
    print(json.dumps(output))


def reset_state() -> None:
    """Reset state for new session (called by SessionStart hook)."""
    session_start = datetime.now().isoformat()
    state = {
        "session_start": session_start,
        "session_hash": "0000",  # Will be updated below
        "tool_count": 0,
        "check_count": 0,
        "last_save": None,
        "warnings_shown": 0,
        "last_warning_at": 0,
        "history": []
    }
    # Generate session hash
    state["session_hash"] = generate_session_hash(state)
    save_state(state, add_history=True, event="SESSION_RESET")


def mark_saved() -> None:
    """Mark that a save was performed (can be called by /save skill)."""
    state = load_state()
    state["last_save"] = datetime.now().isoformat()
    state["warnings_shown"] = 0  # Reset warnings after save
    save_state(state, add_history=True, event="CONTEXT_SAVED")


def _extract_tool_name() -> Optional[str]:
    """Extract tool name from stdin hook event JSON (G.3)."""
    try:
        if not sys.stdin.isatty():
            data = json.loads(sys.stdin.read())
            return data.get("tool_name") or data.get("toolName")
    except Exception:
        pass
    return None


def _detect_context_rot(recent_tools: list) -> float:
    """Detect context rot via repetitive tool call patterns (G.3).

    Returns rot_score 0.0-1.0 where higher = more repetitive.
    """
    if len(recent_tools) < 5:
        return 0.0

    last_10 = recent_tools[-10:]
    unique = len(set(last_10))
    total = len(last_10)

    # If same tool called 3+ times in last 10 calls
    from collections import Counter
    counts = Counter(last_10)
    max_repeat = max(counts.values()) if counts else 0

    # Rot score: weighted combination of low uniqueness + high repetition
    uniqueness = unique / total  # 1.0 = all different, 0.1 = all same
    repetition = max_repeat / total  # 0.1 = no repeat, 1.0 = all same tool

    rot_score = (1 - uniqueness) * 0.5 + repetition * 0.5
    return round(rot_score, 2)


def main():
    """Main entropy monitoring logic."""
    try:
        # Check for special commands via arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == "--reset":
                reset_state()
                format_output("[ENTROPY] State reset for new session")
                return
            elif sys.argv[1] == "--saved":
                mark_saved()
                format_output("[ENTROPY] Save recorded")
                return
            elif sys.argv[1] == "--status":
                state = load_state()
                tool_count = state.get("tool_count", 0)
                minutes = get_session_minutes(state)
                format_output(f"[ENTROPY] Tools: {tool_count}, Duration: {int(minutes)}m")
                return

        # Normal operation: increment tool count
        state = load_state()
        state["tool_count"] = state.get("tool_count", 0) + 1
        tool_count = state["tool_count"]
        session_minutes = get_session_minutes(state)
        warnings_shown = state.get("warnings_shown", 0)
        last_warning_at = state.get("last_warning_at", 0)

        # G.3: Track tool name for context rot detection
        tool_name = _extract_tool_name()
        recent_tools = state.get("recent_tools", [])
        if tool_name:
            recent_tools.append(tool_name)
            recent_tools = recent_tools[-20:]  # Keep last 20
            state["recent_tools"] = recent_tools

        # Determine if we should show a warning
        context = None

        # Track event for history
        event = None
        extra = None

        # Periodic checkpoint for audit trail (every CHECKPOINT_INTERVAL calls)
        should_checkpoint = (tool_count % CHECKPOINT_INTERVAL == 0)

        # G.3: Context rot detection — check for repetitive patterns
        rot_score = _detect_context_rot(recent_tools)
        if rot_score > 0.7 and tool_count > 30:
            context = (
                f"[CONTEXT ROT DETECTED] Freshness: {int((1 - rot_score) * 100)}%. "
                f"Repetitive tool call patterns detected.\n"
                f"Save context and consider restarting session."
            )
            event = "CONTEXT_ROT"
            extra = {"rot_score": rot_score, "freshness": 1 - rot_score}

        # HIGH threshold - strong suggestion (but don't spam)
        # BUG-ENTROPY-OVERWRITE-001: Use elif to preserve context rot message
        elif tool_count >= HIGH_THRESHOLD and tool_count - last_warning_at >= 20:
            context = (
                f"[CONTEXT ENTROPY HIGH] {tool_count} tool calls, {int(session_minutes)}m session.\n"
                f"Run /save before complex tasks to preserve context."
            )
            state["last_warning_at"] = tool_count
            state["warnings_shown"] = warnings_shown + 1
            event = "WARNING_HIGH"

        # LOW threshold - first gentle reminder
        elif tool_count >= LOW_THRESHOLD and warnings_shown == 0:
            context = (
                f"[CONTEXT CHECKPOINT] {tool_count} tool calls.\n"
                f"Consider /save at natural breakpoints."
            )
            state["warnings_shown"] = 1
            state["last_warning_at"] = tool_count
            event = "WARNING_LOW"

        # Time-based reminder (60 minutes)
        elif session_minutes >= TIME_THRESHOLD and warnings_shown < 2:
            context = (
                f"[SESSION DURATION] {int(session_minutes)} minutes active.\n"
                f"Consider /save if approaching milestone."
            )
            state["warnings_shown"] = 2
            event = "WARNING_TIME"
            extra = {"minutes": int(session_minutes)}

        # Periodic checkpoint (no warning, just audit trail)
        elif should_checkpoint and not event:
            event = "CHECKPOINT"
            extra = {"minutes": int(session_minutes), "warnings_shown": warnings_shown}

        # Save state (with history if event occurred)
        save_state(state, add_history=bool(event), event=event or "", extra=extra)

        if context:
            format_output(context)
        else:
            # Silent operation - just update state
            print(json.dumps({}))  # Empty JSON for no context injection

    except Exception as e:
        # Never fail - graceful degradation
        format_output(f"[ENTROPY ERROR] {str(e)[:50]}")

    sys.exit(0)  # Always exit 0


if __name__ == "__main__":
    main()
