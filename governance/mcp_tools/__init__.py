"""
MCP Tools Package
=================
Modular MCP tool implementations for Governance Server.

Per RULE-012: DSP Semantic Code Structure
Per FP + Digital Twin Paradigm

Package Structure (by entity/concern):
    rules.py       - Rule query and CRUD operations
    trust.py       - Trust score operations
    proposals.py   - Proposal/vote/dispute operations
    decisions.py   - Decision impact operations
    sessions.py    - Session evidence operations
    dsm.py         - DSM tracker operations (RULE-012)
    evidence.py    - Evidence viewing operations

Main Server:
    governance/mcp_server.py - Thin coordinator (imports + registration)

Usage:
    from governance.mcp_tools import register_all_tools
    register_all_tools(mcp)
"""

from .rules import register_rule_tools
from .trust import register_trust_tools
from .proposals import register_proposal_tools
from .decisions import register_decision_tools
from .sessions import register_session_tools
from .dsm import register_dsm_tools
from .evidence import register_evidence_tools


def register_all_tools(mcp) -> None:
    """
    Register all MCP tools with the server.

    Args:
        mcp: FastMCP server instance
    """
    register_rule_tools(mcp)
    register_trust_tools(mcp)
    register_proposal_tools(mcp)
    register_decision_tools(mcp)
    register_session_tools(mcp)
    register_dsm_tools(mcp)
    register_evidence_tools(mcp)


__all__ = [
    'register_all_tools',
    'register_rule_tools',
    'register_trust_tools',
    'register_proposal_tools',
    'register_decision_tools',
    'register_session_tools',
    'register_dsm_tools',
    'register_evidence_tools',
]
