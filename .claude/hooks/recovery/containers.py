"""
Container recovery for Claude Code hooks.

Per RULE-021: Auto-recovery of containers (runtime-agnostic).
Per user request: Audit logging for transparency, resiliency, debugability.

Platform: Linux (xubuntu) with Podman - migrated 2026-01-11
Note: Docker support stubbed for future implementation.
"""

import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..core.base import HookConfig, HookResult, DEFAULT_CONFIG


def _get_audit_logger():
    """Get audit logger (late import to avoid circular dependency)."""
    try:
        from .audit import get_audit_log
        return get_audit_log()
    except Exception:
        return None


class ContainerRecovery:
    """
    Handles auto-recovery of containers (runtime-agnostic).

    Supports:
    - Starting container runtime socket (non-blocking)
    - Starting containers via compose
    - Resetting stale containers (post-reboot)
    - Recovery cooldown to prevent spam

    Runtime: Auto-detected (podman preferred, docker fallback)
    Platform: Linux (xubuntu) with Podman - migrated 2026-01-09
    """

    def __init__(self, config: Optional[HookConfig] = None, runtime: str = "auto"):
        """
        Initialize container recovery.

        Args:
            config: Hook configuration (uses DEFAULT_CONFIG if None)
            runtime: Container runtime ("auto", "podman", "docker")
        """
        self.config = config or DEFAULT_CONFIG
        self.runtime = self._detect_runtime() if runtime == "auto" else runtime

    def _detect_runtime(self) -> str:
        """
        Detect available container runtime.

        Returns:
            "podman" or "docker" based on availability
        """
        # Check podman first (preferred on Linux)
        try:
            result = subprocess.run(
                ["podman", "--version"],
                capture_output=True, timeout=2
            )
            if result.returncode == 0:
                return "podman"
        except Exception:
            pass

        # Fallback to docker
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True, timeout=2
            )
            if result.returncode == 0:
                return "docker"
        except Exception:
            pass

        # Default to podman even if not found (will fail gracefully)
        return "podman"

    def _get_compose_cmd(self) -> List[str]:
        """Get compose command for current runtime."""
        if self.runtime == "podman":
            return ["podman", "compose", "--profile", "cpu"]
        else:
            # TODO: Docker implementation
            # Docker Compose v2: docker compose (plugin)
            # Docker Compose v1: docker-compose (standalone)
            return ["docker", "compose"]

    def start_socket(self) -> bool:
        """
        Start container runtime socket service (non-blocking).

        Returns:
            True if start command succeeded
        """
        if self.runtime == "podman":
            return self._start_podman_socket()
        else:
            # TODO: Docker implementation
            # Docker Desktop: Start via GUI or CLI
            # Docker Engine: systemctl start docker
            return self._start_docker_socket()

    def _start_podman_socket(self) -> bool:
        """Start Podman socket service (Linux only)."""
        try:
            subprocess.Popen(
                ["systemctl", "--user", "start", "podman.socket"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception:
            pass
        return False

    def _start_docker_socket(self) -> bool:
        """
        Start Docker socket service.

        TODO: Implement Docker-specific startup:
        - Docker Desktop (macOS/Windows): open -a Docker or Start-Process
        - Docker Engine (Linux): systemctl start docker
        """
        try:
            # Try systemd first (Docker Engine on Linux)
            subprocess.Popen(
                ["systemctl", "start", "docker"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception:
            pass
        return False

    # Backward compatibility aliases
    def start_podman_socket(self) -> bool:
        """Backward-compatible alias for start_socket (podman)."""
        return self._start_podman_socket()

    def start_docker_desktop(self) -> bool:
        """Backward-compatible alias for start_socket (docker)."""
        return self._start_docker_socket()

    def _try_start_existing(self, container_names: List[str]) -> bool:
        """
        Try to start existing stopped containers (fast resume).

        Per GAP-HOOK-RECOVERY-001: Try 'podman start' before 'podman compose up'.

        Args:
            container_names: Container names to start

        Returns:
            True if at least one container was started successfully
        """
        any_started = False
        for name in container_names:
            try:
                # Try direct start (resume existing)
                result = subprocess.run(
                    [self.runtime, "start", name],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    any_started = True
            except Exception:
                pass
        return any_started

    def start_containers(self, services: Optional[List[str]] = None) -> bool:
        """
        Start containers - tries resume first, then compose.

        Per GAP-HOOK-RECOVERY-001:
        1. Try 'podman start <container>' (resume existing - fast)
        2. If fails, use 'podman compose up' (create new - slower)

        Args:
            services: List of services to start (defaults to core services)

        Returns:
            True if start command succeeded
        """
        services = services or ["typedb", "chromadb"]

        # Step 1: Try to resume existing containers (fast)
        if self._try_start_existing(services):
            return True

        # Step 2: Fall back to compose (create new)
        try:
            cmd = self._get_compose_cmd() + ["up", "-d"] + services

            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(self.config.project_root)
            )
            return True
        except Exception:
            pass
        return False

    def reset_containers(self) -> bool:
        """
        Reset containers after system reboot (non-blocking).

        Post-reboot, containers have stale state (resolv.conf errors).
        This does a full down + up cycle to recreate them cleanly.

        Returns:
            True if reset command succeeded
        """
        try:
            if self.runtime == "podman":
                cmd = (
                    "podman compose --profile cpu down 2>/dev/null; "
                    "podman compose --profile cpu up -d typedb chromadb"
                )
            else:
                # TODO: Docker implementation
                cmd = (
                    "docker compose down 2>/dev/null; "
                    "docker compose up -d typedb chromadb"
                )

            subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(self.config.project_root)
            )
            return True
        except Exception:
            pass
        return False

    def detect_stale_containers(self) -> bool:
        """
        Detect if containers have stale state (post-reboot scenario).

        Returns:
            True if containers appear to have stale state
        """
        try:
            cmd = self._get_compose_cmd() + ["ps", "-a"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                cwd=str(self.config.project_root)
            )
            output = result.stdout.lower()
            # Stale indicators: exited containers or error states
            if "exited" in output or "dead" in output or "created" in output:
                return True
            # Also check stderr for common post-reboot errors
            if "no such file" in result.stderr.lower() or "resolv.conf" in result.stderr.lower():
                return True
        except Exception:
            pass
        return False

    def attempt_recovery(
        self,
        services: Dict[str, Dict[str, Any]],
        prev_state: Dict[str, Any]
    ) -> HookResult:
        """
        Attempt auto-recovery based on service state.

        Logs all recovery attempts to audit log for transparency.

        Args:
            services: Current service status
            prev_state: Previous healthcheck state

        Returns:
            HookResult with recovery actions taken
        """
        actions = []
        audit = _get_audit_logger()
        start_time = time.time()
        last_recovery = prev_state.get("last_recovery", 0)

        # Check cooldown
        if time.time() - last_recovery < self.config.recovery_cooldown:
            return HookResult.ok(
                "Recovery in cooldown period",
                cooldown_remaining=int(
                    self.config.recovery_cooldown - (time.time() - last_recovery)
                )
            )

        # Use runtime-agnostic key for checking runtime health
        runtime_key = self.runtime  # "podman" or "docker"
        runtime_ok = services.get(runtime_key, {}).get("ok", False)

        # Scenario 1: Runtime not running
        if not runtime_ok:
            success = self.start_socket()
            action = f"start_{runtime_key}_socket"
            if success:
                actions.append(f"STARTING {runtime_key.title()} socket")
            # Log to audit
            if audit:
                audit.log_attempt(
                    action=action,
                    success=success,
                    services=[runtime_key],
                    error=None if success else f"Failed to start {runtime_key.title()} socket",
                    resolution_hint=self._get_socket_hint(),
                    duration_ms=int((time.time() - start_time) * 1000)
                )
            return HookResult(
                success=True,
                status="RECOVERING",
                message=f"{runtime_key.title()} socket starting",
                recovery_actions=actions,
                resolution_path="Wait 30-60s then run /health to verify"
            )

        # Scenario 2: Runtime running but core containers down
        core_down = [
            s for s in self.config.core_services
            if s not in ("podman", "docker") and not services.get(s, {}).get("ok", False)
        ]

        if core_down:
            # Check for stale containers (post-reboot scenario)
            is_stale = self.detect_stale_containers()
            if is_stale:
                success = self.reset_containers()
                action = "reset_containers"
                if success:
                    actions.append(f"RESETTING stale containers ({', '.join(core_down)})")
            else:
                success = self.start_containers(core_down)
                action = "start_containers"
                if success:
                    actions.append(f"STARTING containers ({', '.join(core_down)})")

            # Log to audit
            if audit:
                compose_cmd = " ".join(self._get_compose_cmd())
                audit.log_attempt(
                    action=action,
                    success=success,
                    services=core_down,
                    error=None if success else f"Failed to {action}",
                    resolution_hint=f"Run: {compose_cmd} up -d {' '.join(core_down)}",
                    duration_ms=int((time.time() - start_time) * 1000)
                )
            return HookResult(
                success=True,
                status="RECOVERING",
                message=f"Starting containers: {', '.join(core_down)}",
                recovery_actions=actions,
                resolution_path="Wait 30-60s then run /health to verify"
            )

        return HookResult.ok("No recovery needed")

    def _get_socket_hint(self) -> str:
        """Get resolution hint for socket startup."""
        if self.runtime == "podman":
            return "Run: systemctl --user start podman.socket"
        else:
            # TODO: Docker-specific hints
            return "Run: systemctl start docker  # or start Docker Desktop"

    def get_manual_recovery_command(self, failed_services: List[str]) -> str:
        """
        Get manual recovery command for failed services.

        Args:
            failed_services: List of failed service names

        Returns:
            Shell command string
        """
        compose_cmd = " ".join(self._get_compose_cmd())
        if self.runtime in failed_services:
            if self.runtime == "podman":
                return f"systemctl --user start podman.socket && {compose_cmd} up -d"
            else:
                return f"systemctl start docker && {compose_cmd} up -d"
        else:
            return f"{compose_cmd} up -d"

    def get_resolution_path(self, services: Dict[str, Dict[str, Any]]) -> Optional[str]:
        """
        Get resolution path based on current service state.

        Args:
            services: Current service status

        Returns:
            Resolution instruction string or None if healthy
        """
        runtime_key = self.runtime
        runtime_ok = services.get(runtime_key, {}).get("ok", False)
        compose_cmd = " ".join(self._get_compose_cmd())

        if not runtime_ok:
            if self.runtime == "podman":
                return f"Start Podman: systemctl --user start podman.socket && {compose_cmd} up -d"
            else:
                return f"Start Docker: systemctl start docker && {compose_cmd} up -d"

        failed = [
            s for s in self.config.core_services
            if s not in ("podman", "docker") and not services.get(s, {}).get("ok", False)
        ]

        if failed:
            return f"Run: {compose_cmd} up -d {' '.join(failed)}"

        return None


# Backward compatibility aliases
PodmanRecovery = ContainerRecovery
DockerRecovery = ContainerRecovery
