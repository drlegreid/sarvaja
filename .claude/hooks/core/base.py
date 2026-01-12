"""
Base classes and configuration for Claude Code hooks.

Per EPIC-006: Provides reusable foundation for healthcheck and entropy monitoring.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class HealthLevel(Enum):
    """Health/entropy level indicators."""
    OK = "OK"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    DOWN = "DOWN"
    UNKNOWN = "UNKNOWN"


class ServiceStatus(Enum):
    """Service status indicators."""
    OK = "OK"
    OFF = "OFF"
    DOWN = "DOWN"
    STARTING = "STARTING"  # Container up but port not ready (healthcheck pending)
    PODMAN_DOWN = "PODMAN_DOWN"
    CONTAINER_UP = "CONTAINER_UP"
    UNKNOWN = "UNKNOWN"


@dataclass
class HookConfig:
    """Configuration for hook execution."""
    # Timeouts (seconds)
    global_timeout: float = 15.0  # Max seconds for entire script (podman compose needs more)
    subprocess_timeout: float = 2.0  # Max seconds per subprocess call
    socket_timeout: float = 0.5  # Max seconds per socket check

    # Retry settings
    retry_ceiling_seconds: int = 30  # Stop detailed checks after unchanged duration
    recovery_cooldown: int = 60  # Seconds between recovery attempts
    stale_process_hours: int = 2  # Python processes older than this are stale

    # Paths
    hooks_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent.parent)

    # Core services that must be running
    core_services: List[str] = field(default_factory=lambda: ["podman", "typedb", "chromadb"])

    # Expected MCP servers (should have exactly 1 of each)
    expected_mcp_servers: List[str] = field(default_factory=lambda: [
        "governance.mcp_server_core",
        "governance.mcp_server_agents",
        "governance.mcp_server_sessions",
        "governance.mcp_server_tasks",
        "claude_mem.mcp_server",  # RULE-024: AMNESIA recovery
    ])

    # Service ports
    service_ports: Dict[str, int] = field(default_factory=lambda: {
        "typedb": 1729,
        "chromadb": 8001,
        "litellm": 4000,
        "ollama": 11434
    })

    # Container runtime (Linux: podman, Windows: docker)
    # Podman socket path for Linux
    podman_socket_path: Path = field(
        default_factory=lambda: Path("/run/user/1000/podman/podman.sock")
    )

    @property
    def state_file(self) -> Path:
        """Path to healthcheck state file."""
        return self.hooks_dir / ".healthcheck_state.json"

    @property
    def entropy_file(self) -> Path:
        """Path to entropy state file."""
        return self.hooks_dir / ".entropy_state.json"

    @property
    def deploy_script(self) -> Path:
        """Path to deploy.ps1 script."""
        return self.project_root / "deploy.ps1"


@dataclass
class HookResult:
    """Result from a hook check operation."""
    success: bool
    status: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    recovery_actions: List[str] = field(default_factory=list)
    resolution_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "recovery_actions": self.recovery_actions,
            "resolution_path": self.resolution_path
        }

    @classmethod
    def ok(cls, message: str = "OK", **details) -> "HookResult":
        """Create a successful result."""
        return cls(
            success=True,
            status="OK",
            message=message,
            details=details
        )

    @classmethod
    def error(cls, message: str, resolution_path: Optional[str] = None, **details) -> "HookResult":
        """Create an error result with optional resolution path."""
        return cls(
            success=False,
            status="ERROR",
            message=message,
            details=details,
            resolution_path=resolution_path
        )

    @classmethod
    def warning(cls, message: str, resolution_path: Optional[str] = None, **details) -> "HookResult":
        """Create a warning result with optional resolution path."""
        return cls(
            success=True,  # Warnings don't fail
            status="WARNING",
            message=message,
            details=details,
            resolution_path=resolution_path
        )


@dataclass
class ServiceInfo:
    """Information about a service status."""
    name: str
    status: ServiceStatus
    ok: bool
    port: Optional[int] = None
    optional: bool = False
    hash: str = "????"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "ok": self.ok,
            "port": self.port,
            "optional": self.optional,
            "hash": self.hash
        }


# Default configuration singleton
DEFAULT_CONFIG = HookConfig()
