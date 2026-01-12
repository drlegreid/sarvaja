"""
Level 2: Integration Tests - Require Podman services.

Run: python -m pytest .claude/hooks/tests/test_level2_integration.py -v

Prerequisites:
- Podman running (rootless)
- TypeDB container up (port 1729)
- ChromaDB container up (port 8001)

Platform: Linux (xubuntu) - migrated 2026-01-09
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).parent.parent
PROJECT_ROOT = HOOKS_DIR.parent.parent  # .claude/hooks -> project root
HEALTHCHECK_SCRIPT = HOOKS_DIR / "healthcheck.py"
ENTROPY_SCRIPT = HOOKS_DIR / "entropy_monitor.py"


def podman_available():
    """Check if Podman is running."""
    try:
        result = subprocess.run(
            ["podman", "info"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


@pytest.mark.skipif(not podman_available(), reason="Podman not available")
class TestHealthcheckIntegration:
    """Integration tests for healthcheck with actual services."""

    def test_healthcheck_checks_real_services(self):
        """Healthcheck validates actual Podman services."""
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(PROJECT_ROOT)
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]

        # Should report on service status (PODMAN, MCP, HEALTH, containers, etc.)
        assert any(kw in context for kw in [
            "PODMAN", "MCP", "HEALTH", "typedb", "chromadb", "containers"
        ]) or "podman" in context.lower()

    def test_healthcheck_creates_state_file(self):
        """Healthcheck creates state file with real data."""
        state_file = HOOKS_DIR / ".healthcheck_state.json"

        subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            timeout=15,
            cwd=str(PROJECT_ROOT)
        )

        assert state_file.exists()
        with open(state_file) as f:
            state = json.load(f)

        assert "master_hash" in state
        assert "components" in state
        assert len(state["master_hash"]) == 8

    def test_healthcheck_hash_stability(self):
        """Hash stays stable when services unchanged."""
        state_file = HOOKS_DIR / ".healthcheck_state.json"

        # Run twice
        subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            timeout=15,
            cwd=str(PROJECT_ROOT)
        )
        with open(state_file) as f:
            state1 = json.load(f)

        subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            timeout=15,
            cwd=str(PROJECT_ROOT)
        )
        with open(state_file) as f:
            state2 = json.load(f)

        # Hash should be same if services didn't change
        assert state1["master_hash"] == state2["master_hash"]


@pytest.mark.skipif(not podman_available(), reason="Podman not available")
class TestServiceChecker:
    """Integration tests for service checker."""

    def test_checker_detects_container_runtime(self):
        """ServiceChecker detects container runtime (podman or docker)."""
        sys.path.insert(0, str(HOOKS_DIR.parent))
        try:
            from hooks.checkers import ServiceChecker

            checker = ServiceChecker()
            services = checker.check_all()

            # Should detect either podman or docker (module may not be migrated yet)
            assert "podman" in services or "docker" in services
            runtime = "podman" if "podman" in services else "docker"
            # Runtime should be detected
            assert runtime in services
        except ImportError:
            pytest.skip("hooks.checkers not implemented")
        finally:
            sys.path.pop(0)

    def test_checker_detects_containers(self):
        """ServiceChecker detects running containers."""
        sys.path.insert(0, str(HOOKS_DIR.parent))
        try:
            from hooks.checkers import ServiceChecker

            checker = ServiceChecker()
            services = checker.check_all()

            # Should detect either podman or docker
            assert "podman" in services or "docker" in services
            # TypeDB and ChromaDB should be in the response
            assert "typedb" in services
            assert "chromadb" in services
        except ImportError:
            pytest.skip("hooks.checkers not implemented")
        finally:
            sys.path.pop(0)


class TestEntropyIntegration:
    """Integration tests for entropy monitor."""

    def test_entropy_state_persistence(self):
        """Entropy state persists across runs."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not implemented")

        state_file = HOOKS_DIR / ".entropy_state.json"

        # Reset
        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--reset"],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state1 = json.load(f)

        # Run normal (increments)
        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state2 = json.load(f)

        assert state2["tool_count"] == state1["tool_count"] + 1

    def test_entropy_tracks_session(self):
        """Entropy tracks session with hash and history."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not implemented")

        state_file = HOOKS_DIR / ".entropy_state.json"

        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--reset"],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state = json.load(f)

        assert "session_hash" in state
        assert len(state["session_hash"]) == 4
        assert "history" in state
        assert len(state["history"]) > 0
        assert state["history"][-1]["event"] == "SESSION_RESET"


class TestZombieProcessDetection:
    """Integration tests for zombie MCP process detection (Linux)."""

    def test_zombie_detection_memory_check(self):
        """Memory percentage check works on Linux."""
        result = subprocess.run(
            [sys.executable, "-c", """
import os

# Read memory from /proc/meminfo (Linux)
try:
    with open("/proc/meminfo") as f:
        meminfo = f.read()
    total = int([l for l in meminfo.split("\\n") if "MemTotal" in l][0].split()[1])
    avail = int([l for l in meminfo.split("\\n") if "MemAvailable" in l][0].split()[1])
    mem_pct = round((total - avail) / total * 100, 1)
    print(f"memory_pct={mem_pct}")
    print(f"valid={0 <= mem_pct <= 100}")
