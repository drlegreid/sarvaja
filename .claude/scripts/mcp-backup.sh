#!/bin/bash
#
# MCP Configuration Backup Script (Bash Wrapper)
#
# Creates timestamped backups of MCP configuration files and manages restoration.
#
# Usage:
#   ./mcp-backup.sh                    # Show status and backup
#   ./mcp-backup.sh --backup-only      # Only create backup
#   ./mcp-backup.sh --list             # List available backups
#   ./mcp-backup.sh --status           # Show MCP status
#   ./mcp-backup.sh --restore FILE     # Restore from specific backup
#   ./mcp-backup.sh --help             # Show help
#
# Per R&D TOOL-009: MCP optimization for memory management.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/mcp-backup.py"

show_help() {
    cat << EOF
MCP Configuration Backup Script

Usage:
    $(basename "$0") [OPTIONS]

Options:
    --backup-only   Only create backup, don't show status
    --restore FILE  Restore from a specific backup file
    --list          List available backup files
    --status        Show current MCP configuration status
    --help          Show this help message

Examples:
    $(basename "$0")                              # Status and backup
    $(basename "$0") --list                       # List backups
    $(basename "$0") --restore mcp-backup.20260104_123456.json

Per R&D TOOL-009: MCP optimization for memory management.
EOF
}

# Check for help flag
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_help
    exit 0
fi

# Check Python is available
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "Error: Python not found in PATH"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

# Run Python script with all arguments
"$PYTHON_CMD" "$PYTHON_SCRIPT" "$@"
exit $?
