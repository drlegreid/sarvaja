"""
Service Health Checks
=====================
Shared functions to check TypeDB, ChromaDB, and Podman health.

Per RULE-021: MCP Healthcheck Protocol
"""

import socket
import subprocess
from dataclasses import dataclass
from typing import Dict, Optional

# Configuration
SOCKET_TIMEOUT = 0.5
SUBPROCESS_TIMEOUT = 2

# CORE Services
CORE_SERVICES = ["podman", "typedb", "chromadb"]


@dataclass
class ServiceStatus:
    """Status of a service."""
    name: str
    ok: bool
    status: str
    port: Optional[int] = None
    error: Optional[str] = None


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


def check_podman() -> ServiceStatus:
    """Check if Podman is responding."""
    try:
        result = subprocess.run(
            ["podman", "info"],
            capture_output=True,
            timeout=SUBPROCESS_TIMEOUT
        )
        ok = result.returncode == 0
        return ServiceStatus(
            name="podman",
            ok=ok,
            status="OK" if ok else "DOWN"
        )
    except Exception as e:
        return ServiceStatus(
            name="podman",
            ok=False,
            status="DOWN",
            error=str(e)[:50]
        )


def check_typedb(host: str = "localhost", port: int = 1729) -> ServiceStatus:
    """
    Check TypeDB health via port check.

    For deeper health check, use TypeDB client directly.
    """
    port_ok = check_port(host, port)
    return ServiceStatus(
        name="typedb",
        ok=port_ok,
        status="OK" if port_ok else "DOWN",
        port=port
    )


def check_chromadb(host: str = "localhost", port: int = 8001) -> ServiceStatus:
    """
    Check ChromaDB health via port check.

    ChromaDB runs on 8001 (mapped from container 8000).
    """
    port_ok = check_port(host, port)
    return ServiceStatus(
        name="chromadb",
        ok=port_ok,
        status="OK" if port_ok else "DOWN",
        port=port
    )


def check_all_services(
    typedb_host: str = "localhost",
    typedb_port: int = 1729,
    chromadb_host: str = "localhost",
    chromadb_port: int = 8001
) -> Dict[str, ServiceStatus]:
    """
    Check all CORE services.

    Returns dict with service name -> ServiceStatus.
    """
    services = {}

    # Check Podman first
    podman_status = check_podman()
    services["podman"] = podman_status

    if not podman_status.ok:
        # If Podman is down, mark all container services as PODMAN_DOWN
        services["typedb"] = ServiceStatus(
            name="typedb",
            ok=False,
            status="PODMAN_DOWN",
            port=typedb_port
        )
        services["chromadb"] = ServiceStatus(
            name="chromadb",
            ok=False,
            status="PODMAN_DOWN",
            port=chromadb_port
        )
        return services

    # Check TypeDB
    services["typedb"] = check_typedb(typedb_host, typedb_port)

    # Check ChromaDB
    services["chromadb"] = check_chromadb(chromadb_host, chromadb_port)

    return services


def are_core_services_healthy(services: Dict[str, ServiceStatus]) -> bool:
    """Check if all CORE services are healthy."""
    return all(
        services.get(name, ServiceStatus(name=name, ok=False, status="MISSING")).ok
        for name in CORE_SERVICES
    )


def get_failed_services(services: Dict[str, ServiceStatus]) -> list:
    """Get list of failed CORE service names."""
    return [
        name for name in CORE_SERVICES
        if not services.get(name, ServiceStatus(name=name, ok=False, status="MISSING")).ok
    ]
