"""
Session Evidence MCP Tools - Orchestrator
==========================================
Combines core session and entity linking operations.

Per RULE-012: DSP Semantic Code Structure
Per RULE-032: File size <300 lines - split into modules

Modules:
- sessions_core.py: Core operations (session_start, session_end, etc.)
- sessions_linking.py: Entity linking (session_link_rule, session_link_decision, etc.)
- sessions_intent.py: Intent/outcome capture (RD-INTENT)
- sessions_evidence.py: Test evidence compression (EPIC-TEST-COMPRESS-001)

Created: 2024-12-26
Refactored: 2026-01-03 - Split into modules per RULE-032
Updated: 2026-01-10 - Added sessions_intent per RD-INTENT
"""

from governance.mcp_tools.sessions_core import register_session_core_tools
from governance.mcp_tools.sessions_linking import register_session_linking_tools
from governance.mcp_tools.sessions_intent import register_session_intent_tools
from governance.mcp_tools.sessions_evidence import register_session_evidence_tools


def register_session_tools(mcp) -> None:
    """Register all session-related MCP tools.

    This orchestrator function maintains backward compatibility
    while delegating to modular implementations.
    """
    register_session_core_tools(mcp)
    register_session_linking_tools(mcp)
    register_session_intent_tools(mcp)
    register_session_evidence_tools(mcp)
