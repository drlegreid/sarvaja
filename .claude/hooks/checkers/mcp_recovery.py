#!/usr/bin/env python3
"""
MCP Recovery Tool - Check and fix failed MCP connections.

Per GAP-MCP-VALIDATE-001: Workaround for Claude Code MCP race condition.
Per GitHub Issue #12449: Connection establishes then closes within 1ms.

Features:
1. Check status using `claude mcp list`
2. Attempt recovery via remove/add cycle (forces reconnect)

Usage:
    # Check status
    python3 mcp_recovery.py check

    # Check and attempt recovery
    python3 mcp_recovery.py recover

    # JSON output
    python3 mcp_recovery.py check --json
"""

import json
import subprocess
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def run_cmd(cmd: List[str], timeout: int = 30) -> Tuple[int, str, str]:
    """Run command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -1, "", str(e)


def get_mcp_status() -> Dict[str, str]:
    """Get MCP server status from Claude Code CLI."""
    code, stdout, _ = run_cmd(["claude", "mcp", "list"])
    if code != 0:
        return {}

    status = {}
    for line in stdout.split('\n'):
        match = re.match(r'^([a-zA-Z0-9_-]+):\s+.*\s+-\s+(✓ Connected|✗ Failed|✗ Not connected)', line.strip())
        if match:
            status[match.group(1)] = "connected" if "Connected" in match.group(2) else "failed"
    return status


def get_server_config(name: str) -> Optional[Dict]:
    """Get server config from .mcp.json."""
    mcp_path = PROJECT_ROOT / ".mcp.json"
    if not mcp_path.exists():
        return None
    try:
        with open(mcp_path) as f:
            config = json.load(f)
        return config.get("mcpServers", {}).get(name)
    except:
        return None


def attempt_reconnect(name: str) -> Tuple[bool, str]:
    """Attempt to reconnect via remove/add cycle."""
    config = get_server_config(name)
    if not config:
        return False, "No config found"

    # Remove server
    code, _, stderr = run_cmd(["claude", "mcp", "remove", name, "-s", "project"])
    if code != 0 and "not found" not in stderr.lower():
        return False, f"Remove failed: {stderr}"

    # Re-add server
    args = config.get("args", [])
    cmd = config.get("command", "")
    add_cmd = ["claude", "mcp", "add", name]
    
    for key, value in config.get("env", {}).items():
        add_cmd.extend(["-e", f"{key}={value}"])
    
    add_cmd.extend(["-s", "project", "--", cmd] + args)
    
    code, _, stderr = run_cmd(add_cmd)
    if code != 0:
        return False, f"Add failed: {stderr}"

    return True, "Recovery initiated - restart IDE to complete"


def cmd_check(as_json: bool = False):
    """Check MCP status."""
    status = get_mcp_status()
    if not status:
        print("ERROR: Could not get MCP status" if not as_json else json.dumps({"error": "Cannot get status"}))
        return 1

    connected = [k for k, v in status.items() if v == "connected"]
    failed = [k for k, v in status.items() if v == "failed"]

    if as_json:
        print(json.dumps({
            "connected": connected,
            "failed": failed,
            "total": len(status),
            "recovery": "python3 .claude/hooks/checkers/mcp_recovery.py recover" if failed else None
        }, indent=2))
    else:
        for name, state in sorted(status.items()):
            icon = "✓" if state == "connected" else "✗"
            print(f"  {icon} {name}: {state}")
        print(f"\n{len(connected)}/{len(status)} connected")
        if failed:
            print(f"\nFailed: {', '.join(failed)}")
            print("\nRecovery: python3 .claude/hooks/checkers/mcp_recovery.py recover")

    return 1 if failed else 0


def cmd_recover():
    """Attempt recovery for failed servers."""
    print("=== MCP Recovery ===\n")
    status = get_mcp_status()
    
    if not status:
        print("ERROR: Could not get MCP status")
        return 1

    failed = [k for k, v in status.items() if v == "failed"]
    if not failed:
        print("All servers connected - no recovery needed")
        return 0

    print(f"Attempting recovery for {len(failed)} servers...\n")
    
    recovered = []
    still_failed = []

    for name in failed:
        print(f"  {name}...", end=" ")
        success, msg = attempt_reconnect(name)
        if success:
            recovered.append(name)
            print(f"✓ {msg}")
        else:
            still_failed.append(name)
            print(f"✗ {msg}")

    print(f"\n=== Results ===")
    print(f"Recovered: {len(recovered)}")
    print(f"Failed: {len(still_failed)}")

    if recovered:
        print("\n⚠️  RESTART IDE to complete recovery")

    if still_failed:
        print(f"\nStill failing: {', '.join(still_failed)}")
        print("Try: /mcp → Select server → Reconnect")
        return 1

    return 0


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: mcp_recovery.py <check|recover> [--json]")
        return 1

    cmd = args[0]
    as_json = "--json" in args

    if cmd == "check":
        return cmd_check(as_json)
    elif cmd == "recover":
        return cmd_recover()
    else:
        print(f"Unknown command: {cmd}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
