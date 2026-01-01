"""
PowerShell MCP Tools
====================
Agno Toolkit wrapping PowerShell MCP tools for DevOps automation.

Per RULE-007: PowerShell MCP is Tier 2 (recommended)
Per GAP-FILE-011: Extracted from external_mcp_tools.py

Created: 2024-12-28
"""

import json
from typing import Optional
from dataclasses import dataclass

from .common import tool, Toolkit


@dataclass
class PowerShellConfig:
    """Configuration for PowerShell MCP tools."""
    timeout: int = 300  # 5 minutes default
    working_directory: Optional[str] = None


class PowerShellTools(Toolkit):
    """
    Agno Toolkit wrapping PowerShell MCP tools for DevOps automation.

    Provides PowerShell execution capabilities for agents.
    Per RULE-007: PowerShell MCP is Tier 2 (recommended).

    Available tools:
        - run_script: Execute PowerShell code
        - run_command: Run a single PowerShell command
    """

    def __init__(self, config: Optional[PowerShellConfig] = None):
        super().__init__(name="powershell")
        self.config = config or PowerShellConfig()

        # Register tools
        self.register(self.run_script)
        self.register(self.run_command)

    @tool
    def run_script(self, code: str, timeout: Optional[int] = None) -> str:
        """
        Execute PowerShell code.

        Args:
            code: PowerShell code to execute (max 10,000 chars)
            timeout: Timeout in seconds (default 300)

        Returns:
            JSON with execution output
        """
        # In production, would call mcp__powershell__run_powershell
        return json.dumps({
            "action": "run_script",
            "code_length": len(code),
            "timeout": timeout or self.config.timeout,
            "status": "simulated",
            "message": "Would execute PowerShell script"
        })

    @tool
    def run_command(self, command: str) -> str:
        """
        Run a single PowerShell command.

        Args:
            command: PowerShell command to run

        Returns:
            JSON with command output
        """
        # Wrapper for run_script with single command
        return self.run_script(command)
