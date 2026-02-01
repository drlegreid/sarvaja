"""
Infrastructure API endpoints.

Per EPIC-7.1: Container logs accessible from dashboard.
Provides /api/infra/logs endpoint that reads container logs
via the Podman REST API unix socket.
"""

import http.client
import os
import socket
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/infra", tags=["infra"])

# Podman socket paths (checked in order)
_SOCKET_PATHS = [
    "/run/podman/podman.sock",       # Mounted in container
    f"/run/user/{os.getuid()}/podman/podman.sock",  # Host user socket
    "/tmp/podman.sock",              # Manual service start
]

# Container name mapping
CONTAINER_NAMES = {
    "dashboard": "platform_governance-dashboard-dev_1",
    "typedb": "platform_typedb_1",
    "chromadb": "platform_chromadb_1",
    "litellm": "platform_litellm_1",
    "ollama": "platform_ollama_1",
    "agents": "platform_agents_1",
}


def _find_socket() -> str | None:
    """Find available podman socket."""
    for path in _SOCKET_PATHS:
        if os.path.exists(path):
            return path
    return None


def _fetch_logs_socket(sock_path: str, container: str, tail: int) -> list[str]:
    """Fetch logs via podman REST API unix socket."""
    conn = http.client.HTTPConnection("localhost")
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect(sock_path)
    conn.sock = sock
    try:
        path = (
            f"/v4.0.0/containers/{container}/logs"
            f"?stdout=true&stderr=true&tail={tail}"
        )
        conn.request("GET", path)
        resp = conn.getresponse()
        if resp.status != 200:
            return [f"Error {resp.status} from podman API"]
        raw = resp.read()
        # Parse Docker/Podman log stream frames (8-byte header per frame)
        lines = []
        pos = 0
        while pos + 8 <= len(raw):
            size = int.from_bytes(raw[pos + 4:pos + 8], "big")
            if pos + 8 + size > len(raw):
                break
            chunk = raw[pos + 8:pos + 8 + size].decode(errors="replace")
            lines.append(chunk.rstrip("\n"))
            pos += 8 + size
        if not lines and raw:
            return raw.decode(errors="replace").strip().split("\n")
        return lines
    finally:
        conn.close()


@router.get("/logs")
def get_container_logs(
    container: str = Query("dashboard", description="Container short name"),
    tail: int = Query(50, ge=1, le=500, description="Number of lines"),
    level: str = Query("", description="Log level filter (ERROR, WARNING, INFO)"),
):
    """Fetch container logs via podman socket."""
    container_name = CONTAINER_NAMES.get(container, container)
    sock_path = _find_socket()

    if not sock_path:
        return {
            "lines": ["No podman socket available. Mount podman.sock into container."],
            "container": container,
            "source": "none",
        }

    try:
        lines = _fetch_logs_socket(sock_path, container_name, tail)
        if level:
            level_upper = level.upper()
            lines = [l for l in lines if level_upper in l.upper()]
        return {
            "lines": lines[-tail:],
            "container": container,
            "source": sock_path,
        }
    except Exception as e:
        return {
            "lines": [f"Error fetching logs: {e}"],
            "container": container,
            "source": sock_path,
        }


@router.get("/containers")
def list_containers():
    """List available container names."""
    return {"containers": list(CONTAINER_NAMES.keys())}
