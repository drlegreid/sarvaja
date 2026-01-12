#!/bin/bash
#
# Claude Code Settings Recovery Script (Bash Wrapper)
#
# Creates a backup of settings.local.json with timestamp suffix and restores
# to a clean minimal configuration.
#
# Usage:
#   ./recover.sh                    # Backup and restore to minimal
#   ./recover.sh --backup-only      # Only create backup
#   ./recover.sh --list             # List available backups
#   ./recover.sh --restore FILE     # Restore from specific backup
#   ./recover.sh --help             # Show help
#
# Per EPIC-006: Used when hooks cause Claude Code startup failures.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/recover.py"

show_help() {
    cat << EOF
Claude Code Settings Recovery Script

Usage:
    $(basename "$0") [OPTIONS]

Options:
    --backup-only   Only create backup, don't restore to minimal
    --restore FILE  Restore from a specific backup file
    --list          List available backup files
    --help          Show this help message

Examples:
    $(basename "$0")                              # Backup and restore minimal
    $(basename "$0") --backup-only                # Only create backup
    $(basename "$0") --list                       # List backups
    $(basename "$0") --restore settings.local.json.20260104_123456.bak

Per EPIC-006: Used when hooks cause Claude Code startup failures.
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
    echo ""
    echo "Manual recovery steps:"
    echo "1. Rename .claude/settings.local.json to .claude/settings.local.json.bak"
    echo "2. Create new .claude/settings.local.json with minimal content:"
    echo '   { "hooks": {} }'
    echo "3. Restart Claude Code"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

# Run Python script with all arguments
"$PYTHON_CMD" "$PYTHON_SCRIPT" "$@"
exit_code=$?

if [[ $exit_code -ne 0 ]]; then
    echo ""
    echo "Recovery script failed. Manual recovery steps:"
    echo "1. Rename .claude/settings.local.json to .claude/settings.local.json.bak"
    echo "2. Create new .claude/settings.local.json with minimal content:"
    echo '   { "hooks": {} }'
    echo "3. Restart Claude Code"
fi

exit $exit_code