except Exception as e:
    print(f"error={e}")
    print("valid=False")
"""],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert "valid=True" in result.stdout

    def test_zombie_detection_pgrep(self):
        """pgrep script for governance process detection works."""
        result = subprocess.run(
            ["pgrep", "-a", "-f", "governance.mcp_server"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # pgrep returns 0 if found, 1 if not found - both are valid
        assert result.returncode in [0, 1]
        # Output format should be "PID command..."
        if result.stdout.strip():
            lines = result.stdout.strip().split("\n")
            for line in lines:
                parts = line.split(" ", 1)
                assert len(parts) >= 1
                assert parts[0].isdigit()  # First part is PID

    def test_expected_mcp_servers_in_healthcheck(self):
        """EXPECTED_MCP_SERVERS constant is defined in healthcheck."""
        content = open(HEALTHCHECK_SCRIPT).read()
        assert "EXPECTED_MCP_SERVERS" in content
        assert "governance.mcp_server_core" in content
        assert "governance.mcp_server_agents" in content
        assert "governance.mcp_server_sessions" in content
        assert "governance.mcp_server_tasks" in content

    def test_cleanup_zombie_pids_function_exists(self):
        """cleanup_zombie_pids function is defined in healthcheck."""
        content = open(HEALTHCHECK_SCRIPT).read()
        assert "def cleanup_zombie_pids" in content
        # Linux uses kill command, not PowerShell
        assert "kill" in content


@pytest.mark.skipif(not podman_available(), reason="Podman not available")
class TestStaleContainerRecovery:
    """Tests for stale container detection and reset (post-reboot recovery).

    Implementation is in hooks/recovery/containers.py (ContainerRecovery class).
    Healthcheck.py provides thin wrapper functions for backward compatibility.
    """

    # Path to the implementation module (containers.py)
    CONTAINERS_SCRIPT = HOOKS_DIR / "recovery" / "containers.py"

    def test_detect_stale_containers_function_exists(self):
        """detect_stale_containers function should exist in healthcheck (wrapper)."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("healthcheck", HEALTHCHECK_SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert hasattr(module, "detect_stale_containers"), "Missing detect_stale_containers function"
        assert callable(module.detect_stale_containers)

    def test_reset_containers_function_exists(self):
        """reset_containers function should exist in healthcheck (wrapper)."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("healthcheck", HEALTHCHECK_SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert hasattr(module, "reset_containers"), "Missing reset_containers function"
        assert callable(module.reset_containers)

    def test_attempt_recovery_detects_stale_scenario(self):
        """attempt_recovery should detect and handle stale container scenario."""
        import importlib.util
        import inspect

        spec = importlib.util.spec_from_file_location("healthcheck", HEALTHCHECK_SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        source = inspect.getsource(module.attempt_recovery)

        # Check docstring documents stale container scenario
        assert "stale" in source.lower(), "attempt_recovery should document stale scenario"
        assert "reset" in source.lower(), "attempt_recovery should mention reset for stale"

    def test_recovery_output_shows_reset_action(self):
        """When stale containers detected, output should show RESETTING action."""
        # Implementation is in containers.py (ContainerRecovery.attempt_recovery)
        with open(self.CONTAINERS_SCRIPT) as f:
            content = f.read()

        assert "RESETTING stale containers" in content, \
            "ContainerRecovery should show 'RESETTING stale containers' when stale detected"

    def test_stale_detection_checks_container_status(self):
        """detect_stale_containers should check for exited/dead/created states."""
        # Implementation is in containers.py (ContainerRecovery.detect_stale_containers)
        with open(self.CONTAINERS_SCRIPT) as f:
            content = f.read()

        # Should check for stale indicators
        assert '"exited"' in content or "'exited'" in content, \
            "Should detect exited containers"
        assert '"dead"' in content or "'dead'" in content, \
            "Should detect dead containers"
        assert "resolv.conf" in content.lower(), \
            "Should detect resolv.conf errors (common post-reboot issue)"

    def test_detect_stale_containers_returns_bool(self):
        """detect_stale_containers should return a boolean."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("healthcheck", HEALTHCHECK_SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result = module.detect_stale_containers()
        assert isinstance(result, bool), "detect_stale_containers should return bool"

    def test_container_recovery_class_exists(self):
        """ContainerRecovery class should exist with runtime auto-detection."""
        sys.path.insert(0, str(HOOKS_DIR.parent))
        try:
            from hooks.recovery.containers import ContainerRecovery

            # Should auto-detect runtime
            recovery = ContainerRecovery()
            assert recovery.runtime in ("podman", "docker"), \
                "ContainerRecovery should auto-detect runtime"
        finally:
            sys.path.pop(0)

    def test_backward_compat_aliases(self):
        """PodmanRecovery and DockerRecovery aliases should exist."""
        sys.path.insert(0, str(HOOKS_DIR.parent))
        try:
            from hooks.recovery.containers import (
                ContainerRecovery, PodmanRecovery, DockerRecovery
            )

            # Should be aliases to ContainerRecovery
            assert PodmanRecovery is ContainerRecovery
            assert DockerRecovery is ContainerRecovery
        finally:
            sys.path.pop(0)
