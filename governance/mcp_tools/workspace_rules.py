"""
Workspace Rule-Document Linking MCP Tools.

Per P10.8: TypeDB-Filesystem Rule Linking.
Per GAP-MCP-008: Semantic Rule ID Support.
Per DOC-SIZE-01-v1: Modularized from workspace.py.

Tools:
- workspace_scan_rule_documents: Scan rule markdown files (dry run)
- workspace_link_rules_to_documents: Create TypeDB relations
- workspace_get_document_for_rule: Get document path for a rule
- workspace_get_rules_for_document: Get rules in a document

Created: 2026-01-17 (extracted from workspace.py)
"""

import logging

from governance.mcp_tools.common import format_mcp_result

logger = logging.getLogger(__name__)


def register_workspace_rule_tools(mcp) -> None:
    """Register workspace rule-document linking MCP tools."""

    @mcp.tool()
    def workspace_scan_rule_documents() -> str:
        """
        Scan rule markdown documents and extract rule references (dry run).

        Per P10.8: TypeDB-Filesystem Rule Linking.
        Per GAP-MCP-008: Supports both legacy and semantic rule IDs.

        Scans docs/rules/**/*.md files (including subdirectories) and extracts:
        - Legacy IDs: RULE-001, RULE-042
        - Semantic IDs: SESSION-EVID-01-v1, GOV-BICAM-01-v1

        Returns:
            JSON summary of documents and their linked rules
        """
        try:
            from governance.rule_linker import scan_rule_documents

            documents = scan_rule_documents()

            result = []
            for doc in documents:
                result.append({
                    "document_id": doc.document_id,
                    "path": doc.path,
                    "rule_count": len(doc.rule_ids) if doc.rule_ids else 0,
                    "rule_ids": doc.rule_ids or [],
                })

            return format_mcp_result({
                "total_documents": len(documents),
                "documents": result,
            })
        except Exception as e:
            logger.error(f"workspace_scan_rule_documents failed: {e}")
            return format_mcp_result({"error": str(e)})

    @mcp.tool()
    def workspace_link_rules_to_documents() -> str:
        """
        Link rules to their filesystem markdown documents in TypeDB.

        Per P10.8: TypeDB-Filesystem Rule Linking.

        Creates document entities and document-references-rule relations
        in TypeDB to link rules with their source markdown files.

        Returns:
            JSON with sync statistics (documents_inserted, relations_created, etc.)
        """
        try:
            from governance.rule_linker import link_rules_to_documents

            result = link_rules_to_documents()
            return format_mcp_result(result)
        except Exception as e:
            logger.error(f"workspace_link_rules_to_documents failed: {e}")
            return format_mcp_result({"error": str(e)})

    @mcp.tool()
    def workspace_get_document_for_rule(rule_id: str) -> str:
        """
        Get the markdown document path for a rule.

        Per P10.8: TypeDB-Filesystem Rule Linking.
        Per GAP-MCP-008: Accepts both legacy and semantic rule IDs.

        Args:
            rule_id: Rule ID (e.g., "RULE-001" or "SESSION-EVID-01-v1")

        Returns:
            JSON with document path or null if not found
        """
        try:
            from governance.rule_linker import get_document_for_rule

            path = get_document_for_rule(rule_id)
            return format_mcp_result({
                "rule_id": rule_id,
                "document_path": path,
            })
        except Exception as e:
            logger.error(f"workspace_get_document_for_rule failed: {e}")
            return format_mcp_result({"error": str(e)})

    @mcp.tool()
    def workspace_get_rules_for_document(document_id: str) -> str:
        """
        Get all rules documented in a specific markdown file.

        Per P10.8: TypeDB-Filesystem Rule Linking.

        Args:
            document_id: Document ID (e.g., "RULES-GOVERNANCE")

        Returns:
            JSON with list of rule IDs
        """
        try:
            from governance.rule_linker import get_rules_for_document

            rule_ids = get_rules_for_document(document_id)
            return format_mcp_result({
                "document_id": document_id,
                "rule_count": len(rule_ids),
                "rule_ids": rule_ids,
            })
        except Exception as e:
            logger.error(f"workspace_get_rules_for_document failed: {e}")
            return format_mcp_result({"error": str(e)})

    logger.info("Registered workspace rule-document linking tools (4 tools)")
