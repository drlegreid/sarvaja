#!/bin/bash
# MCP Zombie Cleanup - Run before starting IDE
# Per GAP-MCP-VALIDATE-001: Prevents zombie process conflicts

echo "=== MCP Zombie Cleanup ==="

# Count before
before=$(pgrep -cf "mcp_server" 2>/dev/null || echo 0)
echo "Before: $before MCP processes"

# Kill all MCP server processes
pkill -9 -f "governance.mcp_server" 2>/dev/null || true
pkill -9 -f "claude_mem.mcp_server" 2>/dev/null || true

sleep 0.5

# Count after
after=$(pgrep -cf "mcp_server" 2>/dev/null || echo 0)
echo "After: $after MCP processes"

if [ "$before" -gt 0 ]; then
    echo "Cleaned $((before - after)) zombie processes"
fi

echo "Ready for IDE startup"
