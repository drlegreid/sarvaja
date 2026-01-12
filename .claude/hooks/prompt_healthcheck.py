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


def main():
    """Quick health check - only warn if services down."""
    try:
        # Add project root to path for shared module
        PROJECT_ROOT = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(PROJECT_ROOT))

        from governance.health import check_all_services, are_core_services_healthy, get_failed_services

        services = check_all_services()

        if are_core_services_healthy(services):
            # All good - silent output (no context injection)
            output_json("")
        else:
            # Services down - warn
            failed = get_failed_services(services)
            context = f"[HEALTH WARN] Down: {', '.join(failed)} | Run: podman compose --profile cpu up -d"
            output_json(context)

    except Exception as e:
        # Don't block on errors
        output_json(f"[HEALTH ERROR] {str(e)[:50]}")
    finally:
        watchdog.cancel()


if __name__ == "__main__":
    main()
    sys.exit(0)
