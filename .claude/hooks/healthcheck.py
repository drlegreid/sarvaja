#!/usr/bin/env python3
"""
Session Start Healthcheck - Non-Blocking with Auto-Recovery

Per RULE-021, GAP-MCP-003: Validates MCP dependency chain with:
- 30-second retry ceiling when state unchanged
- 3-second max execution time (never blocks Claude Code)
- Always returns valid JSON (graceful degradation)
- Hash-based incremental checking (Frankel hash)
- Auto-recovery: Starts Docker Desktop and containers in background

CRITICAL: Windows stdin EOF issue - do NOT read stdin, just run and exit.
Per GitHub issues #9591, #10373, #11519 - SessionStart hooks can hang.

Chain: Claude Code → claude-mem MCP → governance MCP → TypeDB/ChromaDB (Docker)

CORE MCPs (must be running for governance):
- TypeDB (port 1729) - Rule inference engine
- ChromaDB (port 8001) - Semantic search for claude-mem
"""

import hashlib
import json
import os
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configuration
GLOBAL_TIMEOUT = 3  # Max seconds for entire script (reduced from 5)
SUBPROCESS_TIMEOUT = 1  # Max seconds per subprocess call (reduced from 2)
SOCKET_TIMEOUT = 0.5  # Max seconds per socket check (reduced from 1)
RETRY_CEILING_SECONDS = 30  # Stop detailed checks after this unchanged duration
RECOVERY_COOLDOWN = 60  # Seconds between recovery attempts
STATE_FILE = Path(__file__).parent / ".healthcheck_state.json"
PROJECT_ROOT = Path(__file__).parent.parent.parent  # .claude/hooks -> project root
DEPLOY_SCRIPT = PROJECT_ROOT / "deploy.ps1"
DOCKER_DESKTOP = Path(r"C:\Program Files\Docker\Docker\Docker Desktop.exe")

# CORE MCP Dependencies (required for governance)
CORE_SERVICES = ["docker", "typedb", "chromadb"]


def force_exit():
    """Force exit after timeout - Windows safety."""
    output_json("[TIMEOUT] Healthcheck force-exit after 3s")
    sys.stdout.flush()  # Critical: flush before os._exit
    os._exit(0)  # Hard exit, no cleanup


# Start watchdog timer immediately (Windows doesn't support SIGALRM)
watchdog = threading.Timer(GLOBAL_TIMEOUT, force_exit)
watchdog.daemon = True
watchdog.start()


def compute_frankel_hash(data: Dict[str, Any]) -> str:
    """Compute Frankel-style hash (first 8 chars of SHA256, uppercase)."""
    serialized = json.dumps(data, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()[:8].upper()


def load_previous_state() -> Dict[str, Any]:
    """Load previous healthcheck state from file."""
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_current_state(state: Dict[str, Any]) -> None:
    """Save current healthcheck state to file."""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass  # Non-critical


def check_port(host: str, port: int) -> bool:
    """Quick port check with timeout protection."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SOCKET_TIMEOUT)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def check_docker_running() -> bool:
    """Check if Docker daemon is responding."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=SUBPROCESS_TIMEOUT
        )
        return result.returncode == 0
    except Exception:
        return False


