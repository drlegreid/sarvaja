"""Rule CRUD MCP Tools. Per RULE-012: DSP Semantic Code Structure."""
from typing import Optional
from dataclasses import asdict

from governance.mcp_tools.common import get_typedb_client, format_mcp_result


def register_rule_crud_tools(mcp) -> None:
    """Register rule CRUD MCP tools."""

    @mcp.tool()
    def rule_create(rule_id: str, name: str, category: str, priority: str, directive: str,
                    status: str = "DRAFT", rule_type: Optional[str] = None) -> str:
        """
        Create a new governance rule in TypeDB.

        Args:
            rule_id: Unique rule identifier (e.g., "RULE-001" or "SESSION-EVID-01-v1")
            name: Human-readable rule name
            category: Rule category (e.g., "GOVERNANCE", "TECHNICAL", "OPERATIONAL")
            priority: Priority level (CRITICAL, HIGH, MEDIUM, LOW)
            directive: The rule directive text
            status: Rule status (default: DRAFT)
            rule_type: Optional rule type classification

        Returns:
            JSON with created rule or error
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            rule = client.create_rule(
                rule_id=rule_id,
                name=name,
                category=category,
                priority=priority,
                directive=directive,
                status=status,
                rule_type=rule_type
            )

            if rule:
                return format_mcp_result({
                    "success": True,
                    "message": f"Rule {rule_id} created successfully",
                    "rule": asdict(rule)
                })
            else:
                return format_mcp_result({"error": f"Failed to create rule {rule_id}"})

        except ValueError as e:
            return format_mcp_result({"error": str(e)})

        finally:
            client.close()

    @mcp.tool()
    def rule_update(rule_id: str, name: Optional[str] = None, category: Optional[str] = None,
                    priority: Optional[str] = None, directive: Optional[str] = None,
                    status: Optional[str] = None, rule_type: Optional[str] = None,
                    semantic_id: Optional[str] = None) -> str:
        """
        Update an existing governance rule in TypeDB.

        Args:
            rule_id: Rule identifier to update
            name: New rule name (optional)
            category: New category (optional)
            priority: New priority (optional)
            directive: New directive text (optional)
            status: New status (optional)
            rule_type: New rule type (optional)
            semantic_id: New semantic ID for migration (optional)

        Returns:
            JSON with updated rule or error
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            rule = client.update_rule(
                rule_id=rule_id,
                name=name,
                category=category,
                priority=priority,
                directive=directive,
                status=status,
                rule_type=rule_type,
                semantic_id=semantic_id
            )

            if rule:
                return format_mcp_result({
                    "success": True,
                    "message": f"Rule {rule_id} updated successfully",
                    "rule": asdict(rule)
                })
            else:
                return format_mcp_result({"error": f"Failed to update rule {rule_id}"})

        except ValueError as e:
            return format_mcp_result({"error": str(e)})

        finally:
            client.close()

    @mcp.tool()
    def rule_deprecate(rule_id: str, reason: Optional[str] = None) -> str:
        """
        Deprecate a governance rule (soft delete).

        Sets rule status to DEPRECATED. Preferred over hard delete.

        Args:
            rule_id: Rule identifier to deprecate
            reason: Optional reason for deprecation

        Returns:
            JSON with deprecation status or error
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            rule = client.deprecate_rule(rule_id, reason=reason)

            if rule:
                result = {
                    "success": True,
                    "message": f"Rule {rule_id} deprecated",
                    "rule_id": rule_id,
                    "new_status": "DEPRECATED"
                }
                if reason:
                    result["reason"] = reason
                return format_mcp_result(result)
            else:
                return format_mcp_result({"error": f"Rule {rule_id} not found"})

        except ValueError as e:
            return format_mcp_result({"error": str(e)})

        finally:
            client.close()

    @mcp.tool()
    def rule_delete(rule_id: str, confirm: bool = False) -> str:
        """
        Permanently delete a governance rule (hard delete with archive).

        Requires explicit confirmation. Consider using rule_deprecate instead.

        Args:
            rule_id: Rule identifier to delete
            confirm: Must be True to proceed with deletion

        Returns:
            JSON with deletion status or error
        """
        if not confirm:
            return format_mcp_result({
                "error": "Deletion requires explicit confirmation. Set confirm=True to proceed.",
                "warning": "This is a hard delete. Consider using rule_deprecate instead."
            })

        client = get_typedb_client()

        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            deleted = client.delete_rule(rule_id)

            if deleted:
                return format_mcp_result({
                    "success": True,
                    "message": f"Rule {rule_id} permanently deleted (archived for recovery)",
                    "rule_id": rule_id,
                    "archived": True
                })
            else:
                return format_mcp_result({"error": f"Rule {rule_id} not found"})

        finally:
            client.close()
