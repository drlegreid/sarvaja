#!/usr/bin/env python3
"""
Pre-Bash Destructive Command Check - GAP-DESTRUCT-001

Per SAFETY-DESTR-01-v1: Checks Bash commands for destructive patterns
before execution. Blocks dangerous commands and warns about risky ones.

This hook reads the command from CLAUDE_TOOL_INPUT environment variable
and returns non-zero exit code to block execution if needed.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).parent
sys.path.insert(0, str(HOOKS_DIR))

from checkers.destructive import check_destructive_command, format_warning, get_safe_alternative


def log_destructive_attempt(result, action: str):
    """Log destructive command attempt to audit file."""
    log_dir = HOOKS_DIR / ".destructive_log"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"destructive_{datetime.now().strftime('%Y-%m-%d')}.jsonl"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "command": result.command,
        "pattern": result.pattern_matched,
        "risk": result.risk_description,
        "blocked": result.is_blocked,
        "action": action
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    """Check bash command for destructive patterns."""
    # Get the tool input from environment variable
    tool_input = os.environ.get("CLAUDE_TOOL_INPUT", "{}")

    try:
        input_data = json.loads(tool_input)
        command = input_data.get("command", "")
    except json.JSONDecodeError:
        # If not JSON, treat as raw command
        command = tool_input

    if not command:
        # No command, allow execution
        sys.exit(0)

    # Check for destructive patterns
    result = check_destructive_command(command)

    if result.is_blocked:
        # NEVER allow blocked commands
        log_destructive_attempt(result, "BLOCKED")
        warning = format_warning(result)
        # Output to stderr for user visibility
        print(f"\n{'='*60}", file=sys.stderr)
        print(warning, file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)
        # Return JSON for Claude Code to display
        output = {
            "status": "blocked",
            "message": result.risk_description,
            "command": result.command
        }
        print(json.dumps(output))
        sys.exit(1)  # Block execution

    elif result.is_destructive:
        # Warn about destructive command but allow (Claude will see warning)
        log_destructive_attempt(result, "WARNED")
        warning = format_warning(result)
        alternative = get_safe_alternative(result)

        # Return warning as context (non-blocking)
        output = {
            "status": "warning",
            "message": f"DESTRUCTIVE: {result.risk_description}",
            "command": result.command,
            "alternative": alternative,
            "rule": "SAFETY-DESTR-01-v1"
        }
        print(json.dumps(output))
        sys.exit(0)  # Allow but warn

    # Safe command
    sys.exit(0)


if __name__ == "__main__":
    main()
