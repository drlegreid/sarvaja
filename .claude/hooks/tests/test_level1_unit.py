"""
Level 1: Unit Tests - Fast, no external dependencies.

Run: python -m pytest .claude/hooks/tests/level1_unit.py -v
"""

import json
import sys
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

# Add hooks to path
HOOKS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(HOOKS_DIR.parent))


class TestCoreImports:
    """Test that core modules import correctly."""

    def test_base_imports(self):
        """Base module imports without errors."""
        from hooks.core.base import HookConfig, HookResult, ServiceInfo
        assert HookConfig is not None
        assert HookResult is not None
        assert ServiceInfo is not None

    def test_state_imports(self):
        """State module imports without errors."""
        from hooks.core.state import (
            StateManager,
            compute_frankel_hash,
            compute_session_hash
        )
        assert StateManager is not None
        assert compute_frankel_hash is not None

    def test_formatters_imports(self):
        """Formatters module imports without errors."""
        from hooks.core.formatters import OutputFormatter, HealthFormatter
        assert OutputFormatter is not None
        assert HealthFormatter is not None


class TestHookResult:
    """Test HookResult dataclass functionality."""

    def test_ok_result(self):
        """HookResult.ok creates successful result."""
        from hooks.core.base import HookResult

        result = HookResult.ok("Test passed", extra="data")
        assert result.success is True
        assert result.status == "OK"
        assert result.message == "Test passed"
        assert result.details.get("extra") == "data"

    def test_error_result(self):
        """HookResult.error creates error with resolution."""
        from hooks.core.base import HookResult

        result = HookResult.error(
            "Service down",
            resolution_path="Run recovery script"
        )
        assert result.success is False
        assert result.status == "ERROR"
        assert result.resolution_path == "Run recovery script"

    def test_warning_result(self):
        """HookResult.warning creates warning (still success)."""
        from hooks.core.base import HookResult

        result = HookResult.warning("Entropy high", resolution_path="/save")
        assert result.success is True  # Warnings don't fail
        assert result.status == "WARNING"
        assert result.resolution_path == "/save"

    def test_to_dict(self):
        """HookResult serializes to dictionary."""
        from hooks.core.base import HookResult

        result = HookResult.ok("Test", foo="bar")
        d = result.to_dict()
        assert d["success"] is True
        assert d["message"] == "Test"
        assert d["details"]["foo"] == "bar"


class TestHashFunctions:
    """Test hash computation functions."""

    def test_frankel_hash_deterministic(self):
        """Same input produces same hash."""
        from hooks.core.state import compute_frankel_hash

        data = {"docker": "OK", "typedb": "OK"}
        h1 = compute_frankel_hash(data)
        h2 = compute_frankel_hash(data)
        assert h1 == h2

    def test_frankel_hash_changes(self):
        """Different input produces different hash."""
        from hooks.core.state import compute_frankel_hash

        h1 = compute_frankel_hash({"docker": "OK"})
        h2 = compute_frankel_hash({"docker": "DOWN"})
        assert h1 != h2

    def test_frankel_hash_format(self):
        """Hash is 8 uppercase hex characters."""
        from hooks.core.state import compute_frankel_hash

        h = compute_frankel_hash({"test": True})
        assert len(h) == 8
        assert h == h.upper()
        assert all(c in "0123456789ABCDEF" for c in h)

    def test_session_hash_format(self):
        """Session hash is 4 uppercase hex characters."""
        from hooks.core.state import compute_session_hash

        h = compute_session_hash("2026-01-01T00:00:00", 50)
        assert len(h) == 4
        assert h == h.upper()
        assert all(c in "0123456789ABCDEF" for c in h)


