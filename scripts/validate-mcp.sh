#!/bin/bash
# MCP Server Validation Script
# Per GAP-MCP-VALIDATE-001: Validate MCP servers before restart
#
# Usage: ./scripts/validate-mcp.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== MCP Server Validation ==="
echo ""

# Use the project venv (or sarvaja venv as fallback)
if [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    PYTHON="$PROJECT_DIR/.venv/bin/python"
elif [ -f "$HOME/.venv/sarvaja/bin/python" ]; then
    PYTHON="$HOME/.venv/sarvaja/bin/python"
else
    echo "ERROR: No Python venv found"
    exit 1
fi
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

INIT_MSG='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"validator","version":"1.0"}}}'

FAILED=0
PASSED=0

# Test a single MCP server module
test_mcp() {
  local name="$1"
  local module="$2"

  local result
  result=$(timeout 8 bash -c "{ echo '$INIT_MSG'; sleep 2; } | $PYTHON -m $module" 2>/dev/null)

  if echo "$result" | grep -q '"result"'; then
    echo "✓ $name: OK"
    ((PASSED++))
  else
    echo "✗ $name: FAILED"
    ((FAILED++))
  fi
}

# Test all governance servers
test_mcp "gov-core" "governance.mcp_server_core"
test_mcp "gov-agents" "governance.mcp_server_agents"
test_mcp "gov-sessions" "governance.mcp_server_sessions"
test_mcp "gov-tasks" "governance.mcp_server_tasks"
test_mcp "claude-mem" "claude_mem.mcp_server"

echo ""
echo "=== Results: $PASSED passed, $FAILED failed ==="

if [ $FAILED -gt 0 ]; then
  echo ""
  echo "WARNING: Some MCP servers failed validation!"
  exit 1
fi

echo "All MCP servers validated successfully."
exit 0
