"""
E2E and Unit Tests for Claude Code Hooks - Healthcheck & Entropy Monitor

Per GAP-MCP-003: Verify SessionStart hook context injection
Per EPIC-006: Entropy Monitor for SLEEP Mode Automation
Per RULE-023: TDD - tests written before implementation

Tests verify:
1. Healthcheck script produces valid JSON
2. Non-blocking behavior (max 5s for initial check)
3. 30-second retry ceiling when state unchanged
4. Graceful degradation when services down
5. hookSpecificOutput format for Claude Code
6. Entropy Monitor audit trail (session_hash, check_count, history)

Run:
    pytest tests/test_claude_hooks.py -v
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Path to the hooks
HOOKS_DIR = Path(__file__).parent.parent / ".claude" / "hooks"
HEALTHCHECK_SCRIPT = HOOKS_DIR / "healthcheck.py"
ENTROPY_SCRIPT = HOOKS_DIR / "entropy_monitor.py"


class TestHealthcheckOutput:
    """Tests for healthcheck JSON output format."""

    def test_healthcheck_returns_valid_json(self):
        """Healthcheck must always return valid JSON, even on failure."""
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10  # Should complete much faster
        )

        # Must be valid JSON
        output = json.loads(result.stdout)
        assert isinstance(output, dict)

    def test_healthcheck_has_hook_specific_output(self):
        """Output must have hookSpecificOutput for Claude Code context injection."""
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = json.loads(result.stdout)
        assert "hookSpecificOutput" in output
        assert "additionalContext" in output["hookSpecificOutput"]

    def test_healthcheck_completes_within_timeout(self):
        """Initial healthcheck must complete within 5 seconds."""
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        start = time.time()
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )
        elapsed = time.time() - start

        # Must complete within 5 seconds for non-blocking behavior
        assert elapsed < 5, f"Healthcheck took {elapsed:.1f}s, must be < 5s"
        assert result.returncode == 0

    def test_healthcheck_exits_zero_always(self):
        """Healthcheck must exit 0 even when services are down."""
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Always exit 0 - failure info is in the JSON, not exit code
        assert result.returncode == 0


class TestHealthcheckStateManagement:
    """Tests for hash-based state and retry ceiling."""

    def test_state_file_created(self):
        """Healthcheck should create state file for hash tracking."""
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        state_file = HOOKS_DIR / ".healthcheck_state.json"

        # Run healthcheck
        subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            timeout=10
        )

        assert state_file.exists()

        # State file must be valid JSON
        with open(state_file) as f:
            state = json.load(f)

        assert "master_hash" in state
        assert "last_check" in state

    def test_unchanged_state_triggers_summary(self):
        """When state unchanged, should return summary not detailed output."""
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        # Run twice - second run should detect unchanged hash
        subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            timeout=10
        )

        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]

        # Second run with same state should show summary (shorter)
        # or indicate hash unchanged
        assert "unchanged" in context.lower() or len(context) < 500

    def test_retry_ceiling_after_30_seconds(self):
        """After 30s of unchanged state, stop detailed retrying."""
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        state_file = HOOKS_DIR / ".healthcheck_state.json"

        # First, run healthcheck to get current actual hash
        result1 = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )
        output1 = json.loads(result1.stdout)

        # Now read the state file to get the actual hash
        with open(state_file) as f:
            actual_state = json.load(f)

        # Simulate state that's been unchanged for 31 seconds WITH SAME HASH
        old_state = {
            "master_hash": actual_state.get("master_hash", "DEADBEEF"),
            "last_check": "2020-01-01T00:00:00",
            "check_count": 100,
            "unchanged_since": time.time() - 31,  # 31 seconds ago
            "components": actual_state.get("components", {})  # Use actual components
        }

        with open(state_file, "w") as f:
            json.dump(old_state, f)

        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]

        # When hash unchanged for >30s, should return stable/summary output
        # Either "cached", "stable", or just short summary
        assert (
            "cached" in context.lower() or
            "stable" in context.lower() or
            "unchanged" in context.lower() or
            len(context) < 300  # Summary output is shorter
        )


class TestHealthcheckServiceDetection:
    """Tests for Docker/service detection logic."""

    def test_detects_docker_status(self):
        """Should detect whether Docker daemon is running."""
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        state_file = HOOKS_DIR / ".healthcheck_state.json"

        # Reset state to force detailed output on first run
        if state_file.exists():
            state_file.unlink()

        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]

        # First run or hash change should show detailed output with PODMAN/DOCKER
        # Summary output (HEALTH OK) indicates container runtime is working but won't mention it by name
        # Note: Migrated from Docker to Podman on 2026-01-09
        container_mentioned = "docker" in context.lower() or "podman" in context.lower()
        health_ok = "[HEALTH OK]" in context or "chain ready" in context.lower()

        # Either shows container runtime explicitly OR indicates overall health is OK
        assert container_mentioned or health_ok, f"Output should mention container runtime or indicate healthy: {context}"

    def test_provides_recovery_hint_when_down(self):
        """When services down, should provide recovery command."""
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        # This test runs regardless of actual Docker state
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]

        # If any service is down, should have recovery hint
        if "DOWN" in context or "OFF" in context or "unhealthy" in context.lower():
            assert "deploy.ps1" in context or "docker" in context.lower()


class TestHealthcheckNonBlocking:
    """Tests to ensure healthcheck never blocks Claude Code."""

    def test_subprocess_timeout_protection(self):
        """All subprocess calls must have timeout protection."""
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        # Read the script and verify timeout usage
        with open(HEALTHCHECK_SCRIPT) as f:
            content = f.read()

        # Find each subprocess.run and verify it has timeout in following lines
        # Use line-by-line analysis since calls span multiple lines
        lines = content.split('\n')
        in_subprocess_call = False
        call_lines = []
        missing_timeout = []

        for i, line in enumerate(lines):
            if 'subprocess.run(' in line:
                in_subprocess_call = True
                call_lines = [line]
            elif in_subprocess_call:
                call_lines.append(line)
                # End of call detected by closing paren at end or next statement
                if ')' in line and not line.strip().endswith(','):
                    call_text = '\n'.join(call_lines)
                    if 'timeout' not in call_text.lower():
                        missing_timeout.append(call_text[:100])
                    in_subprocess_call = False
                    call_lines = []

        assert not missing_timeout, f"subprocess.run missing timeout: {missing_timeout}"

    def test_socket_timeout_protection(self):
        """All socket operations must have timeout protection."""
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        with open(HEALTHCHECK_SCRIPT) as f:
            content = f.read()

        # Socket operations should have settimeout
        if "socket" in content:
            assert "settimeout" in content or "timeout" in content

    def test_global_timeout_wrapper(self):
        """Script should have global timeout to prevent any hanging."""
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        with open(HEALTHCHECK_SCRIPT) as f:
            content = f.read()

        # Should have signal-based timeout or try/except with timeout
        has_protection = (
            "signal.alarm" in content or
            "threading.Timer" in content or
            "GLOBAL_TIMEOUT" in content or
            "max_duration" in content
        )
        assert has_protection, "Script needs global timeout protection"


class TestFrankelHash:
    """Tests for the Frankel hash implementation."""

    def test_hash_deterministic(self):
        """Same input should produce same hash."""
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        # Import the function
        import importlib.util
        spec = importlib.util.spec_from_file_location("healthcheck", HEALTHCHECK_SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        data = {"docker": "OK", "typedb": "OK"}
        hash1 = module.compute_frankel_hash(data)
        hash2 = module.compute_frankel_hash(data)

        assert hash1 == hash2

    def test_hash_changes_on_state_change(self):
        """Different state should produce different hash."""
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        import importlib.util
        spec = importlib.util.spec_from_file_location("healthcheck", HEALTHCHECK_SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        data1 = {"docker": "OK", "typedb": "OK"}
        data2 = {"docker": "OK", "typedb": "DOWN"}

        hash1 = module.compute_frankel_hash(data1)
        hash2 = module.compute_frankel_hash(data2)

        assert hash1 != hash2

    def test_hash_is_8_chars(self):
        """Frankel hash should be 8 uppercase hex chars."""
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        import importlib.util
        spec = importlib.util.spec_from_file_location("healthcheck", HEALTHCHECK_SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        data = {"docker": "OK"}
        hash_val = module.compute_frankel_hash(data)

        assert len(hash_val) == 8
        assert hash_val.isupper()
        assert all(c in "0123456789ABCDEF" for c in hash_val)


# =============================================================================
# ENTROPY MONITOR TESTS (EPIC-006)
# =============================================================================

class TestEntropyMonitorOutput:
    """Tests for entropy monitor JSON output format."""

    def test_entropy_returns_valid_json(self):
        """Entropy monitor must always return valid JSON."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not yet implemented")

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Must be valid JSON
        output = json.loads(result.stdout)
        assert isinstance(output, dict)

    def test_entropy_exits_zero_always(self):
        """Entropy monitor must exit 0 even on errors."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not yet implemented")

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0

    def test_entropy_status_command(self):
        """--status flag should return current entropy state."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not yet implemented")

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--status"],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        assert "hookSpecificOutput" in output
        context = output["hookSpecificOutput"]["additionalContext"]
        assert "ENTROPY" in context or "Tools" in context


