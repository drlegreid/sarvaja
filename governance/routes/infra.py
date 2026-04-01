"""
Infrastructure API endpoints.

Per EPIC-7.1: Container logs accessible from dashboard.
Provides /api/infra/logs endpoint that reads container logs
via the Podman REST API unix socket, with subprocess fallback.
"""

import http.client
import logging
import os
import socket
import subprocess
from fastapi import APIRouter, Query
from fastapi.responses import Response
try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    _HAS_PROMETHEUS = True
except ImportError:
    _HAS_PROMETHEUS = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/infra", tags=["infra"])

# Separate router for /metrics (no prefix — Prometheus convention)
metrics_prom_router = APIRouter(tags=["metrics"])

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
    """Find available podman socket (must be a real socket, not a directory)."""
    for path in _SOCKET_PATHS:
        if os.path.exists(path) and not os.path.isdir(path):
            return path
    return None


def _fetch_logs_socket(sock_path: str, container: str, tail: int) -> list[str]:
    """Fetch logs via podman REST API unix socket."""
    conn = http.client.HTTPConnection("localhost")
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    # BUG-INFRA-SOCKET-001: Use try/finally to ensure socket cleanup
    try:
        sock.settimeout(5)
        sock.connect(sock_path)
        conn.sock = sock
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
        sock.close()
        conn.close()


def _fetch_logs_subprocess(container: str, tail: int) -> list[str]:
    """Fallback: fetch logs via podman CLI subprocess."""
    try:
        result = subprocess.run(
            ["podman", "logs", "--tail", str(tail), container],
            capture_output=True, text=True, timeout=10,
        )
        lines = []
        if result.stdout:
            lines.extend(result.stdout.strip().split("\n"))
        if result.stderr:
            lines.extend(result.stderr.strip().split("\n"))
        return lines if lines else ["No log output from container"]
    except FileNotFoundError:
        return []
    except subprocess.TimeoutExpired:
        return ["Timeout fetching logs via CLI"]
    except Exception as e:
        return [f"CLI fallback error: {e}"]


def _fetch_own_process_logs(tail: int) -> list[str]:
    """Read own container process logs from /proc/1/fd/1 (stdout of PID 1)."""
    lines = []
    # Try reading recent Python logging output
    try:
        result = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True, timeout=5
        )
        lines.append("=== Container Processes ===")
        for line in result.stdout.strip().split("\n"):
            if "python" in line.lower() or "PID" in line:
                lines.append(line)
    except Exception:
        pass
    if not lines:
        lines = ["Running inside container - use host podman socket for full logs"]
    return lines[-tail:]


@router.get("/logs")
def get_container_logs(
    container: str = Query("dashboard", description="Container short name"),
    tail: int = Query(50, ge=1, le=500, description="Number of lines"),
    level: str = Query("", description="Log level filter (ERROR, WARNING, INFO)"),
):
    """Fetch container logs via podman socket, CLI fallback, or process info."""
    # BUG-ROUTE-LOGIC-010: Strict whitelist — reject unmapped container names
    if container not in CONTAINER_NAMES:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unknown container: {container}. Valid: {list(CONTAINER_NAMES.keys())}")
    container_name = CONTAINER_NAMES[container]

    # Strategy 1: Podman REST API socket
    sock_path = _find_socket()
    if sock_path:
        try:
            lines = _fetch_logs_socket(sock_path, container_name, tail)
            if level:
                level_upper = level.upper()
                lines = [ln for ln in lines if level_upper in ln.upper()]
            return {"lines": lines[-tail:], "container": container, "source": sock_path}
        except Exception as e:
            # BUG-470-INF-001: Sanitize logger message + add exc_info for stack trace preservation
            logger.warning(f"Socket log fetch failed: {type(e).__name__}", exc_info=True)

    # Strategy 2: podman CLI subprocess
    cli_lines = _fetch_logs_subprocess(container_name, tail)
    if cli_lines and not cli_lines[0].startswith(("CLI fallback error", "Timeout")):
        if level:
            level_upper = level.upper()
            cli_lines = [ln for ln in cli_lines if level_upper in ln.upper()]
        return {"lines": cli_lines[-tail:], "container": container, "source": "cli"}

    # Strategy 3: For own container, show process info
    own_lines = _fetch_own_process_logs(tail)
    return {"lines": own_lines, "container": container, "source": "process-info"}


@router.get("/containers")
def list_containers():
    """List available container names."""
    return {"containers": list(CONTAINER_NAMES.keys())}


# =============================================================================
# PROMETHEUS METRICS ENDPOINT (EPIC-PERF-TELEM-V1 Phase 9)
# =============================================================================

@metrics_prom_router.get("/metrics")
def prometheus_metrics():
    """Expose Prometheus metrics in text exposition format."""
    if not _HAS_PROMETHEUS:
        return Response(content="# prometheus_client not installed\n", media_type="text/plain")
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
