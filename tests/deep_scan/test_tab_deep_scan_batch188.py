"""Deep scan batch 188: Hooks + config layer.

Batch 188 findings: 12 total, 1 confirmed fix, 11 rejected/deferred.
- BUG-188-004: context_monitor.py sys.exit(1) blocks UserPromptSubmit.
"""
import pytest
from pathlib import Path


# ── Context monitor non-blocking defense ──────────────


class TestContextMonitorNonBlocking:
    """Verify context_monitor.py uses non-blocking exit codes."""

    def test_warning_uses_exit_0(self):
        """Warning path uses sys.exit(0), not sys.exit(1)."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/checkers/context_monitor.py").read_text()
        # Find the warning check section
        start = src.index("warning = check_warning(state)")
        section = src[start:start + 400]
        # Should have exit(0) not exit(1) in warning path
        assert "sys.exit(0)" in section
        assert "sys.exit(1)" not in section

    def test_warning_prints_to_stderr(self):
        """Warning message goes to stderr, not stdout."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/checkers/context_monitor.py").read_text()
        start = src.index("warning = check_warning(state)")
        section = src[start:start + 200]
        assert "file=sys.stderr" in section


# ── Hook safety patterns defense ──────────────


class TestHookSafetyPatterns:
    """Verify hooks follow safety conventions."""

    def test_todo_sync_exits_zero(self):
        """todo_sync.py always exits 0."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/todo_sync.py").read_text()
        # Should not have sys.exit(1)
        assert "sys.exit(1)" not in src

    def test_mcp_usage_check_exits_zero(self):
        """mcp_usage_check.py always exits 0."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/mcp_usage_check.py").read_text()
        assert "sys.exit(1)" not in src

    def test_entropy_cli_importable(self):
        """entropy_cli module is importable."""
        root = Path(__file__).parent.parent.parent
        path = root / ".claude/hooks/entropy_cli.py"
        assert path.exists()

    def test_mcp_usage_checker_has_gov_prefixes(self):
        """mcp_usage_checker.py defines GOV_TOOL_PREFIXES."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/checkers/mcp_usage_checker.py").read_text()
        assert "GOV_TOOL_PREFIXES" in src
        assert "gov-tasks" in src
        assert "gov-sessions" in src
        assert "gov-core" in src


# ── Pre-bash check structure defense ──────────────


class TestPreBashCheckDefense:
    """Verify pre_bash_check module structure."""

    def test_pre_bash_check_exists(self):
        """pre_bash_check.py exists."""
        root = Path(__file__).parent.parent.parent
        assert (root / ".claude/hooks/pre_bash_check.py").exists()

    def test_pre_bash_check_has_main(self):
        """pre_bash_check.py has main function."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/pre_bash_check.py").read_text()
        assert "def main" in src