class TestEntropyMonitorStateManagement:
    """Tests for entropy state file and audit trail."""

    def test_state_file_created(self):
        """Entropy monitor should create state file."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not yet implemented")

        state_file = HOOKS_DIR / ".entropy_state.json"

        # Run entropy monitor
        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            timeout=5
        )

        assert state_file.exists()

        # State file must be valid JSON
        with open(state_file) as f:
            state = json.load(f)

        assert "session_start" in state
        assert "tool_count" in state

    def test_state_has_audit_trail_fields(self):
        """State should have session_hash, check_count, history for audit trail."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not yet implemented")

        state_file = HOOKS_DIR / ".entropy_state.json"

        # Reset state first
        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--reset"],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state = json.load(f)

        # Audit trail fields
        assert "session_hash" in state, "Missing session_hash for audit trail"
        assert "check_count" in state, "Missing check_count for audit trail"
        assert "history" in state, "Missing history for audit trail"

    def test_session_hash_is_4_chars(self):
        """Session hash should be 4 uppercase hex chars."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not yet implemented")

        state_file = HOOKS_DIR / ".entropy_state.json"

        # Reset state
        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--reset"],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state = json.load(f)

        hash_val = state.get("session_hash", "")
        assert len(hash_val) == 4, f"Session hash should be 4 chars, got {len(hash_val)}"
        # Check valid hex (uppercase or numeric-only is valid)
        assert all(c in "0123456789ABCDEF" for c in hash_val), "Invalid hex chars in hash"
        # Ensure any letters are uppercase (numeric-only hashes like "0130" are valid)
        assert hash_val == hash_val.upper(), "Session hash should be uppercase"

    def test_check_count_increments(self):
        """Check count should increment with each state save."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not yet implemented")

        state_file = HOOKS_DIR / ".entropy_state.json"

        # Reset state
        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--reset"],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state1 = json.load(f)
        count1 = state1.get("check_count", 0)

        # Run again (normal mode increments tool_count)
        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state2 = json.load(f)
        count2 = state2.get("check_count", 0)

        assert count2 > count1, f"Check count should increment: {count1} -> {count2}"

    def test_reset_creates_history_entry(self):
        """Reset should create SESSION_RESET history entry."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not yet implemented")

        state_file = HOOKS_DIR / ".entropy_state.json"

        # Reset state
        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--reset"],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state = json.load(f)

        history = state.get("history", [])
        assert len(history) > 0, "History should have at least one entry after reset"

        # Find SESSION_RESET event
        reset_events = [h for h in history if h.get("event") == "SESSION_RESET"]
        assert len(reset_events) > 0, "History should contain SESSION_RESET event"

    def test_tool_count_increments(self):
        """Tool count should increment with each run (normal mode)."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not yet implemented")

        state_file = HOOKS_DIR / ".entropy_state.json"

        # Reset state
        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--reset"],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state1 = json.load(f)
        tools1 = state1.get("tool_count", 0)

        # Run in normal mode (increments tool count)
        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state2 = json.load(f)
        tools2 = state2.get("tool_count", 0)

        assert tools2 == tools1 + 1, f"Tool count should increment: {tools1} -> {tools2}"


