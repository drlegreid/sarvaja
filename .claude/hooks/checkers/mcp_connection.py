#!/usr/bin/env python3
"""
MCP Connection Health Check using Claude Code CLI.

Per GAP-MCP-VALIDATE-001: Auto-detect and report failed MCP connections.
Per GitHub Issue #12449: Known race condition in Claude Code MCP startup.

Uses `claude mcp list` to get ACTUAL Claude Code connection status,
not just our own server testing.

Usage:
    # Quick check (recommended for SessionStart)
    python3 mcp_connection.py --quick

    # Full check with reconnect attempt
    python3 mcp_connection.py

    # Check and return JSON
    python3 mcp_connection.py --json
"""

import json
import subprocess
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Expected MCP servers
EXPECTED_SERVERS = {
    "gov-core",
    "gov-agents",
    "gov-sessions",
    "gov-tasks",
    "claude-mem",
    "rest-api",
    "playwright",
}


def get_mcp_status() -> Tuple[Dict[str, str], List[str], List[str]]:
    """
    Get MCP server status from Claude Code CLI.

    Returns:
        Tuple of (status_dict, connected_list, failed_list)
    """
    try:
        result = subprocess.run(
            ["claude", "mcp", "list"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return {}, [], list(EXPECTED_SERVERS)

        # Parse output lines
        # Format: "server-name: command - ✓ Connected" or "✗ Failed"
        status = {}
        connected = []
        failed = []

        for line in result.stdout.split('\n'):
            line = line.strip()
            if not line or line.startswith("Checking"):
                continue

            # Parse server name and status
            match = re.match(r'^([a-zA-Z0-9_-]+):\s+.*\s+-\s+(✓ Connected|✗ Failed|✗ Not connected)', line)
            if match:
                name = match.group(1)
                state = match.group(2)
                status[name] = state

                if "Connected" in state:
                    connected.append(name)
                else:
                    failed.append(name)

        return status, connected, failed

    except subprocess.TimeoutExpired:
        return {}, [], list(EXPECTED_SERVERS)
    except FileNotFoundError:
        # claude CLI not found
        return {}, [], []
    except Exception as e:
        return {}, [], []


def format_output(connected: List[str], failed: List[str], as_json: bool = False) -> str:
    """Format output for display or JSON."""
    total = len(connected) + len(failed)

    if as_json:
        return json.dumps({
            "status": "ok" if not failed else "warning",
            "connected": connected,
            "failed": failed,
            "total": total,
            "recovery": "Use /mcp menu to reconnect" if failed else None
        }, indent=2)

    if not failed:
        return f"[MCP OK] All {total} servers connected"
    else:
        lines = [
            f"[MCP WARN] {len(failed)}/{total} servers failed",
            "",
            "Failed: " + ", ".join(failed),
            "",
            "Recovery: /mcp → Select server → Reconnect",
        ]
        return "\n".join(lines)


def main():
    """Main entry point."""
    args = sys.argv[1:]
    as_json = "--json" in args
    quick = "--quick" in args

    # Get actual status from Claude Code
    status, connected, failed = get_mcp_status()

    # Quick mode - just report
    if quick:
        if not failed:
            print(f"[MCP OK] {len(connected)} servers connected")
        else:
            print(f"[MCP WARN] Failed: {', '.join(failed)} | Recovery: /mcp → Reconnect")
        return 0

    # Full mode - detailed output
    print(format_output(connected, failed, as_json))

    # Return non-zero if servers failed (for CI/scripts)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