def check_container(name_pattern: str) -> tuple:
    """Check if Docker container is running. Returns (running, status)."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}|{{.Status}}"],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT
        )
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                name, status = line.split("|", 1)
                if name_pattern in name.lower() and "up" in status.lower():
                    return True, status
        return False, "not running"
    except Exception as e:
        return False, f"error: {str(e)[:30]}"


def check_services() -> Dict[str, Dict[str, Any]]:
    """Check all services with timeout protection."""
    services = {}

    # Docker daemon
    docker_ok = check_docker_running()
    services["docker"] = {"status": "OK" if docker_ok else "DOWN", "ok": docker_ok}

    if not docker_ok:
        # If Docker is down, skip container checks
        for svc in ["typedb", "chromadb", "litellm", "ollama"]:
            services[svc] = {"status": "DOCKER_DOWN", "ok": False}
        return services

    # TypeDB (required)
    running, status = check_container("typedb")
    port_ok = check_port("localhost", 1729) if running else False
    services["typedb"] = {
        "status": "OK" if port_ok else ("CONTAINER_UP" if running else "DOWN"),
        "ok": port_ok,
        "port": 1729
    }

    # ChromaDB (required)
    running, status = check_container("chromadb")
    port_ok = check_port("localhost", 8001) if running else False
    services["chromadb"] = {
        "status": "OK" if port_ok else ("CONTAINER_UP" if running else "DOWN"),
        "ok": port_ok,
        "port": 8001
    }

    # LiteLLM (optional)
    port_ok = check_port("localhost", 4000)
    services["litellm"] = {"status": "OK" if port_ok else "OFF", "ok": port_ok, "optional": True}

    # Ollama (optional)
    port_ok = check_port("localhost", 11434)
    services["ollama"] = {"status": "OK" if port_ok else "OFF", "ok": port_ok, "optional": True}

    return services


def start_docker_desktop() -> bool:
    """Start Docker Desktop in background (non-blocking)."""
    try:
        if DOCKER_DESKTOP.exists():
            # Start Docker Desktop without waiting
            subprocess.Popen(
                [str(DOCKER_DESKTOP)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
            )
            return True
    except Exception:
        pass
    return False


def start_containers() -> bool:
    """Start CORE containers using docker compose (non-blocking).

    Note: deploy.ps1 has strict error handling that fails on docker info warnings.
    Using docker compose directly is more reliable for auto-recovery.
    """
    try:
        # Start CORE services directly with docker compose
        # This is more reliable than deploy.ps1 which has strict $ErrorActionPreference
        subprocess.Popen(
            ["docker", "compose", "--profile", "cpu", "up", "-d", "typedb", "chromadb"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(PROJECT_ROOT),
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
        )
        return True
    except Exception:
        pass
    return False


def attempt_recovery(services: Dict, prev_state: Dict) -> List[str]:
    """
    Attempt auto-recovery based on service state.
    Returns list of recovery actions taken.
    """
    actions = []
    last_recovery = prev_state.get("last_recovery", 0)

    # Check cooldown
    if time.time() - last_recovery < RECOVERY_COOLDOWN:
        return []  # Still in cooldown, skip recovery

    docker_ok = services.get("docker", {}).get("ok", False)

    # Scenario 1: Docker Desktop not running
    if not docker_ok:
        if start_docker_desktop():
            actions.append("STARTING Docker Desktop")
        return actions  # Can't start containers without Docker

    # Scenario 2: Docker running but CORE containers down
    core_down = [s for s in ["typedb", "chromadb"]
                 if not services.get(s, {}).get("ok", False)]

    if core_down:
        if start_containers():
            actions.append(f"STARTING containers ({', '.join(core_down)})")

    return actions


def check_amnesia_indicators(prev_state: Dict) -> Dict[str, Any]:
    """
    Check for AMNESIA indicators by analyzing state patterns.

    AMNESIA Detection Heuristics:
    - Hash changed from previous session → Context may be stale
    - Long time since last check → Potential session restart
    - Services were down and now up → Likely restart occurred

    Returns dict with: detected (bool), confidence (0-1), indicators (list)
    """
    indicators = []
    confidence = 0.0

    prev_hash = prev_state.get("master_hash", "")
    prev_components = prev_state.get("components", {})
    last_check_str = prev_state.get("last_check", "")

    # Indicator 1: No previous state (first run or state wiped)
    if not prev_hash:
        indicators.append("NO_PREVIOUS_STATE")
        confidence += 0.3

    # Indicator 2: Long gap since last check (>1 hour)
    if last_check_str:
        try:
            last_check = datetime.fromisoformat(last_check_str)
            gap_hours = (datetime.now() - last_check).total_seconds() / 3600
            if gap_hours > 1:
                indicators.append(f"LONG_GAP_{int(gap_hours)}h")
                confidence += min(0.4, gap_hours * 0.1)  # Max 0.4
        except Exception:
            pass

    # Indicator 3: Services were DOWN, now UP (restart recovery)
    for svc in CORE_SERVICES:
        prev_status = prev_components.get(svc, "")
        if prev_status in ("DOWN", "DOCKER_DOWN"):
            indicators.append(f"SERVICE_RECOVERED:{svc}")
            confidence += 0.2

    return {
        "detected": confidence >= 0.5,
        "confidence": min(1.0, confidence),
        "indicators": indicators
    }


def format_detailed(services: Dict, master_hash: str, recovery_actions: List[str] = None, amnesia: Dict = None) -> str:
    """Format detailed output with component chain and AMNESIA detection."""
    lines = [f"=== MCP DEPENDENCY CHAIN [Hash: {master_hash}] ===", ""]

    required_ok = all(services.get(s, {}).get("ok", False) for s in CORE_SERVICES)

    lines.append("Required Services (CORE MCPs):")
    for name in CORE_SERVICES:
        data = services.get(name, {})
        status = data.get("status", "UNKNOWN")
        port = data.get("port", "")
        port_str = f" (:{port})" if port else ""
        icon = "✓" if data.get("ok") else "✗"
        lines.append(f"  {icon} {name.upper()}{port_str}: {status}")

    lines.append("")
    lines.append("Optional Services:")
    for name in ["litellm", "ollama"]:
        data = services.get(name, {})
        status = data.get("status", "UNKNOWN")
        port = data.get("port", "")
        port_str = f" (:{port})" if port else ""
        icon = "✓" if data.get("ok") else "○"
        lines.append(f"  {icon} {name.upper()}{port_str}: {status}")

    # AMNESIA Detection
    if amnesia and amnesia.get("detected"):
        lines.append("")
        lines.append(f"⚠️ AMNESIA RISK: {int(amnesia['confidence']*100)}% confidence")
        lines.append(f"  Indicators: {', '.join(amnesia['indicators'])}")
        lines.append("  Action: Run /remember sim-ai to restore context")

    # Show recovery actions if any
    if recovery_actions:
        lines.append("")
        lines.append("Auto-Recovery:")
        for action in recovery_actions:
            lines.append(f"  → {action}")
        lines.append("  (Run /health again in 30-60s to verify)")
    elif not required_ok:
        lines.append("")
        lines.append("Manual Recovery: .\\deploy.ps1 -Action up -Profile cpu")

    return "\n".join(lines)


def format_summary(services: Dict, master_hash: str, reason: str = "", recovery_actions: List[str] = None) -> str:
    """Format summary output (for unchanged state or retry ceiling)."""
    required_ok = all(services.get(s, {}).get("ok", False) for s in CORE_SERVICES)

    if required_ok:
        return f"[HEALTH OK] Hash: {master_hash} {reason}. MCP chain ready."
    else:
        failed = [s for s in CORE_SERVICES if not services.get(s, {}).get("ok", False)]
        if recovery_actions:
            recovery_str = " | " + "; ".join(recovery_actions)
            return f"[HEALTH RECOVERING] Hash: {master_hash} {reason}. Down: {', '.join(failed)}{recovery_str}"
        else:
            hint = " | Recovery: .\\deploy.ps1 -Action up" if failed else ""
            return f"[HEALTH WARN] Hash: {master_hash} {reason}. Down: {', '.join(failed)}{hint}"


def format_cached(prev_state: Dict) -> str:
    """Format cached response when retry ceiling reached."""
    master_hash = prev_state.get("master_hash", "????????")
    components = prev_state.get("components", {})

    failed = [s for s, status in components.items() if status not in ("OK", "OFF") and s in CORE_SERVICES]

    if failed:
        return f"[CACHED] Hash: {master_hash} (retry ceiling reached). Down: {', '.join(failed)} | Recovery: .\\deploy.ps1 -Action up"
    else:
        return f"[CACHED] Hash: {master_hash} (retry ceiling reached). MCP chain ready."


def output_json(context: str) -> None:
    """Output valid JSON for Claude Code context injection."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context
        }
    }
    print(json.dumps(output))