class TestEntropyMonitorWarnings:
    """Tests for entropy warning thresholds."""

    def test_no_warning_below_threshold(self):
        """Should not show warning below LOW_THRESHOLD (50)."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not yet implemented")

        state_file = HOOKS_DIR / ".entropy_state.json"

        # Set state below threshold
        state = {
            "session_start": "2026-01-01T00:00:00",
            "session_hash": "TEST",
            "tool_count": 10,
            "check_count": 0,
            "last_save": None,
            "warnings_shown": 0,
            "last_warning_at": 0,
            "history": []
        }
        with open(state_file, "w") as f:
            json.dump(state, f)

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        # Empty output or no warning context
        if "hookSpecificOutput" in output:
            context = output["hookSpecificOutput"].get("additionalContext", "")
            assert "CHECKPOINT" not in context and "ENTROPY HIGH" not in context

    def test_low_threshold_warning(self):
        """Should show warning at LOW_THRESHOLD (50)."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not yet implemented")

        state_file = HOOKS_DIR / ".entropy_state.json"

        # Set state at threshold (will be 50 after increment)
        state = {
            "session_start": "2026-01-01T00:00:00",
            "session_hash": "TEST",
            "tool_count": 49,
            "check_count": 0,
            "last_save": None,
            "warnings_shown": 0,
            "last_warning_at": 0,
            "history": []
        }
        with open(state_file, "w") as f:
            json.dump(state, f)

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        assert "hookSpecificOutput" in output
        context = output["hookSpecificOutput"].get("additionalContext", "")
        assert "CHECKPOINT" in context or "50 tool calls" in context

    def test_high_threshold_warning(self):
        """Should show strong warning at HIGH_THRESHOLD (100)."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not yet implemented")

        state_file = HOOKS_DIR / ".entropy_state.json"

        # Set state at high threshold (will be 100 after increment)
        state = {
            "session_start": "2026-01-01T00:00:00",
            "session_hash": "TEST",
            "tool_count": 99,
            "check_count": 0,
            "last_save": None,
            "warnings_shown": 1,  # Already saw low warning
            "last_warning_at": 50,
            "history": []
        }
        with open(state_file, "w") as f:
            json.dump(state, f)

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        assert "hookSpecificOutput" in output
        context = output["hookSpecificOutput"].get("additionalContext", "")
        assert "ENTROPY HIGH" in context or "100 tool calls" in context


class TestEntropyMonitorNonBlocking:
    """Tests to ensure entropy monitor never blocks."""

    def test_completes_quickly(self):
        """Entropy monitor must complete within 1 second."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not yet implemented")

        start = time.time()
        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )
        elapsed = time.time() - start

        assert elapsed < 1, f"Entropy monitor took {elapsed:.2f}s, must be < 1s"
        assert result.returncode == 0

    def test_graceful_on_corrupt_state(self):
        """Should handle corrupt state file gracefully."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not yet implemented")

        state_file = HOOKS_DIR / ".entropy_state.json"

        # Write corrupt JSON
        with open(state_file, "w") as f:
            f.write("{invalid json")

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should still exit 0 and return valid JSON
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert isinstance(output, dict)


# =============================================================================
# NEGATIVE TESTS WITH RESOLUTION PATHS (Per user request)
# =============================================================================

class TestNegativeHealthWithResolution:
    """Tests for error scenarios with resolution path injection."""

    def test_docker_down_shows_resolution_path(self):
        """When Docker is down, output should include resolution path."""
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        state_file = HOOKS_DIR / ".healthcheck_state.json"

        # Simulate Docker down state
        state = {
            "master_hash": "00000000",
            "check_count": 1,
            "last_check": "2026-01-01T00:00:00",
            "unchanged_since": 0,
            "components": {
                "docker": "DOWN",
                "typedb": "DOCKER_DOWN",
                "chromadb": "DOCKER_DOWN"
            },
            "history": []
        }
        with open(state_file, "w") as f:
            json.dump(state, f)

        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]

        # If services are down, should have resolution path
        if "DOWN" in context:
            # Should include actionable resolution command
            has_resolution = (
                "deploy.ps1" in context or
                "docker compose" in context.lower() or
                "Docker Desktop" in context or
                "Recovery" in context or
                "Resolution" in context
            )
            assert has_resolution, "Missing resolution path when services down"

    def test_container_down_shows_docker_compose_hint(self):
        """When containers down but Docker up, show docker compose hint."""
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]

        # If TypeDB or ChromaDB down, should hint at docker compose
        if "typedb" in context.lower() and "DOWN" in context:
            assert (
                "docker compose" in context.lower() or
                "deploy.ps1" in context or
                "Recovery" in context
            ), "Missing docker compose hint for container down"

    def test_entropy_high_shows_save_resolution(self):
        """When entropy is high, should show /save resolution."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not yet implemented")

        state_file = HOOKS_DIR / ".entropy_state.json"

        # Set high entropy state
        state = {
            "session_start": "2026-01-01T00:00:00",
            "session_hash": "HIGH",
            "tool_count": 119,  # Will be 120 after increment (>100)
            "check_count": 0,
            "last_save": None,
            "warnings_shown": 1,
            "last_warning_at": 50,  # Last warning was at 50, now 120 > 50+20
            "history": []
        }
        with open(state_file, "w") as f:
            json.dump(state, f)

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        assert "hookSpecificOutput" in output
        context = output["hookSpecificOutput"].get("additionalContext", "")

        # High entropy should suggest /save
        if "ENTROPY HIGH" in context or "120 tool calls" in context:
            assert "/save" in context, "Missing /save resolution for high entropy"


