"""
Governance Core MCP Server
==========================
Rules, decisions, and health operations.

Per RULE-012: DSP Semantic Code Structure
Per 4-Server Split Architecture (2026-01-03)
Per MCP-LOGGING-01-v1: Structured logging with metrics

Tools:
- governance_query_rules, governance_get_rule, governance_get_dependencies, governance_find_conflicts
- governance_create_rule, governance_update_rule, governance_deprecate_rule, governance_delete_rule
- governance_list_archived_rules, governance_get_archived_rule, governance_restore_rule
- governance_get_decision_impacts
- governance_analyze_rules, governance_rule_impact, governance_find_issues
- governance_health

Usage:
    python -m governance.mcp_server_core

Environment:
    MCP_LOG_LEVEL=DEBUG   # TRACE/DEBUG/INFO/WARNING/ERROR (default: ERROR)
    MCP_LOG_FILE=path     # Log file path (default: logs/mcp.jsonl)
"""

import time

from mcp.server.fastmcp import FastMCP

# Initialize MCP server with startup timing
_startup_start = time.perf_counter()

mcp = FastMCP("governance-core")

# =============================================================================
# LOGGING SETUP
# =============================================================================

from governance.mcp_logging import get_logger, log_server_start, MCPMetrics

logger = get_logger("gov-core")
metrics = MCPMetrics("gov-core")

# =============================================================================
# REGISTER TOOLS
# =============================================================================

from governance.mcp_tools.rules import register_rule_tools
from governance.mcp_tools.decisions import register_decision_tools

# Register rule quality tools (from evidence subpackage)
try:
    from governance.mcp_tools.evidence.quality import register_quality_tools
    QUALITY_AVAILABLE = True
except ImportError:
    QUALITY_AVAILABLE = False
    logger.debug("quality_tools_unavailable", reason="import_error")

register_rule_tools(mcp)
register_decision_tools(mcp)

if QUALITY_AVAILABLE:
    register_quality_tools(mcp)

# Note: governance_health is registered via register_decision_tools()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys
    from governance.mcp_tools.common import TYPEDB_HOST, TYPEDB_PORT, DATABASE_NAME

    # Calculate startup time
    startup_ms = (time.perf_counter() - _startup_start) * 1000
    tool_count = len(list(mcp._tool_manager._tools.keys()))

    # Log startup with metrics
    log_server_start(logger, "gov-core", tool_count, version="1.25.0")
    metrics.record_startup(tool_count, startup_ms)

    # Print to stderr for Claude Code (non-JSON)
    print("Starting Governance Core MCP Server...", file=sys.stderr)
    print(f"TypeDB: {TYPEDB_HOST}:{TYPEDB_PORT}/{DATABASE_NAME}", file=sys.stderr)
    print(f"Tools: {tool_count} | Startup: {startup_ms:.0f}ms", file=sys.stderr)

    mcp.run()
