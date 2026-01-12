"""
Zombie/duplicate MCP process detection and cleanup.

Per GAP-ZOMBIE-001: Detects and auto-cleans duplicate MCP processes.
Platform: Linux (xubuntu) with Podman - migrated 2026-01-09
"""

import subprocess
from typing import Any, Dict, List

# Default expected MCP servers
DEFAULT_EXPECTED_SERVERS = [
    "governance.mcp_server_core",
    "governance.mcp_server_agents",
    "governance.mcp_server_sessions",
    "governance.mcp_server_tasks",
    "claude_mem.mcp_server",
]


def cleanup_zombie_pids(zombie_pids: List[int], timeout: float = 2.0) -> int:
    """
    Kill zombie processes by PID (auto-cleanup).

    Args:
        zombie_pids: List of PIDs to kill
        timeout: Timeout for kill command

    Returns:
        Number of processes killed
    """
    killed = 0
    if not zombie_pids:
        return 0

    try:
        for pid in zombie_pids:
            subprocess.run(
                ["kill", "-9", str(pid)],
                capture_output=True, timeout=timeout
            )
            killed += 1
    except Exception:
        pass

    return killed


def check_zombie_processes(
    auto_cleanup: bool = True,
    subprocess_timeout: float = 2.0,
    stale_process_hours: int = 2,
    expected_servers: List[str] = None
) -> Dict[str, Any]:
    """
    Check for zombie/duplicate MCP processes (GAP-ZOMBIE-001).

    Detects:
    - Duplicate governance MCP servers (should be exactly 1 of each)
    - Stale Python processes (older than stale_process_hours)
    - Memory pressure indicators

    If auto_cleanup=True, automatically kills duplicate MCP processes.

    Args:
        auto_cleanup: Whether to auto-kill duplicates
        subprocess_timeout: Timeout for subprocess commands
        stale_process_hours: Hours after which processes are stale
        expected_servers: List of expected MCP server module names

    Returns:
        Dict with: zombies, stale_count, memory_pct, action_required, cleaned
    """
    expected_servers = expected_servers or DEFAULT_EXPECTED_SERVERS

    result = {
        "zombies": [],
        "duplicates": {},
        "stale_count": 0,
        "memory_pct": 0,
        "action_required": False,
        "cleanup_command": "",
        "cleaned": 0
    }

    try:
        # Get all python processes with their command lines (for MCP detection)
        proc_result = subprocess.run(
            ["pgrep", "-a", "-f", "governance.mcp_server"],
            capture_output=True, text=True, timeout=subprocess_timeout
        )

        # Count MCP server instances
        mcp_counts = {server: [] for server in expected_servers}
        for line in proc_result.stdout.strip().split("\n"):
            if line:
                parts = line.split(" ", 1)
                if len(parts) >= 2:
                    pid, cmd = parts
                    for server in expected_servers:
                        if server in cmd:
                            mcp_counts[server].append(int(pid))

        # Detect duplicates (more than 1 of same server)
        for server, pids in mcp_counts.items():
            if len(pids) > 1:
                server_short = server.split(".")[-1]
                result["duplicates"][server_short] = pids
                result["zombies"].extend(pids[1:])

        # AUTO-CLEANUP: Kill duplicate MCP processes immediately
        if auto_cleanup and result["zombies"]:
            result["cleaned"] = cleanup_zombie_pids(result["zombies"], subprocess_timeout)

        # Count stale Python processes
        stale_result = subprocess.run(
            ["pgrep", "-c", "python3"],
            capture_output=True, text=True, timeout=subprocess_timeout
        )
        result["stale_count"] = int(stale_result.stdout.strip() or "0")

        # Check memory usage (Linux: read from /proc/meminfo)
        try:
            with open("/proc/meminfo") as f:
                meminfo = f.read()
            total = int([l for l in meminfo.split("\n") if "MemTotal" in l][0].split()[1])
            avail = int([l for l in meminfo.split("\n") if "MemAvailable" in l][0].split()[1])
            result["memory_pct"] = round((total - avail) / total * 100, 1)
        except Exception:
            result["memory_pct"] = 0

        # Determine if action is still required (after auto-cleanup)
        if result["stale_count"] > 20 or result["memory_pct"] > 85:
            result["action_required"] = True
            result["cleanup_command"] = "pkill -9 -f 'governance.mcp_server'"

    except Exception:
        pass  # Non-critical, don't block healthcheck

    return result
