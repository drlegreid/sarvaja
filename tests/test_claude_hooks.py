"""
E2E and Unit Tests for Claude Code Hooks - Healthcheck

Per GAP-MCP-003: Verify SessionStart hook context injection
Per RULE-023: TDD - tests written before implementation

Tests verify:
1. Healthcheck script produces valid JSON
2. Non-blocking behavior (max 5s for initial check)
3. 30-second retry ceiling when state unchanged
4. Graceful degradation when services down
5. hookSpecificOutput format for Claude Code

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

# Path to the healthcheck script
HOOKS_DIR = Path(__file__).parent.parent / ".claude" / "hooks"
HEALTHCHECK_SCRIPT = HOOKS_DIR / "healthcheck.py"


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

        # Simulate state that's been unchanged for 31 seconds
        old_state = {
            "master_hash": "DEADBEEF",
            "last_check": "2020-01-01T00:00:00",  # Old timestamp
            "check_count": 100,
            "unchanged_since": time.time() - 31,  # 31 seconds ago
            "components": {"docker": "DOWN", "typedb": "DOWN", "chromadb": "DOWN"}
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

        # Should indicate retry ceiling reached or provide cached response
        assert "cached" in context.lower() or "ceiling" in context.lower() or "retry" in context.lower() or len(context) < 200


class TestHealthcheckServiceDetection:
    """Tests for Docker/service detection logic."""

    def test_detects_docker_status(self):
        """Should detect whether Docker daemon is running."""
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

        # Should mention Docker status
        assert "docker" in context.lower() or "DOCKER" in context

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

        # Every subprocess.run should have timeout
        import re
        subprocess_calls = re.findall(r'subprocess\.run\([^)]+\)', content, re.DOTALL)

        for call in subprocess_calls:
            assert "timeout" in call, f"subprocess.run missing timeout: {call[:100]}"

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
