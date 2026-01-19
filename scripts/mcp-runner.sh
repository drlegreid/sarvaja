#!/bin/bash
# MCP Runner Script - Optimized for Claude Code
# Usage: mcp-runner.sh <module-name>
# Example: mcp-runner.sh governance.mcp_server_core
#
# Per GAP-MCP-VALIDATE-001: Optimized startup for Claude Code race condition
# Per WORKFLOW-SHELL-01-v1: Use python3, not python

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MODULE="$1"

# Optional: Kill zombie PYTHON processes for THIS module
# Set MCP_CLEANUP=1 to enable pre-start cleanup
if [ "${MCP_CLEANUP:-0}" = "1" ]; then
    for pid in $(pgrep -f "python.*$MODULE" 2>/dev/null); do
        if ps -p "$pid" -o comm= 2>/dev/null | grep -q python; then
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
fi

# Find Python - prefer project venv, fallback to sarvaja venv
# Direct path avoids slow source activation (~50-100ms savings)
if [ -x "$PROJECT_DIR/.venv/bin/python3" ]; then
    PYTHON="$PROJECT_DIR/.venv/bin/python3"
elif [ -x "$HOME/.venv/sarvaja/bin/python3" ]; then
    PYTHON="$HOME/.venv/sarvaja/bin/python3"
else
    # Fallback to system python3
    PYTHON="python3"
fi

export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
exec "$PYTHON" -m "$MODULE"
