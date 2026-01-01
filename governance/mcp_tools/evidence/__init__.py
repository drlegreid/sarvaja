"""
Evidence MCP Tools Package
==========================
Modular evidence viewing operations per RULE-012 and GAP-FILE-008.

Original: governance/mcp_tools/evidence.py (870 lines)
Extracted: 6 domain modules (~100-200 lines each)

Modules:
- sessions: Session listing and retrieval
- decisions: Decision listing and retrieval
- tasks: Task listing and dependency tracking
- search: Evidence semantic search
- quality: Rule quality analysis tools
- documents: Document viewing tools

Created: 2024-12-28 per GAP-FILE-008
"""

from .sessions import register_session_tools
from .decisions import register_decision_tools
from .tasks import register_task_tools
from .search import register_search_tools
from .quality import register_quality_tools
from .documents import register_document_tools

# Re-export common constants for backward compatibility
from .common import (
    EVIDENCE_DIR,
    DOCS_DIR,
    BACKLOG_DIR,
    RULES_DIR,
    GAPS_DIR,
    TASKS_DIR,
)


def register_evidence_tools(mcp) -> None:
    """Register all evidence-related MCP tools."""
    register_session_tools(mcp)
    register_decision_tools(mcp)
    register_task_tools(mcp)
    register_search_tools(mcp)
    register_quality_tools(mcp)
    register_document_tools(mcp)


__all__ = [
    "register_evidence_tools",
    "register_session_tools",
    "register_decision_tools",
    "register_task_tools",
    "register_search_tools",
    "register_quality_tools",
    "register_document_tools",
    # Constants (backward compatibility)
    "EVIDENCE_DIR",
    "DOCS_DIR",
    "BACKLOG_DIR",
    "RULES_DIR",
    "GAPS_DIR",
    "TASKS_DIR",
]
