"""
Tasks MCP Tools - Orchestrator
==============================
Combines CRUD and entity linking operations for tasks.

Per RULE-012: DSP Semantic Code Structure
Per RULE-032: File size <300 lines - split into modules

Modules:
- tasks_crud.py: CRUD operations (governance_create_task, governance_get_task, etc.)
- tasks_linking.py: Entity linking (governance_task_link_session, etc.)

Created: 2024-12-26
Refactored: 2026-01-03 - Split into modules per RULE-032
"""

from governance.mcp_tools.tasks_crud import register_task_crud_tools
from governance.mcp_tools.tasks_linking import register_task_linking_tools


def register_task_tools(mcp) -> None:
    """Register all task-related MCP tools.

    This orchestrator function maintains backward compatibility
    while delegating to modular implementations.
    """
    register_task_crud_tools(mcp)
    register_task_linking_tools(mcp)