def main():
    """Main healthcheck logic with non-blocking guarantees and auto-recovery."""
    try:
        # Load previous state
        prev_state = load_previous_state()
        prev_hash = prev_state.get("master_hash", "")
        unchanged_since = prev_state.get("unchanged_since", 0)

        # Check if retry ceiling reached (30s of unchanged state)
        if unchanged_since > 0 and (time.time() - unchanged_since) > RETRY_CEILING_SECONDS:
            # Return cached summary without rechecking
            output_json(format_cached(prev_state))
            return

        # Run service checks
        services = check_services()

        # Compute master hash
        state_for_hash = {name: data["status"] for name, data in services.items()}
        master_hash = compute_frankel_hash(state_for_hash)

        # Determine if state changed
        hash_changed = master_hash != prev_hash
        check_count = prev_state.get("check_count", 0) + 1

        # Update unchanged_since tracking
        if hash_changed:
            new_unchanged_since = time.time()  # Reset timer on change
        else:
            new_unchanged_since = unchanged_since if unchanged_since > 0 else time.time()

        # Attempt auto-recovery if CORE services are down
        recovery_actions = []
        required_ok = all(services.get(s, {}).get("ok", False) for s in CORE_SERVICES)
        if not required_ok:
            recovery_actions = attempt_recovery(services, prev_state)

        # Save current state (include recovery tracking)
        current_state = {
            "master_hash": master_hash,
            "check_count": check_count,
            "last_check": datetime.now().isoformat(),
            "unchanged_since": new_unchanged_since,
            "components": state_for_hash
        }
        if recovery_actions:
            current_state["last_recovery"] = time.time()
            current_state["recovery_actions"] = recovery_actions
        save_current_state(current_state)

        # Check for AMNESIA indicators
        amnesia = check_amnesia_indicators(prev_state)

        # Format output based on state
        if hash_changed or check_count == 1:
            context = format_detailed(services, master_hash, recovery_actions, amnesia)
        else:
            unchanged_duration = time.time() - new_unchanged_since
            context = format_summary(services, master_hash, f"(unchanged {int(unchanged_duration)}s)", recovery_actions)

        output_json(context)

    except Exception as e:
        output_json(f"[ERROR] Healthcheck failed: {str(e)[:100]}")
    finally:
        # Cancel watchdog timer on successful completion
        watchdog.cancel()


if __name__ == "__main__":
    main()
    sys.exit(0)  # Always exit 0 - never block Claude Code
