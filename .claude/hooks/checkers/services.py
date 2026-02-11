"""
Service health checking for Claude Code hooks.

Per RULE-021: Validates MCP dependency chain services.
Platform: Linux (xubuntu) with Podman - migrated 2026-01-11
"""

import re
import socket
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..core.base import HookConfig, HookResult, ServiceStatus, DEFAULT_CONFIG


def check_port(host: str, port: int, timeout: float = 0.5) -> bool:
    """
    Quick port check with timeout protection.

    Args:
        host: Host to check
        port: Port number
        timeout: Socket timeout in seconds

    Returns:
        True if port is open
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def check_podman_running(timeout: float = 2.0) -> bool:
    """
    Check if Podman is responding.

    Args:
        timeout: Subprocess timeout in seconds

    Returns:
        True if Podman is running
    """
    try:
        result = subprocess.run(
            ["podman", "info"],
            capture_output=True,
            timeout=timeout
        )
        return result.returncode == 0
    except Exception:
        return False


# Alias for backward compatibility
check_docker_running = check_podman_running


def check_container(name_pattern: str, timeout: float = 5.0, project_root: Optional[str] = None) -> Tuple[bool, str, bool]:
    """
    Check if Podman container is running.

    Args:
        name_pattern: Pattern to match container name (case-insensitive)
        timeout: Subprocess timeout in seconds
        project_root: Path to project root for podman compose (optional)

    Returns:
        Tuple of (running: bool, status: str, is_starting: bool)
    """
    try:
        # Use podman compose ps (doesn't support --format like docker)
        cmd = ["podman", "compose", "--profile", "cpu", "ps"]
        cwd = project_root or str(Path(__file__).parent.parent.parent.parent)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        # Strip ANSI escape codes and parse table output
        clean_output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
        for line in clean_output.strip().split("\n"):
            # Skip header line and empty lines
            if not line or "CONTAINER ID" in line:
                continue
            # Look for name pattern and "Up" in the line
            if name_pattern in line.lower():
                if " up " in line.lower() or "\tup " in line.lower():
                    # Check if container is in starting state (health check pending)
                    is_starting = "(starting)" in line.lower() or "(health:" in line.lower()
                    # Extract status (rough - look for "Up X minutes" pattern)
                    status_match = re.search(r'Up \d+ \w+', line, re.IGNORECASE)
                    status = status_match.group(0) if status_match else "Up"
                    if is_starting:
                        status = f"{status} (starting)"
                    return True, status, is_starting
        return False, "not running", False
    except Exception as e:
        return False, f"error: {str(e)[:30]}", False


class ServiceChecker:
    """
    Checks health status of all MCP dependency services.

    Supports:
    - Podman daemon check
    - Container status checks
    - Port availability checks
    - Configurable timeouts
    """

    def __init__(self, config: Optional[HookConfig] = None):
        """
        Initialize service checker.

        Args:
            config: Hook configuration (uses DEFAULT_CONFIG if None)
        """
        self.config = config or DEFAULT_CONFIG

    def check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Check all services with timeout protection.

        Returns:
            Dictionary of service status information
        """
        services = {}

        # Podman daemon
        podman_ok = check_podman_running(self.config.subprocess_timeout)
        services["podman"] = {
            "status": ServiceStatus.OK.value if podman_ok else ServiceStatus.DOWN.value,
            "ok": podman_ok
        }

        if not podman_ok:
            # If Podman is down, skip container checks
            for svc in ["typedb", "chromadb", "litellm", "ollama"]:
                services[svc] = {"status": ServiceStatus.PODMAN_DOWN.value, "ok": False}
            return services

        # TypeDB (required)
        services["typedb"] = self._check_service(
            "typedb", self.config.service_ports["typedb"], required=True
        )

        # ChromaDB (required)
        services["chromadb"] = self._check_service(
            "chromadb", self.config.service_ports["chromadb"], required=True
        )

        # Governance API (required) — calls /api/health for deep readiness
        services["governance-api"] = self._check_api_health(self.config.service_ports["api"])

        # LiteLLM (optional)
        services["litellm"] = self._check_service(
            "litellm", self.config.service_ports["litellm"], required=False
        )

        # Ollama (optional)
        services["ollama"] = self._check_service(
            "ollama", self.config.service_ports["ollama"], required=False
        )

        return services

    def _check_api_health(self, port: int = 8082) -> Dict[str, Any]:
        """Call /api/health for deep API readiness (TypeDB connected, rules loaded)."""
        import json
        import urllib.request
        try:
            url = f"http://localhost:{port}/api/health"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=self.config.socket_timeout + 1) as resp:
                data = json.loads(resp.read())
            api_ok = data.get("status") == "ok"
            typedb_ok = data.get("typedb_connected", False)
            rules = data.get("rules_count", 0)
            detail = f"typedb={'OK' if typedb_ok else 'DOWN'}, {rules} rules"
            return {
                "status": ServiceStatus.OK.value if api_ok else "DEGRADED",
                "ok": api_ok,
                "port": port,
                "optional": False,
                "detail": detail,
            }
        except Exception:
            # Port check fallback
            port_ok = check_port("localhost", port, self.config.socket_timeout)
            if port_ok:
                return {"status": "UP_NO_HEALTH", "ok": True, "port": port, "optional": False,
                        "detail": "port open but /api/health unreachable"}
            return {"status": ServiceStatus.DOWN.value, "ok": False, "port": port, "optional": False}

    def _check_service(self, name: str, port: int, required: bool = True) -> Dict[str, Any]:
        """
        Check a single service.

        Args:
            name: Service name (used for container pattern matching)
            port: Service port
            required: Whether service is required

        Returns:
            Service status dictionary
        """
        running, status, is_starting = check_container(name, self.config.subprocess_timeout)
        port_ok = check_port("localhost", port, self.config.socket_timeout) if running else False

        if port_ok:
            status_str = ServiceStatus.OK.value
        elif is_starting:
            status_str = ServiceStatus.STARTING.value
        elif running:
            status_str = ServiceStatus.CONTAINER_UP.value
        elif required:
            status_str = ServiceStatus.DOWN.value
        else:
            status_str = ServiceStatus.OFF.value

        return {
            "status": status_str,
            "ok": port_ok,
            "port": port,
            "optional": not required,
            "is_starting": is_starting
        }

    def check_core(self) -> HookResult:
        """
        Check only core services and return a HookResult.

        Returns:
            HookResult with success status and details
        """
        services = self.check_all()

        # Check if all core services are OK
        core_ok = all(
            services.get(s, {}).get("ok", False)
            for s in self.config.core_services
        )

        if core_ok:
            return HookResult.ok(
                "All core MCP services healthy",
                services=services
            )
        else:
            failed = [
                s for s in self.config.core_services
                if not services.get(s, {}).get("ok", False)
            ]
            return HookResult.error(
                f"Core services down: {', '.join(failed)}",
                resolution_path="podman compose --profile cpu up -d",
                services=services,
                failed=failed
            )

    def get_failed_services(self, services: Optional[Dict[str, Dict[str, Any]]] = None) -> list:
        """
        Get list of failed core services.

        Args:
            services: Service status dict (runs check_all if None)

        Returns:
            List of failed service names
        """
        if services is None:
            services = self.check_all()

        return [
            s for s in self.config.core_services
            if not services.get(s, {}).get("ok", False)
        ]
