"""
Governance Tasks MCP Server
===========================
Tasks, gaps, and workspace operations.

Per RULE-012: DSP Semantic Code Structure
Per 4-Server Split Architecture (2026-01-03)

Tools:
- governance_create_task, governance_get_task, governance_update_task
- governance_delete_task, governance_list_all_tasks
- governance_task_link_session, governance_task_link_rule, governance_task_link_evidence
- governance_task_get_evidence
- workspace_scan_tasks, workspace_capture_tasks, workspace_list_sources
- workspace_scan_rule_documents, workspace_link_rules_to_documents
- governance_get_backlog, governance_gap_summary, governance_get_critical_gaps
- governance_unified_backlog
- governance_create_handoff, governance_get_pending_handoffs
- governance_complete_handoff, governance_get_handoff
- governance_route_task_to_agent
- governance_query_audit, governance_audit_summary, governance_entity_audit_trail
- governance_trace_correlation

Usage:
    python -m governance.mcp_server_tasks

Or add to MCP config:
    {
        "governance-tasks": {
            "command": "pythonw",
            "args": ["-m", "governance.mcp_server_tasks"],
            "env": {"TYPEDB_HOST": "localhost", "TYPEDB_PORT": "1729"}
        }
    }
"""

from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("governance-tasks")

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
    from governance.mcp_tools.common import TYPEDB_HOST, TYPEDB_PORT, DATABASE_NAME

    print("Starting Governance Tasks MCP Server...")
    print(f"TypeDB: {TYPEDB_HOST}:{TYPEDB_PORT}/{DATABASE_NAME}")
    print("Tools: Tasks, Workspace, Gaps")
    mcp.run()
