#!/usr/bin/env python3
"""
UserPromptSubmit Healthcheck - Lightweight Per-Prompt Check

Per RULE-021: Quick health verification on each prompt.
Only warns if CORE services are down - silent when healthy.

This is a lightweight version of the full SessionStart healthcheck.
Uses shared governance/health module for consistency (RULE-032).
"""

import json
import sys
import threading
from pathlib import Path

# Quick timeout - max 3 seconds
TIMEOUT = 3


def force_exit():
    """Force exit after timeout."""
    output_json("")  # Empty = no context injection
    sys.stdout.flush()
    import os
    os._exit(0)


# Start watchdog timer
watchdog = threading.Timer(TIMEOUT, force_exit)
watchdog.daemon = True
watchdog.start()


def output_json(context: str) -> None:
    """Output valid JSON for Claude Code context injection."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context
        }
    }
    print(json.dumps(output))


def check_entropy() -> tuple[str, str]:
    """Check entropy state and return (level, warning_msg or empty)."""
    try:
        HOOKS_DIR = Path(__file__).parent
        STATE_FILE = HOOKS_DIR / ".entropy_state.json"

        if not STATE_FILE.exists():
            return "LOW", ""

        state = json.loads(STATE_FILE.read_text())
        tool_count = state.get("tool_count", 0)

        # Thresholds
        CRITICAL = 150
        HIGH = 100

        if tool_count >= CRITICAL:
            return "CRITICAL", f"⚠️ [ENTROPY CRITICAL] {tool_count} tool calls - SAVE NOW!"
        elif tool_count >= HIGH:
            return "HIGH", f"[ENTROPY HIGH] {tool_count} tool calls - consider /save"
        return "OK", ""
    except Exception:
        return "UNKNOWN", ""


def main():
    """Quick health check - warn if services down OR entropy high."""
    try:
        # Add project root to path for shared module
        PROJECT_ROOT = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(PROJECT_ROOT))

        from governance.health import check_all_services, are_core_services_healthy, get_failed_services

        warnings = []

        # Check services
        services = check_all_services()
        if not are_core_services_healthy(services):
            failed = get_failed_services(services)
            warnings.append(f"[HEALTH WARN] Down: {', '.join(failed)} | Run: podman compose --profile cpu up -d")

        # Check entropy (CRITICAL pre-warning)
        entropy_level, entropy_msg = check_entropy()
        if entropy_msg:
            warnings.append(entropy_msg)

        if warnings:
            output_json(" | ".join(warnings))
        else:
            output_json("")

    except Exception as e:
        # Don't block on errors
        output_json(f"[HEALTH ERROR] {str(e)[:50]}")
    finally:
        watchdog.cancel()


if __name__ == "__main__":
    main()
    sys.exit(0)
