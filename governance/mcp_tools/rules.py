"""
Rule MCP Tools - Orchestrator
=============================
Combines query, CRUD, and archive operations for governance rules.

Per RULE-012: DSP Semantic Code Structure
Per RULE-032: File size <300 lines - split into modules

Modules:
- rules_query.py: Query operations (governance_query_rules, governance_get_rule, etc.)
- rules_crud.py: CRUD operations (create, update, deprecate, delete)
- rules_archive.py: Archive operations (list, get, restore)

Created: 2024-12-26
Refactored: 2026-01-03 - Split into modules per RULE-032
"""

from governance.mcp_tools.rules_query import register_rule_query_tools
from governance.mcp_tools.rules_crud import register_rule_crud_tools
from governance.mcp_tools.rules_archive import register_rule_archive_tools


def register_rule_tools(mcp) -> None:
    """Register all rule-related MCP tools.

    This orchestrator function maintains backward compatibility
    while delegating to modular implementations.
    """
    register_rule_query_tools(mcp)
    register_rule_crud_tools(mcp)
    register_rule_archive_tools(mcp)
