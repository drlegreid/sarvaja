"""
Governance Tasks MCP Server
===========================
Tasks, gaps, and workspace operations.

Per RULE-012: DSP Semantic Code Structure
Per 4-Server Split Architecture (2026-01-03)
Per MCP-LOGGING-01-v1: Structured logging with metrics

Environment:
    MCP_LOG_LEVEL=DEBUG   # TRACE/DEBUG/INFO/WARNING/ERROR (default: ERROR)
"""

import time

from mcp.server.fastmcp import FastMCP

_startup_start = time.perf_counter()
mcp = FastMCP("governance-tasks")

# =============================================================================
# LOGGING SETUP
# =============================================================================

from governance.mcp_logging import get_logger, log_server_start, MCPMetrics

logger = get_logger("gov-tasks")
metrics = MCPMetrics("gov-tasks")

# =============================================================================
# REGISTER TOOLS
# =============================================================================

from governance.mcp_tools.tasks import register_task_tools
from governance.mcp_tools.workspace import register_workspace_tools
from governance.mcp_tools.gaps import register_gap_tools
from governance.mcp_tools.handoff import register_handoff_tools
from governance.mcp_tools.audit import register_audit_tools

register_task_tools(mcp)
register_workspace_tools(mcp)
register_gap_tools(mcp)
register_handoff_tools(mcp)
register_audit_tools(mcp)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys
    from governance.mcp_tools.common import TYPEDB_HOST, TYPEDB_PORT, DATABASE_NAME

    startup_ms = (time.perf_counter() - _startup_start) * 1000
    tool_count = len(list(mcp._tool_manager._tools.keys()))

    log_server_start(logger, "gov-tasks", tool_count, version="1.25.0")
    metrics.record_startup(tool_count, startup_ms)

    print("Starting Governance Tasks MCP Server...", file=sys.stderr)
    print(f"TypeDB: {TYPEDB_HOST}:{TYPEDB_PORT}/{DATABASE_NAME}", file=sys.stderr)
    print(f"Tools: {tool_count} | Startup: {startup_ms:.0f}ms", file=sys.stderr)
    mcp.run()
