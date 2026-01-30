"""
Infrastructure Health Controller.

Per PLAN-UI-OVERHAUL-001 Task 6.3: Infra Health Intent.
Per RULE-012: Single Responsibility - only infra health logic.
Per RULE-032: File size limit (<300 lines).

Extracts health check logic from data_loaders.py for clean separation.
Provides service health checks, MCP health verification, and system stats.
"""

import json
import os
import socket
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any


# Expected MCP servers in the governance platform
MCP_SERVERS = ["claude-mem", "gov-core", "gov-agents", "gov-sessions", "gov-tasks"]

# Service configuration: (container_host, container_port, host_port)
SERVICE_CONFIG = {
    "typedb": ("typedb", 1729, 1729),
    "chromadb": ("chromadb", 8000, 8001),
    "litellm": ("litellm", 4000, 4000),
    "ollama": ("ollama", 11434, 11434),
}

# Required vs optional services
REQUIRED_SERVICES = {"typedb", "chromadb"}


def is_in_container() -> bool:
    """Detect if running inside a container."""
    return os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")


def check_port(hostname: str, port: int, timeout: int = 2) -> bool:
    """Check if a TCP port is reachable."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((hostname, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def check_podman_health() -> bool:
    """Check if podman daemon is responsive."""
    if is_in_container():
        return True
    try:
        result = subprocess.run(
            ["podman", "info"], capture_output=True, timeout=2
        )
        return result.returncode == 0
    except Exception:
        return False


def check_service_health(name: str) -> dict[str, Any]:
    """Check health of a named service. Returns status dict."""
    if name == "podman":
        ok = check_podman_health()
        return {"status": "OK" if ok else "DOWN", "ok": ok, "port": "daemon"}

    if name not in SERVICE_CONFIG:
        return {"status": "UNKNOWN", "ok": False, "port": "?"}

    container_host, container_port, host_port = SERVICE_CONFIG[name]
    in_container = is_in_container()

    if in_container:
        ok = check_port(container_host, container_port)
    else:
        ok = check_port("localhost", host_port)

    required = name in REQUIRED_SERVICES
    status = "OK" if ok else ("DOWN" if required else "OFF")
    return {"status": status, "ok": ok, "port": host_port}


def check_all_services() -> dict[str, dict]:
    """Check health of all infrastructure services."""
    services = {"podman": check_service_health("podman")}
    for name in SERVICE_CONFIG:
        services[name] = check_service_health(name)
    return services


def get_mcp_server_status(healthcheck_state: dict | None = None) -> dict[str, str]:
    """Get MCP server status from healthcheck state.

    Returns dict of server_name -> status (OK/ON-DEMAND/UNKNOWN).
    """
    mcp_status = {}
    components = {}
    if healthcheck_state:
        components = healthcheck_state.get("components", {})

    for name in MCP_SERVERS:
        if name in components:
            mcp_status[name] = components[name]
        else:
            mcp_status[name] = "ON-DEMAND"
    return mcp_status


def get_system_stats() -> dict[str, Any]:
    """Collect system-level statistics."""
    stats: dict[str, Any] = {
        "memory_pct": 0,
        "python_procs": 0,
        "frankel_hash": "--------",
        "last_check": "Never",
    }

    # Memory usage from /proc/meminfo
    try:
        with open("/proc/meminfo") as f:
            meminfo = f.read()
        lines = meminfo.split("\n")
        total = int([l for l in lines if "MemTotal" in l][0].split()[1])
        avail = int([l for l in lines if "MemAvailable" in l][0].split()[1])
        stats["memory_pct"] = round((total - avail) / total * 100, 1)
    except Exception:
        pass

    # Python process count
    try:
        result = subprocess.run(
            ["pgrep", "-c", "python3"], capture_output=True, text=True, timeout=2
        )
        stats["python_procs"] = int(result.stdout.strip() or "0")
    except Exception:
        pass

    return stats


def check_dsp_conditions(evidence_dir: Path | None = None) -> dict[str, Any]:
    """Check DSP (Deep Sleep Protocol) conditions. Per SESSION-DSP-NOTIFY-01-v1."""
    result: dict[str, Any] = {"dsp_suggested": False, "dsp_alerts": []}
    if evidence_dir is None:
        evidence_dir = Path(__file__).parent.parent.parent.parent / "evidence"

    try:
        if evidence_dir.exists():
            evidence_count = len(list(evidence_dir.glob("SESSION-*.md")))
            if evidence_count > 20:
                result["dsp_alerts"].append(
                    f"Evidence accumulation: {evidence_count} session files"
                )
            dsp_files = sorted(evidence_dir.glob("*DSP*.md"), reverse=True)
            if dsp_files:
                date_parts = dsp_files[0].name.split("-")[1:4]
                if len(date_parts) == 3:
                    dsp_date = datetime(
                        int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
                    )
                    days_since = (datetime.now() - dsp_date).days
                    if days_since > 7:
                        result["dsp_alerts"].append(
                            f"No DSP cycle in {days_since} days"
                        )
            else:
                result["dsp_alerts"].append("No DSP cycle found")
        result["dsp_suggested"] = len(result["dsp_alerts"]) >= 2
    except Exception:
        pass

    return result
