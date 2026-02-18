"""
Rule Archive MCP Tools
======================
Archive operations for governance rules.

Per RULE-012: DSP Semantic Code Structure
Per RULE-032: File size <300 lines

Extracted from rules_crud.py per RULE-032.
Created: 2026-01-03
Refactored: 2026-01-19 - Removed deprecated functions, inlined aliases
"""

import logging
from dataclasses import asdict

from governance.mcp_tools.common import get_typedb_client, format_mcp_result

logger = logging.getLogger(__name__)


def register_rule_archive_tools(mcp) -> None:
    """Register rule archive MCP tools."""

    @mcp.tool()
    def rules_list_archived() -> str:
        """
        List all archived rules available for restoration.

        Returns:
            JSON array of archived rules with metadata including:
            - rule_id: The rule identifier
            - name: Rule name
            - archived_at: Timestamp of archival
            - reason: Reason for archival
            - dependencies/dependents: Related rules
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            archives = client.get_archived_rules()

            return format_mcp_result({
                "archives": [
                    {
                        "rule_id": a.get("rule", {}).get("id"),
                        "name": a.get("rule", {}).get("name"),
                        "archived_at": a.get("archived_at"),
                        "reason": a.get("reason"),
                        "dependencies": a.get("dependencies", []),
                        "dependents": a.get("dependents", [])
                    }
                    for a in archives
                ],
                "count": len(archives)
            })

        # BUG-192-002 + BUG-362-RA-001: Log full error but return only type name
        except Exception as e:
            logger.error(f"rules_list_archived failed: {e}", exc_info=True)
            return format_mcp_result({"error": f"rules_list_archived failed: {type(e).__name__}"})

        finally:
            client.close()

    @mcp.tool()
    def rule_get_archived(rule_id: str) -> str:
        """
        Get a specific archived rule's full data.

        Args:
            rule_id: The archived rule ID to retrieve

        Returns:
            JSON object with full archive record including rule data,
            archive timestamp, reason, and relationship information
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            archive = client.get_archived_rule(rule_id)

            if archive:
                return format_mcp_result(archive)
            else:
                return format_mcp_result({"error": f"No archive found for rule {rule_id}"})

        # BUG-192-002 + BUG-362-RA-001: Log full error but return only type name
        except Exception as e:
            logger.error(f"rule_get_archived failed: {e}", exc_info=True)
            return format_mcp_result({"error": f"rule_get_archived failed: {type(e).__name__}"})

        finally:
            client.close()

    @mcp.tool()
    def rule_restore(rule_id: str) -> str:
        """
        Restore a rule from archive.

        The restored rule will have status DRAFT (requires manual activation).

        Args:
            rule_id: The archived rule ID to restore

        Returns:
            JSON object with restored rule data or error message
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            rule = client.restore_rule(rule_id)

            if rule:
                return format_mcp_result({
                    "success": True,
                    "message": f"Rule {rule_id} restored from archive (status: DRAFT)",
                    "rule": asdict(rule)
                })
            else:
                return format_mcp_result({"error": f"No archive found for rule {rule_id}"})

        # BUG-362-RA-001: Log full error but return only type name
        except Exception as e:
            logger.error(f"rule_restore failed: {e}", exc_info=True)
            return format_mcp_result({"error": f"rule_restore failed: {type(e).__name__}"})

        finally:
            client.close()
