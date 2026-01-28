"""
Robot Framework Library for Claude Code Hooks - Entropy Warning & Non-Blocking Tests.
Split from ClaudeHooksEntropyLibrary.py per DOC-SIZE-01-v1

Covers: Warning Thresholds, Non-Blocking Performance Tests.
Per EPIC-006: Entropy Monitor for SLEEP Mode Automation
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from robot.api.deco import keyword

HOOKS_DIR = Path(__file__).parent.parent.parent / ".claude" / "hooks"
ENTROPY_SCRIPT = HOOKS_DIR / "entropy_monitor.py"


class ClaudeHooksEntropyAdvancedLibrary:
    """Library for Claude Code entropy monitor warning and performance tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Entropy Monitor Warning Tests
    # =========================================================================

    @keyword("No Warning Below Threshold")
    def no_warning_below_threshold(self):
        """Should not show warning below LOW_THRESHOLD (50)."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        state = {
            "session_start": "2026-01-01T00:00:00",
            "session_hash": "TEST",
            "tool_count": 10,
            "check_count": 0,
            "last_save": None,
            "warnings_shown": 0,
            "last_warning_at": 0,
            "history": []
        }
        with open(state_file, "w") as f:
            json.dump(state, f)

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        if "hookSpecificOutput" in output:
            context = output["hookSpecificOutput"].get("additionalContext", "")
            return {"no_warning": "CHECKPOINT" not in context and "ENTROPY HIGH" not in context}

        return {"no_warning": True}

    @keyword("Low Threshold Warning")
    def low_threshold_warning(self):
        """Should show warning at LOW_THRESHOLD (50)."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        state = {
            "session_start": "2026-01-01T00:00:00",
            "session_hash": "TEST",
            "tool_count": 49,
            "check_count": 0,
            "last_save": None,
            "warnings_shown": 0,
            "last_warning_at": 0,
            "history": []
        }
        with open(state_file, "w") as f:
            json.dump(state, f)

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        context = output.get("hookSpecificOutput", {}).get("additionalContext", "")

        return {"has_warning": "CHECKPOINT" in context or "50 tool calls" in context}

    @keyword("High Threshold Warning")
    def high_threshold_warning(self):
        """Should show strong warning at HIGH_THRESHOLD (100)."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        state = {
            "session_start": "2026-01-01T00:00:00",
            "session_hash": "TEST",
            "tool_count": 99,
            "check_count": 0,
            "last_save": None,
            "warnings_shown": 1,
            "last_warning_at": 50,
            "history": []
        }
        with open(state_file, "w") as f:
            json.dump(state, f)

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        context = output.get("hookSpecificOutput", {}).get("additionalContext", "")

        return {"has_warning": "ENTROPY HIGH" in context or "100 tool calls" in context}

    # =========================================================================
    # Entropy Monitor Non-Blocking Tests
    # =========================================================================

    @keyword("Entropy Completes Quickly")
    def entropy_completes_quickly(self):
        """Entropy monitor must complete within 1 second."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        start = time.time()
        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )
        elapsed = time.time() - start

        return {
            "within_1s": elapsed < 1,
            "exit_zero": result.returncode == 0,
            "elapsed": elapsed
        }

    @keyword("Graceful On Corrupt State")
    def graceful_on_corrupt_state(self):
        """Should handle corrupt state file gracefully."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        with open(state_file, "w") as f:
            f.write("{invalid json")

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        try:
            output = json.loads(result.stdout)
            return {
                "exit_zero": result.returncode == 0,
                "valid_json": isinstance(output, dict)
            }
        except json.JSONDecodeError:
            return {"exit_zero": result.returncode == 0, "valid_json": False}