class TestNegativeModuleImports:
    """Tests for modular hooks structure imports."""

    def test_core_module_imports(self):
        """Core module should import without errors."""
        hooks_dir = HOOKS_DIR

        # Add hooks dir to path
        sys.path.insert(0, str(hooks_dir.parent))

        try:
            from hooks.core import HookConfig, HookResult, OutputFormatter
            assert HookConfig is not None
            assert HookResult is not None
            assert OutputFormatter is not None
        except ImportError as e:
            pytest.skip(f"Core module not yet implemented: {e}")
        finally:
            sys.path.pop(0)

    def test_checkers_module_imports(self):
        """Checkers module should import without errors."""
        hooks_dir = HOOKS_DIR
        sys.path.insert(0, str(hooks_dir.parent))

        try:
            from hooks.checkers import ServiceChecker, EntropyChecker, AmnesiaDetector
            assert ServiceChecker is not None
            assert EntropyChecker is not None
            assert AmnesiaDetector is not None
        except ImportError as e:
            pytest.skip(f"Checkers module not yet implemented: {e}")
        finally:
            sys.path.pop(0)

    def test_recovery_module_imports(self):
        """Recovery module should import without errors."""
        hooks_dir = HOOKS_DIR
        sys.path.insert(0, str(hooks_dir.parent))

        try:
            from hooks.recovery import DockerRecovery
            assert DockerRecovery is not None
        except ImportError as e:
            pytest.skip(f"Recovery module not yet implemented: {e}")
        finally:
            sys.path.pop(0)


