"""
Robot Framework Library for Claude Code Hooks - Entropy Monitor Tests
Split from ClaudeHooksLibrary.py per DOC-SIZE-01-v1

Per EPIC-006: Entropy Monitor for SLEEP Mode Automation
Covers: Entropy Output, State Management, Warning Thresholds, Non-Blocking
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from robot.api.deco import keyword

HOOKS_DIR = Path(__file__).parent.parent.parent / ".claude" / "hooks"
ENTROPY_SCRIPT = HOOKS_DIR / "entropy_monitor.py"


class ClaudeHooksEntropyLibrary:
    """Library for Claude Code entropy monitor hook tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Entropy Monitor Output Tests
    # =========================================================================

    @keyword("Entropy Returns Valid JSON")
    def entropy_returns_valid_json(self):
        """Entropy monitor must always return valid JSON."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        try:
            output = json.loads(result.stdout)
            return {"valid_json": isinstance(output, dict)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Entropy Exits Zero Always")
    def entropy_exits_zero_always(self):
        """Entropy monitor must exit 0 even on errors."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        return {"exit_zero": result.returncode == 0}

    @keyword("Entropy Status Command")
    def entropy_status_command(self):
        """--status flag should return current entropy state."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--status"],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        hook_output = output.get("hookSpecificOutput", {})
        context = hook_output.get("additionalContext", "")

        return {
            "has_hook_output": "hookSpecificOutput" in output,
            "has_entropy_or_tools": "ENTROPY" in context or "Tools" in context
        }

    # =========================================================================
    # Entropy Monitor State Management Tests
    # =========================================================================

    @keyword("Entropy State File Created")
    def entropy_state_file_created(self):
        """Entropy monitor should create state file."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            timeout=5
        )

        if not state_file.exists():
            return {"exists": False, "has_session_start": False, "has_tool_count": False}

        with open(state_file) as f:
            state = json.load(f)

        return {
            "exists": True,
            "has_session_start": "session_start" in state,
            "has_tool_count": "tool_count" in state
        }

    @keyword("State Has Audit Trail Fields")
    def state_has_audit_trail_fields(self):
        """State should have session_hash, check_count, history for audit trail."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--reset"],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state = json.load(f)

        return {
            "has_session_hash": "session_hash" in state,
            "has_check_count": "check_count" in state,
            "has_history": "history" in state
        }

    @keyword("Session Hash Is 4 Chars")
    def session_hash_is_4_chars(self):
        """Session hash should be 4 uppercase hex chars."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--reset"],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state = json.load(f)

        hash_val = state.get("session_hash", "")
        return {
            "len_4": len(hash_val) == 4,
            "valid_hex": all(c in "0123456789ABCDEF" for c in hash_val),
            "is_upper": hash_val == hash_val.upper()
        }

    @keyword("Check Count Increments")
    def check_count_increments(self):
        """Check count should increment with each state save."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--reset"],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state1 = json.load(f)
        count1 = state1.get("check_count", 0)

        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state2 = json.load(f)
        count2 = state2.get("check_count", 0)

        return {"incremented": count2 > count1}

    @keyword("Reset Creates History Entry")
    def reset_creates_history_entry(self):
        """Reset should create SESSION_RESET history entry."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--reset"],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state = json.load(f)

        history = state.get("history", [])
        reset_events = [h for h in history if h.get("event") == "SESSION_RESET"]

        return {
            "has_history": len(history) > 0,
            "has_reset_event": len(reset_events) > 0
        }

    @keyword("Tool Count Increments")
    def tool_count_increments(self):
        """Tool count should increment with each run (normal mode)."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--reset"],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state1 = json.load(f)
        tools1 = state1.get("tool_count", 0)

        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state2 = json.load(f)
        tools2 = state2.get("tool_count", 0)

        return {"incremented": tools2 == tools1 + 1}

