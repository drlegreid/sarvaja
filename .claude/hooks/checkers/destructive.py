#!/usr/bin/env python3
"""
Destructive Command Detection - GAP-DESTRUCT-001

Per SAFETY-DESTR-01-v1: Detects and blocks destructive commands that could
cause irreversible data loss. Used by PreToolUse hook for Bash commands.

Protected patterns:
- rm -rf / rm -r: Recursive file deletion
- git reset --hard: Lose uncommitted changes
- git push --force: Overwrite remote history
- podman/docker system prune: Wipe containers/images
- DROP TABLE / DELETE FROM: Database destruction
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

# CRITICAL: Patterns that require explicit user confirmation
DESTRUCTIVE_PATTERNS = [
    # File system destruction
    (r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+|--recursive)", "rm -rf/rm -r: Recursive file deletion"),
    (r"rm\s+.*\*", "rm with wildcard: May delete unexpected files"),

    # Git history destruction
    (r"git\s+reset\s+--hard", "git reset --hard: Loses uncommitted changes"),
    (r"git\s+push\s+.*--force", "git push --force: Overwrites remote history"),
    (r"git\s+push\s+-f\b", "git push -f: Overwrites remote history"),
    (r"git\s+clean\s+-[a-zA-Z]*f", "git clean -f: Removes untracked files"),

    # Container destruction
    (r"(podman|docker)\s+system\s+prune", "system prune: Removes unused containers/images"),
    (r"(podman|docker)\s+system\s+reset", "system reset: Wipes all containers/images"),
    (r"(podman|docker)\s+image\s+prune\s+-a", "image prune -a: Removes all unused images"),
    (r"(podman|docker)\s+volume\s+prune", "volume prune: Removes unused volumes"),
    (r"(podman|docker)\s+rm\s+-f", "container rm -f: Force removes running container"),

    # Database destruction
    (r"DROP\s+(TABLE|DATABASE|INDEX|SCHEMA)", "DROP: Deletes database objects"),
    (r"TRUNCATE\s+TABLE", "TRUNCATE: Empties table"),
    (r"DELETE\s+FROM\s+\w+\s*;?\s*$", "DELETE without WHERE: Deletes all rows"),

    # System destruction
    (r"mkfs\.", "mkfs: Formats filesystem"),
    (r"dd\s+.*of=/dev/", "dd to device: Overwrites disk"),
    (r"fdisk\s+", "fdisk: Partitions disk"),
    (r"chmod\s+777\s+/", "chmod 777 on root: Security risk"),

    # TypeDB destruction
    (r"match\s+.*\s+delete\s+", "TypeQL delete: Removes TypeDB data"),
]

# Commands that are always blocked (no confirmation possible)
BLOCKED_PATTERNS = [
    (r"rm\s+-rf\s+/\s*$", "rm -rf /: System destruction"),
    (r"rm\s+-rf\s+/\*", "rm -rf /*: System destruction"),
    (r":\s*\(\s*\)\s*\{\s*:\s*\|", "Fork bomb: System crash"),
]


@dataclass
class DestructiveCheckResult:
    """Result of destructive command check."""
    is_destructive: bool
    is_blocked: bool
    pattern_matched: Optional[str]
    risk_description: Optional[str]
    command: str


def check_destructive_command(command: str) -> DestructiveCheckResult:
    """
    Check if a command matches destructive patterns.

    Args:
        command: The bash command to check

    Returns:
        DestructiveCheckResult with detection details
    """
    # First check blocked patterns (never allowed)
    for pattern, description in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return DestructiveCheckResult(
                is_destructive=True,
                is_blocked=True,
                pattern_matched=pattern,
                risk_description=description,
                command=command
            )

    # Then check destructive patterns (require confirmation)
    for pattern, description in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return DestructiveCheckResult(
                is_destructive=True,
                is_blocked=False,
                pattern_matched=pattern,
                risk_description=description,
                command=command
            )

    return DestructiveCheckResult(
        is_destructive=False,
        is_blocked=False,
        pattern_matched=None,
        risk_description=None,
        command=command
    )


def format_warning(result: DestructiveCheckResult) -> str:
    """Format a warning message for destructive command detection."""
    if result.is_blocked:
        return (
            f"BLOCKED: {result.risk_description}\n"
            f"Command: {result.command}\n"
            f"This command is NEVER allowed as it could cause catastrophic damage."
        )
    elif result.is_destructive:
        return (
            f"WARNING: Destructive command detected!\n"
            f"Risk: {result.risk_description}\n"
            f"Command: {result.command}\n"
            f"\n"
            f"Per SAFETY-DESTR-01-v1: This command requires user confirmation.\n"
            f"Before proceeding, verify:\n"
            f"1. You have checked current state (ls, git status, podman ps)\n"
            f"2. You have backups if needed\n"
            f"3. This is the intended action"
        )
    return ""


def get_safe_alternative(result: DestructiveCheckResult) -> Optional[str]:
    """Suggest a safer alternative for destructive commands."""
    alternatives = {
        "rm -rf": "Use 'rm -i' for interactive confirmation or list files explicitly",
        "rm -r": "Use 'rm -i' for interactive confirmation or list files explicitly",
        "git reset --hard": "Use 'git stash' first to save changes, or 'git reset --soft'",
        "git push --force": "Use 'git push --force-with-lease' for safer force push",
        "system prune": "Specify what to prune: 'podman container prune' or 'podman image prune'",
        "image prune -a": "Use 'podman image prune' without -a to keep tagged images",
        "DELETE without WHERE": "Add WHERE clause to target specific rows",
    }

    if result.risk_description:
        for key, alternative in alternatives.items():
            if key.lower() in result.risk_description.lower():
                return alternative
    return None


# Testing
if __name__ == "__main__":
    test_commands = [
        "ls -la",
        "rm -rf /tmp/test",
        "git reset --hard HEAD~1",
        "git push --force origin main",
        "podman system prune -a",
        "DELETE FROM users;",
        "rm -rf /",  # Should be blocked
    ]

    for cmd in test_commands:
        result = check_destructive_command(cmd)
        if result.is_destructive:
            print(f"\n{'='*60}")
            print(format_warning(result))
            alt = get_safe_alternative(result)
            if alt:
                print(f"\nSafer alternative: {alt}")
