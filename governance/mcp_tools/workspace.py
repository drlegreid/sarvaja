"""
MCP Tools for Workspace Operations - Coordinator Module.

Per P10.10: Workspace Task Capture.
Per P10.8: TypeDB-Filesystem Rule Linking.
Per GAP-MCP-008: Semantic Rule ID Support.
Per DOC-SIZE-01-v1: Modularized into sub-modules.

Sub-modules:
- workspace_tasks.py: Task scanning tools (3 tools)
- workspace_rules.py: Rule-document linking tools (4 tools)
- workspace_sync.py: Sync status tools (2 tools)

Total: 9 tools registered via this coordinator.
"""

import logging

logger = logging.getLogger(__name__)


def register_workspace_tools(mcp) -> None:
    """
    Register all workspace-related MCP tools.

    Delegates to sub-modules per DOC-SIZE-01-v1 modularization.
    """
    from governance.mcp_tools.workspace_tasks import register_workspace_task_tools
    from governance.mcp_tools.workspace_rules import register_workspace_rule_tools
    from governance.mcp_tools.workspace_sync import register_workspace_sync_tools

    # Register task scanning tools (3 tools)
    register_workspace_task_tools(mcp)

    # Register rule-document linking tools (4 tools)
    register_workspace_rule_tools(mcp)

    # Register sync status tools (2 tools)
    register_workspace_sync_tools(mcp)

    logger.info("Registered all workspace MCP tools (9 tools via 3 sub-modules)")
