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

import json
from dataclasses import asdict

from governance.mcp_tools.common import get_typedb_client


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
                return json.dumps({"error": "Failed to connect to TypeDB"})

            archives = client.get_archived_rules()

            return json.dumps({
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
            }, indent=2)

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
                return json.dumps({"error": "Failed to connect to TypeDB"})

            archive = client.get_archived_rule(rule_id)

            if archive:
                return json.dumps(archive, indent=2, default=str)
            else:
                return json.dumps({"error": f"No archive found for rule {rule_id}"})

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
                return json.dumps({"error": "Failed to connect to TypeDB"})

            rule = client.restore_rule(rule_id)

            if rule:
                return json.dumps({
                    "success": True,
                    "message": f"Rule {rule_id} restored from archive (status: DRAFT)",
                    "rule": asdict(rule)
                }, default=str, indent=2)
            else:
                return json.dumps({"error": f"No archive found for rule {rule_id}"})

        except ValueError as e:
            return json.dumps({"error": str(e)})

        finally:
            client.close()
