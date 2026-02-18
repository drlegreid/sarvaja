"""Deep scan batch 154: Context preloader + entropy + config.

Batch 154 findings: 7 total, 1 confirmed fix, 6 rejected.
- BUG-PRELOAD-001: result.is_warning property doesn't exist on HookResult
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── HookResult has no is_warning defense ──────────────


class TestHookResultIsWarningDefense:
    """Verify HookResult uses status field, not is_warning property."""

    def test_hookresult_has_no_is_warning(self):
        """HookResult dataclass has no is_warning property."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".claude" / "hooks"))
        from core.base import HookResult
        r = HookResult.ok("test")
        assert not hasattr(type(r), "is_warning")

    def test_warning_uses_status_field(self):
        """HookResult.warning() sets status='WARNING'."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".claude" / "hooks"))
        from core.base import HookResult
        r = HookResult.warning("test warning")
        assert r.status == "WARNING"
        assert r.success is True  # Warnings don't fail

    def test_ok_uses_status_field(self):
        """HookResult.ok() sets status='OK'."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".claude" / "hooks"))
        from core.base import HookResult
        r = HookResult.ok("all good")
        assert r.status == "OK"
        assert r.success is True

    def test_error_uses_status_field(self):
        """HookResult.error() sets status='ERROR'."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".claude" / "hooks"))
        from core.base import HookResult
        r = HookResult.error("something broke")
        assert r.status == "ERROR"
        assert r.success is False

    def test_entropy_cli_uses_status_check(self):
        """Entropy CLI uses result.status == 'WARNING' not is_warning."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/checkers/entropy.py").read_text()
        assert 'result.status == "WARNING"' in src
        assert "result.is_warning" not in src


# ── Context monitor state file defense ──────────────


class TestContextMonitorStateFileDefense:
    """Verify context_monitor.py state file handling."""

    def test_state_file_parent_exists(self):
        """STATE_FILE parent is .claude/hooks/ which always exists."""
        root = Path(__file__).parent.parent.parent
        hooks_dir = root / ".claude" / "hooks"
        assert hooks_dir.is_dir()

    def test_save_state_catches_errors(self):
        """save_state wraps in try/except, writes to stderr."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/checkers/context_monitor.py").read_text()
        assert "except Exception" in src
        assert "sys.stderr.write" in src

    def test_load_state_returns_default_on_error(self):
        """load_state returns default state when file missing or corrupt."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/checkers/context_monitor.py").read_text()
        assert "return get_default_state()" in src


# ── Entropy checker thresholds defense ──────────────


class TestEntropyCheckerThresholdsDefense:
    """Verify entropy thresholds are correctly ordered."""

    def _read_thresholds(self):
        """Extract threshold values from entropy.py source."""
        import re
        src = (Path(__file__).parent.parent.parent / ".claude/hooks/checkers/entropy.py").read_text()
        medium = int(re.search(r"MEDIUM_THRESHOLD\s*=\s*(\d+)", src).group(1))
        high = int(re.search(r"HIGH_THRESHOLD\s*=\s*(\d+)", src).group(1))
        critical = int(re.search(r"CRITICAL_THRESHOLD\s*=\s*(\d+)", src).group(1))
        time_t = int(re.search(r"TIME_THRESHOLD\s*=\s*(\d+)", src).group(1))
        return medium, high, critical, time_t

    def test_thresholds_ascending(self):
        """MEDIUM < HIGH < CRITICAL."""
        medium, high, critical, _ = self._read_thresholds()
        assert medium < high < critical

    def test_threshold_values(self):
        """Thresholds match documented values (50/100/150)."""
        medium, high, critical, _ = self._read_thresholds()
        assert medium == 50
        assert high == 100
        assert critical == 150

    def test_time_threshold_60_minutes(self):
        """Time-based reminder at 60 minutes."""
        _, _, _, time_t = self._read_thresholds()
        assert time_t == 60


# ── Entropy state management defense ──────────────


class TestEntropyStateManagementDefense:
    """Verify entropy state persistence patterns."""

    def test_entropy_file_in_hooks_dir(self):
        """Entropy state file is in .claude/hooks/ directory."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".claude" / "hooks"))
        from core.base import HookConfig
        config = HookConfig()
        assert config.entropy_file.parent == config.hooks_dir

    def test_state_file_in_hooks_dir(self):
        """Healthcheck state file is in .claude/hooks/ directory."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".claude" / "hooks"))
        from core.base import HookConfig
        config = HookConfig()
        assert config.state_file.parent == config.hooks_dir

    def test_hooks_dir_is_parent_of_checkers(self):
        """hooks_dir resolves to .claude/hooks/ (parent of core/)."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".claude" / "hooks"))
        from core.base import HookConfig
        config = HookConfig()
        assert config.hooks_dir.name == "hooks"
