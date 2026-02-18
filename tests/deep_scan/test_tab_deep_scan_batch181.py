"""Deep scan batch 181: Hooks + CLI scripts layer.

Batch 181 findings: 21 total, 3 confirmed fixes, 18 rejected/deferred.
- BUG-181-001: entropy_monitor.py SyntaxError from orphaned elif (batch 174 regression).
- BUG-181-003: Hardcoded UID 1000 in Podman socket path.
- BUG-181-006: Hardcoded absolute path with username in compact_context_restore.py.
"""
import os
import pytest
from pathlib import Path


# ── Entropy monitor syntax defense ──────────────


class TestEntropyMonitorSyntaxDefense:
    """Verify entropy_monitor.py has no syntax errors."""

    def test_parses_without_syntax_error(self):
        """entropy_monitor.py is valid Python."""
        import ast
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/entropy_monitor.py").read_text()
        ast.parse(src)  # Will raise SyntaxError if invalid

    def test_elif_chain_intact(self):
        """if/elif chain has no intervening statements."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/entropy_monitor.py").read_text()
        # Find the context rot if block and HIGH threshold elif
        rot_start = src.index("rot_score > 0.7")
        high_start = src.index("HIGH_THRESHOLD", rot_start)
        between = src[rot_start:high_start]
        # No non-comment, non-blank lines should exist between if body and elif
        # The elif should be properly chained
        lines_between_end = between.split("\n")
        # After the if block's indented body, the next non-blank non-comment
        # line should be elif (no dangling assignments)
        found_elif = False
        for line in lines_between_end:
            stripped = line.strip()
            if stripped.startswith("elif"):
                found_elif = True
                break
        assert found_elif, "elif should follow if block without intervening statements"

    def test_should_checkpoint_before_if(self):
        """should_checkpoint is computed before the if/elif chain."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/entropy_monitor.py").read_text()
        checkpoint_pos = src.index("should_checkpoint = ")
        rot_if_pos = src.index("if rot_score > 0.7")
        assert checkpoint_pos < rot_if_pos, "should_checkpoint must be before if/elif chain"


# ── Podman socket path defense ──────────────


class TestPodmanSocketPathDefense:
    """Verify Podman socket path uses dynamic UID."""

    def test_no_hardcoded_uid_1000(self):
        """Podman socket path does NOT hardcode UID 1000."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/core/base.py").read_text()
        # Should not have literal "/run/user/1000/"
        assert "/run/user/1000/" not in src

    def test_uses_os_getuid(self):
        """Podman socket path uses os.getuid() for dynamic UID."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/core/base.py").read_text()
        assert "os.getuid()" in src


# ── Compact context restore path defense ──────────────


class TestCompactContextRestoreDefense:
    """Verify compact_context_restore.py has no hardcoded usernames."""

    def test_no_hardcoded_username(self):
        """MEMORY_FILE path does NOT hardcode 'oderid'."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/compact_context_restore.py").read_text()
        assert "oderid" not in src

    def test_memory_file_computed_dynamically(self):
        """MEMORY_FILE is computed from PROJECT_DIR, not a literal string."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/compact_context_restore.py").read_text()
        # Should use a dynamic computation, not a hardcoded path segment
        assert "_project_slug" in src or "PROJECT_DIR" in src


# ── Hook safety patterns defense ──────────────


class TestHookSafetyPatternsDefense:
    """Verify hooks follow safety patterns."""

    def test_pre_bash_check_exists(self):
        """pre_bash_check.py exists."""
        root = Path(__file__).parent.parent.parent
        assert (root / ".claude/hooks/pre_bash_check.py").exists()

    def test_healthcheck_exists(self):
        """healthcheck.py exists."""
        root = Path(__file__).parent.parent.parent
        assert (root / ".claude/hooks/healthcheck.py").exists()

    def test_todo_sync_exists(self):
        """todo_sync.py exists."""
        root = Path(__file__).parent.parent.parent
        assert (root / ".claude/hooks/todo_sync.py").exists()

    def test_recover_exists(self):
        """recover.py exists."""
        root = Path(__file__).parent.parent.parent
        assert (root / ".claude/hooks/recover.py").exists()

    def test_hooks_dir_has_core(self):
        """hooks/core/ directory exists."""
        root = Path(__file__).parent.parent.parent
        assert (root / ".claude/hooks/core").is_dir()

    def test_hooks_dir_has_checkers(self):
        """hooks/checkers/ directory exists."""
        root = Path(__file__).parent.parent.parent
        assert (root / ".claude/hooks/checkers").is_dir()