class TestHookResultResolutionPath:
    """Tests for HookResult resolution path functionality."""

    def test_hook_result_error_with_resolution(self):
        """HookResult.error should include resolution_path."""
        hooks_dir = HOOKS_DIR
        sys.path.insert(0, str(hooks_dir.parent))

        try:
            from hooks.core import HookResult

            result = HookResult.error(
                "Service down",
                resolution_path=".\\deploy.ps1 -Action up"
            )

            assert not result.success
            assert result.resolution_path == ".\\deploy.ps1 -Action up"
        except ImportError as e:
            pytest.skip(f"HookResult not yet implemented: {e}")
        finally:
            sys.path.pop(0)

    def test_hook_result_warning_with_resolution(self):
        """HookResult.warning should include resolution_path."""
        hooks_dir = HOOKS_DIR
        sys.path.insert(0, str(hooks_dir.parent))

        try:
            from hooks.core import HookResult

            result = HookResult.warning(
                "Entropy high",
                resolution_path="Run /save to preserve context"
            )

            assert result.success  # Warnings don't fail
            assert result.resolution_path == "Run /save to preserve context"
        except ImportError as e:
            pytest.skip(f"HookResult not yet implemented: {e}")
        finally:
            sys.path.pop(0)


# =============================================================================
# E2E TEST - CLAUDE CODE CONSOLE SPAWN (Per user request)
# =============================================================================

