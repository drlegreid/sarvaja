"""
Governance Sessions MCP Server
==============================
Sessions, DSM, and evidence operations.

Per RULE-012: DSP Semantic Code Structure
Per 4-Server Split Architecture (2026-01-03)
Per MCP-LOGGING-01-v1: Structured logging with metrics

Environment:
    MCP_LOG_LEVEL=DEBUG   # TRACE/DEBUG/INFO/WARNING/ERROR (default: ERROR)
"""

import time

from mcp.server.fastmcp import FastMCP

_startup_start = time.perf_counter()
mcp = FastMCP("governance-sessions")

# =============================================================================
# LOGGING SETUP
# =============================================================================

from governance.mcp_logging import get_logger, log_server_start, MCPMetrics

logger = get_logger("gov-sessions")
metrics = MCPMetrics("gov-sessions")

# =============================================================================
# REGISTER TOOLS
# =============================================================================

from governance.mcp_tools.sessions import register_session_tools
from governance.mcp_tools.dsm import register_dsm_tools
from governance.mcp_tools.evidence import register_evidence_tools

register_session_tools(mcp)
register_dsm_tools(mcp)
register_evidence_tools(mcp)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys
    from governance.mcp_tools.common import TYPEDB_HOST, TYPEDB_PORT, DATABASE_NAME

    startup_ms = (time.perf_counter() - _startup_start) * 1000
    tool_count = len(list(mcp._tool_manager._tools.keys()))

    log_server_start(logger, "gov-sessions", tool_count, version="1.25.0")
    metrics.record_startup(tool_count, startup_ms)

    print("Starting Governance Sessions MCP Server...", file=sys.stderr)
    print(f"TypeDB: {TYPEDB_HOST}:{TYPEDB_PORT}/{DATABASE_NAME}", file=sys.stderr)
    print(f"Tools: {tool_count} | Startup: {startup_ms:.0f}ms", file=sys.stderr)
    mcp.run()
