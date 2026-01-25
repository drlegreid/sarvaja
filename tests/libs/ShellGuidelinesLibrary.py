"""
Robot Framework Library for Shell Command Guidelines Tests.

Per RULE-023: Test Before Ship
Per P11.3: Shell MCP documentation validation
Migrated from tests/test_shell_guidelines.py
"""
from pathlib import Path
from robot.api.deco import keyword


class ShellGuidelinesLibrary:
    """Library for testing shell command documentation."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.claude_md = self.project_root / "CLAUDE.md"
        self.shell_guide = self.project_root / "docs" / "SHELL-GUIDE.md"

    # =============================================================================
    # Shell Documentation Tests
    # =============================================================================

    @keyword("Claude MD Exists")
    def claude_md_exists(self):
        """CLAUDE.md must exist."""
        return {"exists": self.claude_md.exists()}

    @keyword("Shell Guide Exists")
    def shell_guide_exists(self):
        """SHELL-GUIDE.md must exist."""
        return {"exists": self.shell_guide.exists()}

    @keyword("Claude MD Links To Shell Guide")
    def claude_md_links_to_shell_guide(self):
        """CLAUDE.md must link to SHELL-GUIDE.md."""
        if not self.claude_md.exists():
            return {"skipped": True, "reason": "CLAUDE.md not found"}

        content = self.claude_md.read_text(encoding="utf-8")
        has_link = "SHELL-GUIDE.md" in content or "Shell Guide" in content

        return {"has_link": has_link}

    @keyword("Bash Tool Documented")
    def bash_tool_documented(self):
        """Bash tool usage must be documented in SHELL-GUIDE.md."""
        if not self.shell_guide.exists():
            return {"skipped": True, "reason": "SHELL-GUIDE.md not found"}

        content = self.shell_guide.read_text(encoding="utf-8")
        has_bash = "Bash" in content and "Linux" in content

        return {"documented": has_bash}

    @keyword("PowerShell MCP Documented")
    def powershell_mcp_documented(self):
        """PowerShell MCP usage must be documented in SHELL-GUIDE.md."""
        if not self.shell_guide.exists():
            return {"skipped": True, "reason": "SHELL-GUIDE.md not found"}

        content = self.shell_guide.read_text(encoding="utf-8")
        has_ps = "mcp__powershell__run_powershell" in content or "PowerShell MCP" in content

        return {"documented": has_ps}

    @keyword("Common Pitfalls Documented")
    def common_pitfalls_documented(self):
        """Common shell pitfalls must be documented in SHELL-GUIDE.md."""
        if not self.shell_guide.exists():
            return {"skipped": True, "reason": "SHELL-GUIDE.md not found"}

        content = self.shell_guide.read_text(encoding="utf-8")

        return {
            "has_start_sleep": "Start-Sleep" in content,
            "has_sleep": "sleep" in content
        }

    # =============================================================================
    # Shell Command Equivalents Tests
    # =============================================================================

    @keyword("Wait Command Documented")
    def wait_command_documented(self):
        """Wait/sleep command equivalents must be documented."""
        if not self.shell_guide.exists():
            return {"skipped": True, "reason": "SHELL-GUIDE.md not found"}

        content = self.shell_guide.read_text(encoding="utf-8")

        return {"documented": "sleep" in content.lower()}

    @keyword("HTTP Request Documented")
    def http_request_documented(self):
        """HTTP request command equivalents must be documented."""
        if not self.shell_guide.exists():
            return {"skipped": True, "reason": "SHELL-GUIDE.md not found"}

        content = self.shell_guide.read_text(encoding="utf-8")

        return {
            "has_curl": "curl" in content,
            "has_invoke_webrequest": "Invoke-WebRequest" in content
        }

    @keyword("Head Tail Documented")
    def head_tail_documented(self):
        """Head/tail command equivalents must be documented."""
        if not self.shell_guide.exists():
            return {"skipped": True, "reason": "SHELL-GUIDE.md not found"}

        content = self.shell_guide.read_text(encoding="utf-8")

        return {
            "has_head": "head" in content,
            "has_tail": "tail" in content,
            "has_select_object": "Select-Object" in content
        }

    @keyword("Last N Lines Documented")
    def last_n_lines_documented(self):
        """Last N lines equivalents must be documented (common pitfall)."""
        if not self.shell_guide.exists():
            return {"skipped": True, "reason": "SHELL-GUIDE.md not found"}

        content = self.shell_guide.read_text(encoding="utf-8")

        return {
            "has_context": "Last N lines" in content or "Last 30" in content,
            "has_tail_n": "tail -n" in content,
            "has_select_last": "Select-Object -Last" in content
        }

    # =============================================================================
    # Codebase Shell Usage Tests
    # =============================================================================

    @keyword("No PowerShell In Bash Scripts")
    def no_powershell_in_bash_scripts(self):
        """Bash scripts should not contain PowerShell-only commands."""
        import re

        powershell_commands = [
            r'\bStart-Sleep\b',
            r'\bSelect-Object\b',
            r'\bInvoke-WebRequest\b',
            r'\bGet-ChildItem\b',
            r'\bSet-Location\b',
        ]

        violations = []
        for sh_file in self.project_root.glob("**/*.sh"):
            try:
                content = sh_file.read_text(encoding="utf-8", errors="ignore")
                for cmd_pattern in powershell_commands:
                    matches = re.findall(cmd_pattern, content, re.IGNORECASE)
                    if matches:
                        violations.append(f"{sh_file.name}: {cmd_pattern}")
            except Exception:
                pass

        return {
            "no_violations": len(violations) == 0,
            "violation_count": len(violations)
        }

    @keyword("Docker Compose Uses Bash Syntax")
    def docker_compose_uses_bash_syntax(self):
        """Docker healthchecks should use bash/sh syntax, not PowerShell."""
        docker_compose = self.project_root / "docker-compose.yml"
        if not docker_compose.exists():
            return {"skipped": True, "reason": "docker-compose.yml not found"}

        content = docker_compose.read_text(encoding="utf-8")

        powershell_in_docker = ["Start-Sleep", "Invoke-WebRequest", "Select-Object"]
        violations = [cmd for cmd in powershell_in_docker if cmd in content]

        return {
            "no_powershell": len(violations) == 0,
            "violation_count": len(violations)
        }
