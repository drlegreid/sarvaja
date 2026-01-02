"""
Rule MCP Tools
==============
Query and CRUD operations for governance rules.

Per RULE-012: DSP Semantic Code Structure
Per FP + Digital Twin Paradigm: Rule entity module
Per GAP-MCP-004: Fallback to markdown when TypeDB unavailable
"""

import json
from typing import Optional
from dataclasses import asdict

from governance.mcp_tools.common import get_typedb_client
from governance.mcp_tools.rule_fallback import (
    get_all_markdown_rules,
    get_markdown_rule_by_id,
    filter_markdown_rules,
    markdown_rule_to_dict,
)


def register_rule_tools(mcp) -> None:
    """Register rule-related MCP tools."""

    @mcp.tool()
    def governance_query_rules(
        category: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> str:
        """
        Query rules from the governance database.

        Args:
            category: Filter by category (governance, architecture, testing, etc.)
            status: Filter by status (ACTIVE, DRAFT, DEPRECATED)
            priority: Filter by priority (CRITICAL, HIGH, MEDIUM, LOW)

        Returns:
            JSON array of matching rules
        """
        client = get_typedb_client()
        use_fallback = False

        try:
            if not client.connect():
                use_fallback = True
            else:
                # Build query based on filters
                if status == "ACTIVE":
                    rules = client.get_active_rules()
                else:
                    rules = client.get_all_rules()

                # Apply additional filters (pure functions)
                if category:
                    rules = [r for r in rules if r.category == category]
                if priority:
                    rules = [r for r in rules if r.priority == priority]
                if status and status != "ACTIVE":
                    rules = [r for r in rules if r.status == status]

                return json.dumps([asdict(r) for r in rules], default=str, indent=2)

        except Exception:
            use_fallback = True

        finally:
            client.close()

        # Fallback to markdown files (GAP-MCP-004)
        if use_fallback:
            md_rules = get_all_markdown_rules()
            if not md_rules:
                return json.dumps({
                    "error": "TypeDB unavailable and no markdown rules found",
                    "hint": "Ensure docs/rules/*.md files exist"
                })

            filtered = filter_markdown_rules(md_rules, category, status, priority)
            result = [markdown_rule_to_dict(r) for r in filtered]
            return json.dumps({
                "rules": result,
                "source": "markdown_fallback",
                "warning": "TypeDB unavailable - using markdown fallback (read-only)"
            }, indent=2)

    @mcp.tool()
    def governance_get_rule(rule_id: str) -> str:
        """
        Get a specific rule by ID.

        Args:
            rule_id: The rule ID (e.g., "RULE-001")

        Returns:
            JSON object with rule details or error
        """
        client = get_typedb_client()
        use_fallback = False

        try:
            if not client.connect():
                use_fallback = True
            else:
                rule = client.get_rule_by_id(rule_id)
                if rule:
                    return json.dumps(asdict(rule), default=str, indent=2)
                else:
                    # Rule not in TypeDB, try markdown
                    use_fallback = True

        except Exception:
            use_fallback = True

        finally:
            client.close()

        # Fallback to markdown files (GAP-MCP-004)
        if use_fallback:
            md_rule = get_markdown_rule_by_id(rule_id)
            if md_rule:
                result = markdown_rule_to_dict(md_rule)
                result["warning"] = "TypeDB unavailable - using markdown fallback (read-only)"
                return json.dumps(result, indent=2)
            else:
                return json.dumps({"error": f"Rule {rule_id} not found in TypeDB or markdown"})

    @mcp.tool()
    def governance_get_dependencies(rule_id: str) -> str:
        """
        Get all dependencies for a rule (uses TypeDB inference for transitive deps).

        Args:
            rule_id: The rule ID to get dependencies for

        Returns:
            JSON array of dependency rule IDs
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            deps = client.get_rule_dependencies(rule_id)
            return json.dumps(deps, indent=2)

        finally:
            client.close()

    @mcp.tool()
    def governance_find_conflicts() -> str:
        """
        Find conflicting rules using TypeDB inference.

        Returns:
            JSON array of conflict pairs with explanations
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            conflicts = client.find_conflicts()
            return json.dumps(conflicts, indent=2)

        finally:
            client.close()

    # =========================================================================
    # CRUD OPERATIONS
    # =========================================================================

    @mcp.tool()
    def governance_create_rule(
        rule_id: str,
        name: str,
        category: str,
        priority: str,
        directive: str,
        status: str = "DRAFT"
    ) -> str:
        """
        Create a new governance rule.

        Args:
            rule_id: Unique rule ID (e.g., "RULE-023")
            name: Human-readable rule name
            category: Rule category (governance, technical, operational, architecture, testing)
            priority: Priority level (CRITICAL, HIGH, MEDIUM, LOW)
            directive: The rule directive text
            status: Initial status (ACTIVE, DRAFT, DEPRECATED). Default: DRAFT

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
                status=status
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
        status: Optional[str] = None
    ) -> str:
        """
        Update an existing rule. Only provided fields will be updated.

        Args:
            rule_id: Rule ID to update (e.g., "RULE-001")
            name: New rule name (optional)
            category: New category (optional)
            priority: New priority (optional)
            directive: New directive text (optional)
            status: New status (optional)

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
                status=status
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

    # =========================================================================
    # ARCHIVE OPERATIONS
    # =========================================================================

    @mcp.tool()
    def governance_list_archived_rules() -> str:
        """
        List all archived rules available for restoration.

        Returns:
            JSON array of archived rules with metadata
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
    def governance_get_archived_rule(rule_id: str) -> str:
        """
        Get a specific archived rule's full data.

        Args:
            rule_id: The archived rule ID to retrieve

        Returns:
            JSON object with full archive record
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
    def governance_restore_rule(rule_id: str) -> str:
        """
        Restore a rule from archive.

        The restored rule will have status DRAFT (requires manual activation).

        Args:
            rule_id: The archived rule ID to restore

        Returns:
            JSON object with restored rule or error
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
