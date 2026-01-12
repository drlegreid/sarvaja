"""
Level 3: E2E Tests - Full Claude Code integration.

Run: python -m pytest .claude/hooks/tests/test_level3_e2e.py -v

Prerequisites:
- Podman services running (migrated from Docker 2026-01-09)
- All hooks configured in settings.local.json

Optional (for TestClaudeCodeCLI):
- Claude Code CLI installed SEPARATELY from VS Code extension
- Install: npm install -g @anthropic-ai/claude-code
- Verify: claude --version

NOTE: The VS Code extension does NOT expose the `claude` CLI command.
      The CLI must be installed independently for E2E CLI tests.
      See: https://code.claude.com/docs/en/setup
"""

import concurrent.futures
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).parent.parent
HEALTHCHECK_SCRIPT = HOOKS_DIR / "healthcheck.py"
ENTROPY_SCRIPT = HOOKS_DIR / "entropy_monitor.py"


class TestClaudeCodeCompatibility:
    """Tests for Claude Code hook contract compliance."""

    def test_healthcheck_valid_json_output(self):
        """Healthcheck produces valid JSON for Claude Code."""
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, "Hook must exit 0"
        output = json.loads(result.stdout)
        assert "hookSpecificOutput" in output

    def test_healthcheck_event_name(self):
        """Healthcheck has correct hookEventName."""
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = json.loads(result.stdout)
        hook_output = output["hookSpecificOutput"]
        assert hook_output.get("hookEventName") == "SessionStart"

    def test_entropy_valid_json_output(self):
        """Entropy monitor produces valid JSON."""
        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert isinstance(output, dict)

    def test_entropy_event_name(self):
        """Entropy monitor uses PostToolUse event."""
        # Set up state to trigger warning
        state_file = HOOKS_DIR / ".entropy_state.json"
        state = {
            "session_start": "2026-01-01T00:00:00",
            "session_hash": "TEST",
            "tool_count": 49,  # Will be 50 after increment
            "check_count": 0,
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
        if "hookSpecificOutput" in output:
            hook_output = output["hookSpecificOutput"]
            assert hook_output.get("hookEventName") == "PostToolUse"


class TestConcurrentExecution:
    """Tests for hook behavior under concurrent execution."""

    def test_hooks_handle_concurrent_calls(self):
        """Hooks handle rapid concurrent execution."""
        def run_hook():
            return subprocess.run(
                [sys.executable, str(HEALTHCHECK_SCRIPT)],
                capture_output=True,
                text=True,
                timeout=10
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_hook) for _ in range(3)]
            results = [f.result() for f in futures]

        for result in results:
            assert result.returncode == 0
            json.loads(result.stdout)  # Valid JSON

    def test_state_integrity_under_load(self):
        """State files maintain integrity under concurrent writes."""
        state_file = HOOKS_DIR / ".healthcheck_state.json"

        # Run multiple times rapidly
        for _ in range(5):
            subprocess.run(
                [sys.executable, str(HEALTHCHECK_SCRIPT)],
                capture_output=True,
                timeout=10
            )

        # State should be valid
        with open(state_file) as f:
            state = json.load(f)

        assert "master_hash" in state
        assert state["check_count"] >= 5


class TestResolutionPaths:
    """Tests for resolution path injection."""

    def test_health_failure_includes_resolution(self):
        """Health failures include actionable resolution paths."""
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]

        # If DOWN, should have resolution
        if "DOWN" in context:
            has_resolution = (
                "deploy.ps1" in context or
                "podman compose" in context.lower() or
                "docker compose" in context.lower() or  # backward compat
                "Recovery" in context or
                "Resolution" in context
            )
            assert has_resolution, "Missing resolution for failure"

    def test_entropy_high_includes_save_hint(self):
        """High entropy includes /save resolution."""
        state_file = HOOKS_DIR / ".entropy_state.json"
        state = {
            "session_start": "2026-01-01T00:00:00",
            "session_hash": "HIGH",
            "tool_count": 119,
            "check_count": 0,
            "warnings_shown": 1,
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
        if "hookSpecificOutput" in output:
            context = output["hookSpecificOutput"].get("additionalContext", "")
            if "ENTROPY HIGH" in context:
                assert "/save" in context


@pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Skip Claude Code spawn in CI"
)
class TestClaudeCodeCLI:
    """
    Tests that require Claude Code CLI (not VS Code extension).

    The CLI must be installed separately:
        npm install -g @anthropic-ai/claude-code

    These tests FAIL (not skip) when CLI is missing to ensure
    full E2E coverage is achieved.

    Reference: https://code.claude.com/docs/en/setup
    """

    def test_claude_cli_accessible(self):
        """
        Claude Code CLI is installed and accessible.

        Verifies the standalone CLI is available via `claude --version`.
        This is SEPARATE from the VS Code extension installation.

        FAILS if CLI not installed (install: npm install -g @anthropic-ai/claude-code)
        """
        # On Windows, npm global bin may not be in subprocess PATH
        # Check both direct command and npm global path
        claude_cmd = "claude"

        if sys.platform == "win32":
            # Try npm global path on Windows
            npm_prefix = os.environ.get("APPDATA", "")
            if npm_prefix:
                npm_bin = Path(npm_prefix) / "npm" / "claude.cmd"
                if npm_bin.exists():
                    claude_cmd = str(npm_bin)

        try:
            result = subprocess.run(
                [claude_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=30,
                shell=(sys.platform == "win32")  # Use shell on Windows for PATH resolution
            )
            # Verify it runs and returns version
            assert result.returncode == 0, f"claude --version failed: {result.stderr}"
            assert result.stdout.strip(), "claude --version returned empty output"
        except FileNotFoundError:
            pytest.fail(
                "Claude Code CLI not installed. "
                "Install: npm install -g @anthropic-ai/claude-code"
            )
