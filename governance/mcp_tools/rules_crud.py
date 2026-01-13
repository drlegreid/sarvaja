"""
Rule CRUD MCP Tools
===================
CRUD operations for governance rules.

Per RULE-012: DSP Semantic Code Structure
Per RULE-032: File size <300 lines

Extracted from rules.py per modularization plan.
Archive operations in rules_archive.py.
Created: 2026-01-03
"""

import json
from typing import Optional
from dataclasses import asdict

from governance.mcp_tools.common import get_typedb_client


def register_rule_crud_tools(mcp) -> None:
    """Register rule CRUD MCP tools."""

    @mcp.tool()
    def governance_create_rule(
        rule_id: str,
        name: str,
        category: str,
        priority: str,
        directive: str,
        status: str = "DRAFT",
        rule_type: Optional[str] = None
    ) -> str:
        """
        Create a new governance rule.

        Args:
            rule_id: Unique rule ID (e.g., "RULE-023")
            name: Human-readable rule name
            category: Rule category (governance, technical, operational, architecture, testing)
            priority: Priority level (CRITICAL, HIGH, MEDIUM, LOW)
            directive: The rule directive text
            status: Initial status (ACTIVE, PROPOSED, DISABLED). Default: DRAFT
            rule_type: Rule type (FOUNDATIONAL, OPERATIONAL, TECHNICAL, META, LEAF)

        Returns:
            JSON object with created rule or error
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

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
                return json.dumps({
                    "success": True,
                    "message": f"Rule {rule_id} created successfully",
                    "rule": asdict(rule)
                }, default=str, indent=2)
            else:
                return json.dumps({"error": f"Failed to create rule {rule_id}"})

        except ValueError as e:
            return json.dumps({"error": str(e)})

        finally:
            client.close()

    @mcp.tool()
    def governance_update_rule(
        rule_id: str,
        name: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        directive: Optional[str] = None,
        status: Optional[str] = None,
        rule_type: Optional[str] = None
    ) -> str:
        """
        Update an existing rule. Only provided fields will be updated.

        Args:
            rule_id: Rule ID to update (e.g., "RULE-001")
            name: New rule name (optional)
            category: New category (optional)
            priority: New priority (optional)
            directive: New directive text (optional)
            status: New status (ACTIVE, PROPOSED, DISABLED)
            rule_type: New rule type (FOUNDATIONAL, OPERATIONAL, TECHNICAL, META, LEAF)

        Returns:
            JSON object with updated rule or error
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            rule = client.update_rule(
                rule_id=rule_id,
                name=name,
                category=category,
                priority=priority,
                directive=directive,
                status=status,
                rule_type=rule_type
            )

            if rule:
                return json.dumps({
                    "success": True,
                    "message": f"Rule {rule_id} updated successfully",
                    "rule": asdict(rule)
                }, default=str, indent=2)
            else:
                return json.dumps({"error": f"Failed to update rule {rule_id}"})

        except ValueError as e:
            return json.dumps({"error": str(e)})

        finally:
            client.close()

    @mcp.tool()
    def governance_deprecate_rule(rule_id: str, reason: Optional[str] = None) -> str:
        """
        Deprecate a rule (soft delete - sets status to DEPRECATED).

        Args:
            rule_id: Rule ID to deprecate (e.g., "RULE-001")
            reason: Optional reason for deprecation

        Returns:
            JSON object with deprecation status
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

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
                return json.dumps(result, indent=2)
            else:
                return json.dumps({"error": f"Rule {rule_id} not found"})

        except ValueError as e:
            return json.dumps({"error": str(e)})

        finally:
            client.close()

    @mcp.tool()
    def governance_delete_rule(rule_id: str, confirm: bool = False) -> str:
        """
        Permanently delete a rule (hard delete).

        WARNING: This is irreversible. Prefer governance_deprecate_rule for audit trail.

        Args:
            rule_id: Rule ID to delete
            confirm: Must be True to confirm deletion

        Returns:
            JSON object with deletion status
        """
        if not confirm:
            return json.dumps({
                "error": "Deletion requires explicit confirmation. Set confirm=True to proceed.",
                "warning": "This is a hard delete. Consider using governance_deprecate_rule instead."
            }, indent=2)

        client = get_typedb_client()

        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            deleted = client.delete_rule(rule_id)

            if deleted:
                return json.dumps({
                    "success": True,
                    "message": f"Rule {rule_id} permanently deleted (archived for recovery)",
                    "rule_id": rule_id,
                    "archived": True
                }, indent=2)
            else:
                return json.dumps({"error": f"Rule {rule_id} not found"})

        finally:
            client.close()
