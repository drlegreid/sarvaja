"""
Governance Sessions MCP Server
==============================
Sessions, DSM, and evidence operations.

Per RULE-012: DSP Semantic Code Structure
Per 4-Server Split Architecture (2026-01-03)

Tools:
- session_start, session_decision, session_task, session_end, session_list
- session_get_tasks, session_link_rule, session_link_decision, session_link_evidence
- dsm_start, dsm_advance, dsm_checkpoint, dsm_finding, dsm_status, dsm_complete, dsm_metrics
- governance_list_sessions, governance_get_session, governance_evidence_search
- governance_get_document, governance_list_documents

Usage:
    python -m governance.mcp_server_sessions

Or add to MCP config:
    {
        "governance-sessions": {
            "command": "pythonw",
            "args": ["-m", "governance.mcp_server_sessions"],
            "env": {"TYPEDB_HOST": "localhost", "TYPEDB_PORT": "1729"}
        }
    }
"""

from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("governance-sessions")

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
    from governance.mcp_tools.common import TYPEDB_HOST, TYPEDB_PORT, DATABASE_NAME

    print("Starting Governance Sessions MCP Server...")
    print(f"TypeDB: {TYPEDB_HOST}:{TYPEDB_PORT}/{DATABASE_NAME}")
    print("Tools: Sessions, DSM, Evidence")
    mcp.run()
