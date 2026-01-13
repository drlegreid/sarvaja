"""
Destructive Command Checker Tests

Per GAP-DESTRUCT-001: Validates the destructive command detection module.
Per SAFETY-DESTR-01-v1: Ensures enforcement mechanism works correctly.
"""

import pytest
import sys
from pathlib import Path

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).parent.parent / ".claude" / "hooks"
CHECKERS_DIR = HOOKS_DIR / "checkers"
sys.path.insert(0, str(CHECKERS_DIR))

# Import directly from the module file
import importlib.util
_spec = importlib.util.spec_from_file_location("destructive", CHECKERS_DIR / "destructive.py")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

check_destructive_command = _module.check_destructive_command
format_warning = _module.format_warning
get_safe_alternative = _module.get_safe_alternative
DESTRUCTIVE_PATTERNS = _module.DESTRUCTIVE_PATTERNS
BLOCKED_PATTERNS = _module.BLOCKED_PATTERNS


class TestDestructiveCommandDetection:
    """Test destructive command pattern matching."""

    @pytest.mark.unit
    def test_safe_command_allowed(self):
        """Safe commands should not be flagged."""
        safe_commands = [
            "ls -la",
            "cat file.txt",
            "grep pattern file",
            "git status",
            "podman ps",
            "python3 script.py",
        ]
        for cmd in safe_commands:
            result = check_destructive_command(cmd)
            assert not result.is_destructive, f"Safe command flagged: {cmd}"
            assert not result.is_blocked, f"Safe command blocked: {cmd}"

    @pytest.mark.unit
    def test_rm_rf_detected(self):
        """rm -rf should be detected as destructive."""
        result = check_destructive_command("rm -rf /tmp/test")
        assert result.is_destructive
        assert "rm -rf" in result.risk_description.lower()

    @pytest.mark.unit
    def test_rm_r_detected(self):
        """rm -r should be detected as destructive."""
        result = check_destructive_command("rm -r directory/")
        assert result.is_destructive

    @pytest.mark.unit
    def test_git_reset_hard_detected(self):
        """git reset --hard should be detected as destructive."""
        result = check_destructive_command("git reset --hard HEAD~1")
        assert result.is_destructive
        assert "uncommitted" in result.risk_description.lower()

    @pytest.mark.unit
    def test_git_push_force_detected(self):
        """git push --force should be detected as destructive."""
        result = check_destructive_command("git push --force origin main")
        assert result.is_destructive

    @pytest.mark.unit
    def test_git_push_f_detected(self):
        """git push -f should be detected as destructive."""
        result = check_destructive_command("git push -f origin main")
        assert result.is_destructive

    @pytest.mark.unit
    def test_podman_system_prune_detected(self):
        """podman system prune should be detected as destructive."""
        result = check_destructive_command("podman system prune -a")
        assert result.is_destructive

    @pytest.mark.unit
    def test_docker_system_prune_detected(self):
        """docker system prune should be detected as destructive."""
        result = check_destructive_command("docker system prune")
        assert result.is_destructive

    @pytest.mark.unit
    def test_drop_table_detected(self):
        """DROP TABLE should be detected as destructive."""
        result = check_destructive_command("DROP TABLE users;")
        assert result.is_destructive

    @pytest.mark.unit
    def test_delete_without_where_detected(self):
        """DELETE FROM without WHERE should be detected as destructive."""
        result = check_destructive_command("DELETE FROM users;")
        assert result.is_destructive


class TestBlockedCommands:
    """Test commands that should be completely blocked."""

    @pytest.mark.unit
    def test_rm_rf_root_blocked(self):
        """rm -rf / should be blocked."""
        result = check_destructive_command("rm -rf /")
        assert result.is_blocked
        assert result.is_destructive

    @pytest.mark.unit
    def test_rm_rf_root_wildcard_blocked(self):
        """rm -rf /* should be blocked."""
        result = check_destructive_command("rm -rf /*")
        assert result.is_blocked


class TestWarningFormatting:
    """Test warning message formatting."""

    @pytest.mark.unit
    def test_blocked_warning_format(self):
        """Blocked commands should have BLOCKED in warning."""
        result = check_destructive_command("rm -rf /")
        warning = format_warning(result)
        assert "BLOCKED" in warning

    @pytest.mark.unit
    def test_destructive_warning_format(self):
        """Destructive commands should have WARNING and rule reference."""
        result = check_destructive_command("rm -rf /tmp/test")
        warning = format_warning(result)
        assert "WARNING" in warning
        assert "SAFETY-DESTR-01-v1" in warning

    @pytest.mark.unit
    def test_safe_command_no_warning(self):
        """Safe commands should have empty warning."""
        result = check_destructive_command("ls -la")
        warning = format_warning(result)
        assert warning == ""


class TestSafeAlternatives:
    """Test safer alternative suggestions."""

    @pytest.mark.unit
    def test_rm_rf_alternative(self):
        """rm -rf should suggest rm -i."""
        result = check_destructive_command("rm -rf /tmp/test")
        alt = get_safe_alternative(result)
        assert alt is not None
        assert "rm -i" in alt

    @pytest.mark.unit
    def test_git_reset_hard_alternative(self):
        """git reset --hard should suggest git stash."""
        result = check_destructive_command("git reset --hard HEAD")
        alt = get_safe_alternative(result)
        assert alt is not None
        assert "stash" in alt.lower()

    @pytest.mark.unit
    def test_git_push_force_alternative(self):
        """git push --force should suggest --force-with-lease."""
        result = check_destructive_command("git push --force")
        alt = get_safe_alternative(result)
        assert alt is not None
        assert "force-with-lease" in alt


class TestPatternCoverage:
    """Verify pattern list coverage."""

    @pytest.mark.unit
    def test_has_destructive_patterns(self):
        """Should have multiple destructive patterns defined."""
        assert len(DESTRUCTIVE_PATTERNS) >= 10

    @pytest.mark.unit
    def test_has_blocked_patterns(self):
        """Should have blocked patterns defined."""
        assert len(BLOCKED_PATTERNS) >= 1

    @pytest.mark.unit
    def test_all_patterns_have_descriptions(self):
        """All patterns should have descriptions."""
        for pattern, desc in DESTRUCTIVE_PATTERNS:
            assert desc, f"Pattern {pattern} missing description"
        for pattern, desc in BLOCKED_PATTERNS:
            assert desc, f"Pattern {pattern} missing description"
