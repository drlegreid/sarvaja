"""
Shell Command Guidelines Tests
Created: 2026-01-03
Updated: 2026-01-13 - Point to SHELL-GUIDE.md per doc refactor
Per RULE-023: Test Before Ship
Per P11.3: Shell MCP documentation validation

Tests that validate shell command documentation and prevent
mixing Bash/PowerShell syntax.

Note: Shell documentation moved from CLAUDE.md to docs/SHELL-GUIDE.md
per RULE-032 (file size limits) and modularization.
"""
import pytest
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"
SHELL_GUIDE = PROJECT_ROOT / "docs" / "SHELL-GUIDE.md"


class TestShellDocumentation:
    """Validate shell command documentation exists in SHELL-GUIDE.md."""

    @pytest.mark.unit
    def test_claude_md_exists(self):
        """CLAUDE.md must exist."""
        assert CLAUDE_MD.exists(), "CLAUDE.md not found"

    @pytest.mark.unit
    def test_shell_guide_exists(self):
        """SHELL-GUIDE.md must exist."""
        assert SHELL_GUIDE.exists(), "docs/SHELL-GUIDE.md not found"

    @pytest.mark.unit
    def test_claude_md_links_to_shell_guide(self):
        """CLAUDE.md must link to SHELL-GUIDE.md."""
        content = CLAUDE_MD.read_text(encoding="utf-8")
        assert "SHELL-GUIDE.md" in content or "Shell Guide" in content, \
            "CLAUDE.md should link to Shell Guide"

    @pytest.mark.unit
    def test_bash_tool_documented(self):
        """Bash tool usage must be documented in SHELL-GUIDE.md."""
        content = SHELL_GUIDE.read_text(encoding="utf-8")
        assert "Bash" in content and "Linux" in content, \
            "Bash tool documentation missing from SHELL-GUIDE.md"

    @pytest.mark.unit
    def test_powershell_mcp_documented(self):
        """PowerShell MCP usage must be documented in SHELL-GUIDE.md."""
        content = SHELL_GUIDE.read_text(encoding="utf-8")
        assert "mcp__powershell__run_powershell" in content or "PowerShell MCP" in content, \
            "PowerShell MCP documentation missing from SHELL-GUIDE.md"

    @pytest.mark.unit
    def test_common_pitfalls_documented(self):
        """Common shell pitfalls must be documented in SHELL-GUIDE.md."""
        content = SHELL_GUIDE.read_text(encoding="utf-8")
        # Check for common mistake documentation
        assert "Start-Sleep" in content, "Start-Sleep pitfall not documented"
        assert "sleep" in content, "sleep equivalent not documented"


class TestShellCommandEquivalents:
    """Validate shell command equivalent documentation in SHELL-GUIDE.md."""

    @pytest.mark.unit
    def test_wait_command_documented(self):
        """Wait/sleep command equivalents must be documented."""
        content = SHELL_GUIDE.read_text(encoding="utf-8")
        # Bash: sleep N, PowerShell: Start-Sleep -Seconds N
        assert "sleep" in content.lower(), "sleep command not documented"

    @pytest.mark.unit
    def test_http_request_documented(self):
        """HTTP request command equivalents must be documented."""
        content = SHELL_GUIDE.read_text(encoding="utf-8")
        # Bash: curl, PowerShell: Invoke-WebRequest
        assert "curl" in content, "curl not documented"
        assert "Invoke-WebRequest" in content, "Invoke-WebRequest not documented"

    @pytest.mark.unit
    def test_head_tail_documented(self):
        """Head/tail command equivalents must be documented."""
        content = SHELL_GUIDE.read_text(encoding="utf-8")
        # Bash: head -n N, PowerShell: Select-Object -First N
        assert "head" in content, "head command not documented"
        assert "tail" in content, "tail command not documented"
        assert "Select-Object" in content, "Select-Object not documented"

    @pytest.mark.unit
    def test_last_n_lines_documented(self):
        """Last N lines equivalents must be documented (common pitfall)."""
        content = SHELL_GUIDE.read_text(encoding="utf-8")
        # This was a common mistake: using Select-Object -Last in Bash
        assert "Last N lines" in content or "Last 30" in content, \
            "Last N lines equivalents not documented - common pitfall!"
        assert "tail -n" in content, "tail -n not documented for last N lines"
        assert "Select-Object -Last" in content, "Select-Object -Last not documented"


class TestCodebaseShellUsage:
    """Validate codebase doesn't mix shell syntaxes incorrectly."""

    @pytest.mark.unit
    def test_no_powershell_in_bash_scripts(self):
        """Bash scripts should not contain PowerShell-only commands."""
        powershell_commands = [
            r'\bStart-Sleep\b',
            r'\bSelect-Object\b',
            r'\bInvoke-WebRequest\b',
            r'\bGet-ChildItem\b',
            r'\bSet-Location\b',
        ]

        # Check shell scripts in project
        for sh_file in PROJECT_ROOT.glob("**/*.sh"):
            content = sh_file.read_text(encoding="utf-8", errors="ignore")
            for cmd_pattern in powershell_commands:
                matches = re.findall(cmd_pattern, content, re.IGNORECASE)
                assert not matches, \
                    f"PowerShell command {cmd_pattern} found in bash script {sh_file}"

    @pytest.mark.unit
    def test_no_bash_only_in_ps1_scripts(self):
        """PowerShell scripts should not use bash-only syntax."""
        bash_patterns = [
            r'^sleep\s+\d+',  # sleep N (without $)
            r'\|.*head\s+-n',  # piping to head
            r'\|.*tail\s+-n',  # piping to tail
        ]

        # Check PowerShell scripts in project
        for ps1_file in PROJECT_ROOT.glob("**/*.ps1"):
            content = ps1_file.read_text(encoding="utf-8", errors="ignore")
            for pattern in bash_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                # Allow if it's in a comment or docker exec
                filtered = [m for m in matches if "docker" not in content[max(0, content.find(m)-50):content.find(m)]]
                assert not filtered, \
                    f"Bash-only syntax {pattern} found in PowerShell script {ps1_file}"


class TestDockerComposeShellUsage:
    """Validate docker-compose.yml uses correct shell syntax."""

    @pytest.mark.unit
    def test_docker_compose_uses_bash_syntax(self):
        """Docker healthchecks should use bash/sh syntax, not PowerShell."""
        docker_compose = PROJECT_ROOT / "docker-compose.yml"
        if not docker_compose.exists():
            pytest.skip("docker-compose.yml not found")

        content = docker_compose.read_text(encoding="utf-8")

        # PowerShell commands that shouldn't be in healthchecks
        powershell_in_docker = [
            "Start-Sleep",
            "Invoke-WebRequest",
            "Select-Object",
        ]

        for cmd in powershell_in_docker:
            assert cmd not in content, \
                f"PowerShell command '{cmd}' found in docker-compose.yml healthcheck"