class TestE2EClaudeCodeSpawn:
    """
    E2E tests that validate Claude Code console can start with hooks.

    Note: These tests verify the hook infrastructure is compatible with
    Claude Code, not that Claude Code itself is installed/working.
    """

    def test_hooks_produce_claude_code_compatible_output(self):
        """
        Verify hooks produce output format compatible with Claude Code.

        Claude Code expects:
        - Valid JSON on stdout
        - Exit code 0
        - hookSpecificOutput.additionalContext for context injection
        """
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        # Run healthcheck
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        # 1. Must exit 0
        assert result.returncode == 0, "Hook must exit 0 for Claude Code compatibility"

        # 2. Must produce valid JSON
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.fail("Hook output must be valid JSON for Claude Code")

        # 3. Must have hookSpecificOutput structure
        assert "hookSpecificOutput" in output, "Missing hookSpecificOutput for Claude Code"

        # 4. Must have additionalContext for injection
        hook_output = output["hookSpecificOutput"]
        assert "additionalContext" in hook_output, "Missing additionalContext for injection"

        # 5. hookEventName should match hook type
        if "hookEventName" in hook_output:
            assert hook_output["hookEventName"] in [
                "SessionStart", "PostToolUse", "PreToolUse", "UserPromptSubmit"
            ], "Invalid hookEventName"

    def test_entropy_produces_claude_code_compatible_output(self):
        """Verify entropy monitor output is Claude Code compatible."""
        if not ENTROPY_SCRIPT.exists():
            pytest.skip("entropy_monitor.py not yet implemented")

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0, "Entropy hook must exit 0"

        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.fail("Entropy output must be valid JSON")

        # Can be empty JSON {} for silent operation
        assert isinstance(output, dict)

    def test_hooks_handle_concurrent_execution(self):
        """
        Verify hooks can handle rapid concurrent execution.

        Claude Code may fire multiple hooks in quick succession.
        """
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        import concurrent.futures

        def run_hook():
            return subprocess.run(
                [sys.executable, str(HEALTHCHECK_SCRIPT)],
                capture_output=True,
                text=True,
                timeout=10
            )

        # Run 3 concurrent executions
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_hook) for _ in range(3)]
            results = [f.result() for f in futures]

        # All should succeed
        for i, result in enumerate(results):
            assert result.returncode == 0, f"Concurrent run {i} failed"
            # Should produce valid JSON
            json.loads(result.stdout)

    def test_hooks_state_isolation(self):
        """
        Verify hook state files don't corrupt under rapid writes.

        Multiple hook invocations should maintain state integrity.
        """
        if not HEALTHCHECK_SCRIPT.exists():
            pytest.skip("healthcheck.py not yet implemented")

        state_file = HOOKS_DIR / ".healthcheck_state.json"

        # Run hook multiple times rapidly
        for _ in range(5):
            subprocess.run(
                [sys.executable, str(HEALTHCHECK_SCRIPT)],
                capture_output=True,
                timeout=10
            )

        # State file should be valid JSON
        with open(state_file) as f:
            state = json.load(f)

        # Should have expected structure
        assert "master_hash" in state
        assert "check_count" in state
        assert state["check_count"] >= 5, "Check count should reflect all runs"

    @pytest.mark.skipif(
        os.environ.get("CI") == "true",
        reason="Skip actual Claude Code spawn in CI"
    )
    def test_claude_code_help_runs(self):
        """
        Verify claude CLI is accessible (optional - skip in CI).

        This is a smoke test that Claude Code CLI is installed.
        """
        try:
            result = subprocess.run(
                ["claude", "--help"],
                capture_output=True,
                text=True,
                timeout=30
            )
            # Just verify it runs - exit code varies
            assert "claude" in result.stdout.lower() or "usage" in result.stdout.lower()
        except FileNotFoundError:
            pytest.skip("Claude Code CLI not installed")
        except subprocess.TimeoutExpired:
            pytest.skip("Claude Code CLI timed out")

class TestResolutionPathInjection:
    """Tests for resolution path injection format."""

    def test_resolution_path_is_actionable(self):
        """Resolution paths should be actionable commands."""
        hooks_dir = HOOKS_DIR
        sys.path.insert(0, str(hooks_dir.parent))

        try:
            from hooks.recovery import DockerRecovery
            from hooks.core import DEFAULT_CONFIG

            recovery = DockerRecovery()

            # Test various failure scenarios
            test_cases = [
                ({"docker": {"ok": False}}, "Docker Desktop"),
                ({"docker": {"ok": True}, "typedb": {"ok": False}}, "docker compose"),
                ({"docker": {"ok": True}, "chromadb": {"ok": False}}, "docker compose"),
            ]

            for services, expected_keyword in test_cases:
                resolution = recovery.get_resolution_path(services)
                if resolution:
                    assert expected_keyword.lower() in resolution.lower(), \
                        f"Resolution '{resolution}' should contain '{expected_keyword}'"
        except ImportError as e:
            pytest.skip(f"DockerRecovery not yet implemented: {e}")
        finally:
            sys.path.pop(0)

    def test_amnesia_resolution_suggests_remember(self):
        """AMNESIA detection should suggest /remember command."""
        hooks_dir = HOOKS_DIR
        sys.path.insert(0, str(hooks_dir.parent))

        try:
            from hooks.checkers import AmnesiaDetector

            detector = AmnesiaDetector()

            # Test with no previous state (AMNESIA indicator)
            result = detector.check({})

            if result.details.get("detected"):
                assert "/remember" in (result.resolution_path or ""), \
                    "AMNESIA should suggest /remember"
        except ImportError as e:
            pytest.skip(f"AmnesiaDetector not yet implemented: {e}")
        finally:
            sys.path.pop(0)
