"""
Governance Agents MCP Server
============================
Agents, trust, and proposals operations.

Per RULE-012: DSP Semantic Code Structure
Per 4-Server Split Architecture (2026-01-03)

Tools:
- governance_get_trust_score, governance_list_agents
- governance_create_agent, governance_get_agent, governance_update_agent_trust
- governance_propose_rule, governance_vote, governance_dispute

Usage:
    python -m governance.mcp_server_agents

Or add to MCP config:
    {
        "governance-agents": {
            "command": "pythonw",
            "args": ["-m", "governance.mcp_server_agents"],
            "env": {"TYPEDB_HOST": "localhost", "TYPEDB_PORT": "1729"}
        }
    }
"""

from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("governance-agents")

# =============================================================================
# REGISTER TOOLS
# =============================================================================

from governance.mcp_tools.agents import register_agent_tools
from governance.mcp_tools.trust import register_trust_tools
from governance.mcp_tools.proposals import register_proposal_tools

register_agent_tools(mcp)
register_trust_tools(mcp)
register_proposal_tools(mcp)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    from governance.mcp_tools.common import TYPEDB_HOST, TYPEDB_PORT, DATABASE_NAME

    print("Starting Governance Agents MCP Server...")
    print(f"TypeDB: {TYPEDB_HOST}:{TYPEDB_PORT}/{DATABASE_NAME}")
    print("Tools: Agents, Trust, Proposals")
    mcp.run()
