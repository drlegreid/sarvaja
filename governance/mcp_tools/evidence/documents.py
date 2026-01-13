"""
Document Viewing MCP Tools
==========================
Document viewing operations for evidence, rules, and tasks.

Per RULE-012: DSP Semantic Code Structure
Per RULE-032: File size <300 lines (modularized)
Per GAP-FILE-008: Extracted from evidence.py
Per P10.8 / GAP-DOC-001, GAP-DOC-002: Document viewing
Per DOC-LINK-01-v1: Relative Document Linking support
Per RD-DOC-SERVICE: Document service with type detection + pagination

Tools (registered from sub-modules):
- governance_get_document: Get document content by path (with pagination)
- governance_list_documents: List documents in directory
- governance_get_rule_document: Get full rule markdown document
- governance_get_task_document: Get task details from workspace documents
- governance_extract_links: Extract all links from a document
- governance_resolve_link: Resolve a relative link to absolute path

Created: 2024-12-28
Updated: 2026-01-13 - Modularized into sub-modules per DOC-SIZE-01-v1
"""

from .documents_core import register_core_document_tools, FILE_TYPE_MAP
from .documents_entity import register_entity_document_tools
from .documents_links import register_link_document_tools


def register_document_tools(mcp) -> None:
    """Register all document viewing MCP tools.

    Delegates to sub-modules:
    - documents_core: get_document, list_documents
    - documents_entity: get_rule_document, get_task_document
    - documents_links: extract_links, resolve_link
    """
    register_core_document_tools(mcp)
    register_entity_document_tools(mcp)
    register_link_document_tools(mcp)


# Re-export for backwards compatibility
__all__ = [
    "register_document_tools",
    "FILE_TYPE_MAP",
]
