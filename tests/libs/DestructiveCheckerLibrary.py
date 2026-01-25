"""
Robot Framework Library for Destructive Command Checker Tests.

Per GAP-DESTRUCT-001: Validates the destructive command detection module.
Per SAFETY-DESTR-01-v1: Ensures enforcement mechanism works correctly.
Migrated from tests/test_destructive_checker.py
"""
import sys
from pathlib import Path
from robot.api.deco import keyword


class DestructiveCheckerLibrary:
    """Library for testing destructive command detection."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self._checker_loaded = False
        self._check_destructive_command = None
        self._format_warning = None
        self._get_safe_alternative = None
        self._destructive_patterns = None
        self._blocked_patterns = None

    def _load_checker(self):
        """Load the destructive checker module."""
        if self._checker_loaded:
            return True

        try:
            import importlib.util
            hooks_dir = Path(__file__).parent.parent.parent / ".claude" / "hooks"
            checkers_dir = hooks_dir / "checkers"
            destructive_file = checkers_dir / "destructive.py"

            if not destructive_file.exists():
                return False

            spec = importlib.util.spec_from_file_location("destructive", destructive_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            self._check_destructive_command = module.check_destructive_command
            self._format_warning = module.format_warning
            self._get_safe_alternative = module.get_safe_alternative
            self._destructive_patterns = module.DESTRUCTIVE_PATTERNS
            self._blocked_patterns = module.BLOCKED_PATTERNS
            self._checker_loaded = True
            return True
        except Exception:
            return False

    # =============================================================================
    # Destructive Command Detection Tests
    # =============================================================================

    @keyword("Safe Commands Allowed")
    def safe_commands_allowed(self):
        """Safe commands should not be flagged."""
        if not self._load_checker():
            return {"skipped": True, "reason": "Checker module not found"}

        safe_commands = [
            "ls -la",
            "cat file.txt",
            "grep pattern file",
            "git status",
            "podman ps",
            "python3 script.py",
        ]

        all_safe = True
        for cmd in safe_commands:
            result = self._check_destructive_command(cmd)
            if result.is_destructive or result.is_blocked:
                all_safe = False
                break

        return {"all_safe": all_safe, "tested_count": len(safe_commands)}

    @keyword("Rm Rf Detected")
    def rm_rf_detected(self):
        """rm -rf should be detected as destructive."""
        if not self._load_checker():
            return {"skipped": True, "reason": "Checker module not found"}

        result = self._check_destructive_command("rm -rf /tmp/test")
        return {
            "is_destructive": result.is_destructive,
            "has_description": "rm" in result.risk_description.lower()
        }

    @keyword("Git Reset Hard Detected")
    def git_reset_hard_detected(self):
        """git reset --hard should be detected as destructive."""
        if not self._load_checker():
            return {"skipped": True, "reason": "Checker module not found"}

        result = self._check_destructive_command("git reset --hard HEAD~1")
        return {
            "is_destructive": result.is_destructive,
            "mentions_uncommitted": "uncommitted" in result.risk_description.lower()
        }

    @keyword("Git Push Force Detected")
    def git_push_force_detected(self):
        """git push --force should be detected as destructive."""
        if not self._load_checker():
            return {"skipped": True, "reason": "Checker module not found"}

        result = self._check_destructive_command("git push --force origin main")
        return {"is_destructive": result.is_destructive}

    @keyword("Podman System Prune Detected")
    def podman_system_prune_detected(self):
        """podman system prune should be detected as destructive."""
        if not self._load_checker():
            return {"skipped": True, "reason": "Checker module not found"}

        result = self._check_destructive_command("podman system prune -a")
        return {"is_destructive": result.is_destructive}

    @keyword("Drop Table Detected")
    def drop_table_detected(self):
        """DROP TABLE should be detected as destructive."""
        if not self._load_checker():
            return {"skipped": True, "reason": "Checker module not found"}

        result = self._check_destructive_command("DROP TABLE users;")
        return {"is_destructive": result.is_destructive}

    # =============================================================================
    # Blocked Commands Tests
    # =============================================================================

    @keyword("Rm Rf Root Blocked")
    def rm_rf_root_blocked(self):
        """rm -rf / should be blocked."""
        if not self._load_checker():
            return {"skipped": True, "reason": "Checker module not found"}

        result = self._check_destructive_command("rm -rf /")
        return {
            "is_blocked": result.is_blocked,
            "is_destructive": result.is_destructive
        }

    @keyword("Rm Rf Root Wildcard Blocked")
    def rm_rf_root_wildcard_blocked(self):
        """rm -rf /* should be blocked."""
        if not self._load_checker():
            return {"skipped": True, "reason": "Checker module not found"}

        result = self._check_destructive_command("rm -rf /*")
        return {"is_blocked": result.is_blocked}

    # =============================================================================
    # Warning Formatting Tests
    # =============================================================================

    @keyword("Blocked Warning Format")
    def blocked_warning_format(self):
        """Blocked commands should have BLOCKED in warning."""
        if not self._load_checker():
            return {"skipped": True, "reason": "Checker module not found"}

        result = self._check_destructive_command("rm -rf /")
        warning = self._format_warning(result)
        return {"has_blocked": "BLOCKED" in warning}

    @keyword("Destructive Warning Format")
    def destructive_warning_format(self):
        """Destructive commands should have WARNING and rule reference."""
        if not self._load_checker():
            return {"skipped": True, "reason": "Checker module not found"}

        result = self._check_destructive_command("rm -rf /tmp/test")
        warning = self._format_warning(result)
        return {
            "has_warning": "WARNING" in warning,
            "has_rule_ref": "SAFETY-DESTR-01-v1" in warning
        }

    @keyword("Safe Command No Warning")
    def safe_command_no_warning(self):
        """Safe commands should have empty warning."""
        if not self._load_checker():
            return {"skipped": True, "reason": "Checker module not found"}

        result = self._check_destructive_command("ls -la")
        warning = self._format_warning(result)
        return {"empty_warning": warning == ""}

    # =============================================================================
    # Safe Alternatives Tests
    # =============================================================================

    @keyword("Rm Rf Alternative Suggested")
    def rm_rf_alternative_suggested(self):
        """rm -rf should suggest rm -i."""
        if not self._load_checker():
            return {"skipped": True, "reason": "Checker module not found"}

        result = self._check_destructive_command("rm -rf /tmp/test")
        alt = self._get_safe_alternative(result)
        return {
            "has_alternative": alt is not None,
            "suggests_rm_i": "rm -i" in alt if alt else False
        }

    @keyword("Git Reset Hard Alternative Suggested")
    def git_reset_hard_alternative_suggested(self):
        """git reset --hard should suggest git stash."""
        if not self._load_checker():
            return {"skipped": True, "reason": "Checker module not found"}

        result = self._check_destructive_command("git reset --hard HEAD")
        alt = self._get_safe_alternative(result)
        return {
            "has_alternative": alt is not None,
            "suggests_stash": "stash" in alt.lower() if alt else False
        }

    @keyword("Git Push Force Alternative Suggested")
    def git_push_force_alternative_suggested(self):
        """git push --force should suggest --force-with-lease."""
        if not self._load_checker():
            return {"skipped": True, "reason": "Checker module not found"}

        result = self._check_destructive_command("git push --force")
        alt = self._get_safe_alternative(result)
        return {
            "has_alternative": alt is not None,
            "suggests_lease": "force-with-lease" in alt if alt else False
        }

    # =============================================================================
    # Pattern Coverage Tests
    # =============================================================================

    @keyword("Has Destructive Patterns")
    def has_destructive_patterns(self):
        """Should have multiple destructive patterns defined."""
        if not self._load_checker():
            return {"skipped": True, "reason": "Checker module not found"}

        return {
            "has_patterns": len(self._destructive_patterns) >= 10,
            "pattern_count": len(self._destructive_patterns)
        }

    @keyword("Has Blocked Patterns")
    def has_blocked_patterns(self):
        """Should have blocked patterns defined."""
        if not self._load_checker():
            return {"skipped": True, "reason": "Checker module not found"}

        return {
            "has_patterns": len(self._blocked_patterns) >= 1,
            "pattern_count": len(self._blocked_patterns)
        }

    @keyword("All Patterns Have Descriptions")
    def all_patterns_have_descriptions(self):
        """All patterns should have descriptions."""
        if not self._load_checker():
            return {"skipped": True, "reason": "Checker module not found"}

        all_have_desc = True
        for pattern, desc in self._destructive_patterns:
            if not desc:
                all_have_desc = False
                break
        for pattern, desc in self._blocked_patterns:
            if not desc:
                all_have_desc = False
                break

        return {"all_have_descriptions": all_have_desc}
