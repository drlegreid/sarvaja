"""
Robot Framework Library for Claude Code Hooks Tests
Migrated from tests/test_claude_hooks.py

Per GAP-MCP-003: Verify SessionStart hook context injection
Per EPIC-006: Entropy Monitor for SLEEP Mode Automation

REFACTORED per DOC-SIZE-01-v1: This file is now a facade that imports from:
- ClaudeHooksHealthcheckLibrary.py (Healthcheck Output, State, Detection, Frankel Hash)
- ClaudeHooksEntropyLibrary.py (Entropy Output, State, Warnings, Non-Blocking)
- ClaudeHooksE2ELibrary.py (Module Imports, Claude Code Compatibility)
"""

from ClaudeHooksHealthcheckLibrary import ClaudeHooksHealthcheckLibrary
from ClaudeHooksEntropyLibrary import ClaudeHooksEntropyLibrary
from ClaudeHooksE2ELibrary import ClaudeHooksE2ELibrary


class ClaudeHooksLibrary(
    ClaudeHooksHealthcheckLibrary,
    ClaudeHooksEntropyLibrary,
    ClaudeHooksE2ELibrary
):
    """
    Facade library combining all Claude Code hooks test modules.

    Inherits from:
    - ClaudeHooksHealthcheckLibrary: Healthcheck output, state, detection, frankel hash
    - ClaudeHooksEntropyLibrary: Entropy output, state, warnings, non-blocking
    - ClaudeHooksE2ELibrary: Module imports, Claude Code compatibility

    Use individual libraries for focused tests or this facade for full coverage.
    """

    ROBOT_LIBRARY_SCOPE = 'SUITE'
