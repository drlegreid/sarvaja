#!/usr/bin/env python3
"""
MCP Usage Pattern Check - PostToolUse Hook.

Per GOV-MCP-FIRST-01-v1: Warn when MCP tools are underused.
Never blocks workflow (always exits 0).

Usage:
    # PostToolUse: track tool and warn if MCP underused
    python3 mcp_usage_check.py

    # SessionStart: reset state for new session
    python3 mcp_usage_check.py --reset

Created: 2026-02-12
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from checkers.mcp_usage_checker import track_tool, reset


def main() -> int:
    """Track tool call and warn if MCP-first pattern violated."""
    # Handle --reset for SessionStart
    if "--reset" in sys.argv:
        reset()
        return 0

    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    if not tool_name:
        return 0

    warning = track_tool(tool_name)
    if warning:
        sys.stderr.write(f"{warning}\n")
        sys.stderr.flush()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # Never block
