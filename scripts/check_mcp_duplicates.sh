#!/bin/bash
# MCP Duplicate Tool Detection - Pre-commit Guard
# Per GAP-CONTEXT-EFFICIENCY-001, TACTIC-2-A
#
# Prevents commits when duplicate MCP tools are detected.
# This guard prevented a 25% context burn incident (2026-01-17).
#
# Usage:
#   scripts/check_mcp_duplicates.sh          # Standalone check
#   ln -sf ../../scripts/check_mcp_duplicates.sh .git/hooks/pre-commit
#
# Exit codes:
#   0 - No duplicates found
#   1 - Duplicates detected (commit blocked)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[MCP Pre-commit] Checking for duplicate tools...${NC}"

# Run Python checker if available
if command -v python3 &> /dev/null; then
    # Run directly with Python
    cd "$PROJECT_ROOT"
    python3 -c "
import sys
sys.path.insert(0, '.claude')
from hooks.checkers.mcp_preflight import MCPPreflightChecker, check_mcp_preflight

result = check_mcp_preflight()
if not result.success:
    print('[MCP Pre-commit] FAILED:', result.message)
    for issue in result.details.get('issues', []):
        print('  -', issue)
    sys.exit(1)
else:
    print('[MCP Pre-commit] OK: No duplicate tools found')
    print(f'  Modules: {result.details.get(\"modules_checked\", 0)}')
    print(f'  Tools: {result.details.get(\"tools_scanned\", 0)}')
    sys.exit(0)
" 2>&1

    exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}[MCP Pre-commit] PASSED${NC}"
        exit 0
    else
        echo -e "${RED}[MCP Pre-commit] BLOCKED - Fix duplicate tools before committing${NC}"
        exit 1
    fi
else
    # Fallback: simple grep check for obvious duplicates
    echo -e "${YELLOW}[MCP Pre-commit] Python not available, using grep fallback${NC}"

    TOOL_DIR="$PROJECT_ROOT/governance/mcp_tools"
    if [ -d "$TOOL_DIR" ]; then
        # Find all governance_* and session_* function definitions
        DUPS=$(grep -rh "^def governance_\|^def session_" "$TOOL_DIR" 2>/dev/null | \
               sed 's/(.*//g' | sort | uniq -d)

        if [ -n "$DUPS" ]; then
            echo -e "${RED}[MCP Pre-commit] POTENTIAL DUPLICATES FOUND:${NC}"
            echo "$DUPS"
            exit 1
        fi
    fi

    echo -e "${GREEN}[MCP Pre-commit] PASSED (grep check)${NC}"
    exit 0
fi