class TestOutputFormatter:
    """Test JSON output formatting."""

    def test_to_json_format(self):
        """Output is valid JSON with hookSpecificOutput."""
        from hooks.core.formatters import OutputFormatter

        output = OutputFormatter.to_json("Test context", "SessionStart")
        parsed = json.loads(output)

        assert "hookSpecificOutput" in parsed
        assert parsed["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        assert parsed["hookSpecificOutput"]["additionalContext"] == "Test context"

    def test_empty_output(self):
        """Empty output is valid JSON."""
        from hooks.core.formatters import OutputFormatter

        output = OutputFormatter.empty()
        parsed = json.loads(output)
        assert parsed == {}


class TestStateManager:
    """Test state persistence."""

    def test_save_and_load(self):
        """State saves and loads correctly."""
        from hooks.core.state import StateManager

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            state_file = Path(f.name)

        try:
            manager = StateManager(state_file)
            state = {"test": "value", "count": 42}
            manager.save(state)

            manager2 = StateManager(state_file)
            loaded = manager2.load()
            assert loaded["test"] == "value"
            assert loaded["count"] == 42
        finally:
            state_file.unlink()

    def test_history_tracking(self):
        """History entries are added and limited."""
        from hooks.core.state import StateManager

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            state_file = Path(f.name)

        try:
            manager = StateManager(state_file, history_limit=3)

            for i in range(5):
                state = {"count": i, "history": manager.state.get("history", [])}
                manager.save(state, add_history=True)
                manager.load()

            final = manager.load()
            assert len(final["history"]) == 3  # Limited to 3
        finally:
            state_file.unlink()


class TestHookConfig:
    """Test configuration defaults."""

    def test_default_config(self):
        """Default configuration has expected values."""
        from hooks.core.base import DEFAULT_CONFIG

        assert DEFAULT_CONFIG.global_timeout == 3.0
        assert DEFAULT_CONFIG.subprocess_timeout == 1.0
        assert "typedb" in DEFAULT_CONFIG.core_services
        assert "chromadb" in DEFAULT_CONFIG.core_services

    def test_service_ports(self):
        """Service ports are configured."""
        from hooks.core.base import DEFAULT_CONFIG

        assert DEFAULT_CONFIG.service_ports["typedb"] == 1729
        assert DEFAULT_CONFIG.service_ports["chromadb"] == 8001


class TestContainerRecoveryImports:
    """Test ContainerRecovery class and backward compat aliases."""

    def test_container_recovery_import(self):
        """ContainerRecovery class imports correctly."""
        from hooks.recovery.containers import ContainerRecovery
        assert ContainerRecovery is not None

    def test_backward_compat_aliases(self):
        """PodmanRecovery and DockerRecovery are aliases to ContainerRecovery."""
        from hooks.recovery.containers import (
            ContainerRecovery, PodmanRecovery, DockerRecovery
        )
        assert PodmanRecovery is ContainerRecovery
        assert DockerRecovery is ContainerRecovery

    def test_recovery_module_exports(self):
        """Recovery module exports ContainerRecovery and aliases."""
        from hooks.recovery import (
            ContainerRecovery, PodmanRecovery, DockerRecovery
        )
        assert ContainerRecovery is not None
        assert PodmanRecovery is ContainerRecovery
        assert DockerRecovery is ContainerRecovery


class TestRecoveryAuditLog:
    """Test recovery audit logging functionality."""

    def test_audit_log_import(self):
        """RecoveryAuditLog class imports correctly."""
        from hooks.recovery.audit import RecoveryAuditLog
        assert RecoveryAuditLog is not None

    def test_audit_log_creates_directory(self):
        """Audit log creates log directory on init."""
        from hooks.recovery.audit import RecoveryAuditLog

        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "test_logs"
            audit = RecoveryAuditLog(log_dir=log_dir)

            assert log_dir.exists()
            assert audit.log_dir == log_dir

    def test_audit_log_records_attempt(self):
        """Audit log records recovery attempt."""
        from hooks.recovery.audit import RecoveryAuditLog

        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "test_logs"
            audit = RecoveryAuditLog(log_dir=log_dir)

            audit.log_attempt(
                action="test_action",
                success=True,
                services=["typedb", "chromadb"],
                duration_ms=100
            )

            # Check log file exists and has content
            log_file = audit.current_log_file
            assert log_file.exists()

            with open(log_file) as f:
                content = f.read()
                assert "test_action" in content
                assert "typedb" in content
