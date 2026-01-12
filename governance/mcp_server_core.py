"""
Governance Core MCP Server
==========================
Rules, decisions, and health operations.

Per RULE-012: DSP Semantic Code Structure
Per 4-Server Split Architecture (2026-01-03)

Tools:
- governance_query_rules, governance_get_rule, governance_get_dependencies, governance_find_conflicts
- governance_create_rule, governance_update_rule, governance_deprecate_rule, governance_delete_rule
- governance_list_archived_rules, governance_get_archived_rule, governance_restore_rule
- governance_get_decision_impacts
- governance_analyze_rules, governance_rule_impact, governance_find_issues
- governance_health

Usage:
    python -m governance.mcp_server_core

Or add to MCP config:
    {
        "governance-core": {
            "command": "pythonw",
            "args": ["-m", "governance.mcp_server_core"],
            "env": {"TYPEDB_HOST": "localhost", "TYPEDB_PORT": "1729"}
        }
    }
"""

from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("governance-core")

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

register_rule_tools(mcp)
register_decision_tools(mcp)

if QUALITY_AVAILABLE:
    register_quality_tools(mcp)

# Register health tool
@mcp.tool()
def governance_health() -> str:
    """
    Check governance system health (GAP-MCP-002).

    Checks both TypeDB and ChromaDB dependencies. Returns structured
    response with action_required for Claude Code integration.

    RULE-021 Compliance:
    - Level 1: Pre-operation health check
    - Level 2: Session start audit
    - Level 3: Recovery protocol with action_required

    Returns:
        JSON object with health status. If unhealthy, includes:
        - action_required: "START_SERVICES" (for Claude Code)
        - services: list of failed service names
        - recovery_hint: Docker command to fix

    Example unhealthy response:
        {
            "status": "unhealthy",
            "error": "DEPENDENCY_FAILURE",
            "action_required": "START_SERVICES",
            "services": ["typedb"],
            "recovery_hint": "docker compose up -d typedb"
        }
    """
    import json
    from governance.health import check_all_services, are_core_services_healthy, get_failed_services

    # Use shared health module for consistency (RULE-032)
    services = check_all_services()
    failed = get_failed_services(services)

    if failed:
        return json.dumps({
            "status": "unhealthy",
            "error": "DEPENDENCY_FAILURE",
            "action_required": "START_SERVICES",
            "services": failed,
            "recovery_hint": "podman compose --profile cpu up -d " + " ".join(failed)
        }, indent=2)

    return json.dumps({
        "status": "healthy",
        "services": {
            name: status.status for name, status in services.items()
        }
    }, indent=2)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    from governance.mcp_tools.common import TYPEDB_HOST, TYPEDB_PORT, DATABASE_NAME

    print("Starting Governance Core MCP Server...")
    print(f"TypeDB: {TYPEDB_HOST}:{TYPEDB_PORT}/{DATABASE_NAME}")
    print("Tools: Rules, Decisions, Quality, Health")
    mcp.run()
