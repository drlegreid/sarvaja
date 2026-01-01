"""
Governance MCP Server - Multi-Agent Conflict Resolution
========================================================
Thin coordinator (per DSP FP + Digital Twin paradigm).

Created: 2024-12-24 (RULE-011, DECISION-005)
Refactored: 2024-12-25 (DSP Semantic Restructure)
Refactored: 2024-12-28 (GAP-FILE-007 - 897→~110 lines, 88% reduction)

Protocol: MCP (Model Context Protocol)
Backend: TypeDB 2.29.1

Structure (per RULE-012):
    mcp_tools/           - MCP tools by entity/concern
        rules.py         - Rule query/CRUD
        trust.py         - Trust score operations
        proposals.py     - Proposal/vote/dispute
        decisions.py     - Decision impact
        sessions.py      - Session evidence
        dsm.py           - DSM tracker (RULE-012)
        evidence.py      - Evidence viewing
    compat/              - Backward compatibility exports
        core.py          - Core query functions
        dsm.py           - DSM tracker exports
        sessions.py      - Session collector exports
        quality.py       - Rule quality exports
        tasks.py         - Task CRUD exports
        agents.py        - Agent CRUD exports
        documents.py     - Document viewing exports

Usage:
    python governance/mcp_server.py

Or add to MCP config:
    {
        "governance": {
            "command": "python",
            "args": ["governance/mcp_server.py"],
            "env": {"TYPEDB_HOST": "localhost", "TYPEDB_PORT": "1729"}
        }
    }
"""

from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("governance")

# =============================================================================
# REGISTER ALL TOOLS FROM mcp_tools PACKAGE
# =============================================================================

from governance.mcp_tools import register_all_tools
register_all_tools(mcp)


# =============================================================================
# BACKWARD COMPATIBILITY EXPORTS (GAP-FILE-007)
# =============================================================================
# Re-export from governance/compat/ package for backward compatibility
# These functions are used by agent/governance_ui/data_access.py and tests

from governance.compat import (
    # Core query functions
    governance_query_rules,
    governance_list_sessions,
    governance_get_session,
    governance_list_decisions,
    governance_get_decision,
    governance_list_tasks,
    governance_get_task_deps,
    governance_evidence_search,
    # DSM tracker
    dsm_start,
    dsm_advance,
    dsm_checkpoint,
    dsm_status,
    dsm_complete,
    dsm_finding,
    dsm_metrics,
    # Session collector
    session_start,
    session_decision,
    session_task,
    session_end,
    session_list,
    # Rule quality
    governance_analyze_rules,
    governance_rule_impact,
    governance_find_issues,
    # Task CRUD
    governance_create_task,
    governance_get_task,
    governance_update_task,
    governance_delete_task,
    # Agent CRUD
    governance_create_agent,
    governance_get_agent,
    governance_list_agents,
    governance_update_agent_trust,
    # Document viewing
    governance_get_document,
    governance_list_documents,
    governance_get_rule_document,
    governance_get_task_document,
)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    from governance.mcp_tools.common import TYPEDB_HOST, TYPEDB_PORT, DATABASE_NAME

    print("Starting Governance MCP Server...")
    print(f"TypeDB: {TYPEDB_HOST}:{TYPEDB_PORT}/{DATABASE_NAME}")
    print("Tools registered from governance.mcp_tools package")
    mcp.run()
