"""Rule CRUD MCP Tools. Per RULE-012: DSP Semantic Code Structure.
Updated: 2026-01-20 - Added monitoring instrumentation per GAP-MONITOR-INSTRUMENT-001.
"""
from typing import Optional
from dataclasses import asdict

from governance.mcp_tools.common import get_typedb_client, format_mcp_result, log_monitor_event


def register_rule_crud_tools(mcp) -> None:
    """Register rule CRUD MCP tools."""

    @mcp.tool()
    def rule_create(rule_id: str, name: str, category: str, priority: str, directive: str,
                    status: str = "DRAFT", rule_type: Optional[str] = None,
                    applicability: Optional[str] = None) -> str:
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
            applicability: Enforcement level (optional) - MANDATORY|RECOMMENDED|FORBIDDEN|CONDITIONAL
                          Per RD-RULE-APPLICABILITY: defaults to RECOMMENDED for new rules.

        Returns:
            JSON with created rule or error
        """
        # RD-RULE-APPLICABILITY: Validate applicability value
        valid_applicability = ["MANDATORY", "RECOMMENDED", "FORBIDDEN", "CONDITIONAL", None]
        if applicability and applicability not in valid_applicability:
            return format_mcp_result({
                "error": f"Invalid applicability: {applicability}",
                "valid_values": ["MANDATORY", "RECOMMENDED", "FORBIDDEN", "CONDITIONAL"]
            })

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
                # RD-RULE-APPLICABILITY: Set applicability after creation if specified
                if applicability:
                    # BUG-276-RCRUD-002: Guard against update_rule returning None
                    updated = client.update_rule(rule_id=rule_id, applicability=applicability)
                    if updated:
                        rule = updated

                # Instrument: log rule creation event (GAP-MONITOR-INSTRUMENT-001)
                log_monitor_event(
                    event_type="rule_change",
                    source="mcp-rule-create",
                    details={"rule_id": rule_id, "action": "create", "status": status, "applicability": applicability},
                    severity="WARNING"
                )
                return format_mcp_result({
                    "success": True,
                    "message": f"Rule {rule_id} created successfully",
                    "rule": asdict(rule)
                })
            else:
                return format_mcp_result({"error": f"Failed to create rule {rule_id}"})

        except Exception as e:
            return format_mcp_result({"error": f"rule_create failed: {e}"})

        finally:
            client.close()

    @mcp.tool()
    def rule_update(rule_id: str, name: Optional[str] = None, category: Optional[str] = None,
                    priority: Optional[str] = None, directive: Optional[str] = None,
                    status: Optional[str] = None, rule_type: Optional[str] = None,
                    semantic_id: Optional[str] = None, applicability: Optional[str] = None) -> str:
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
            applicability: Enforcement level (optional) - MANDATORY|RECOMMENDED|FORBIDDEN|CONDITIONAL

        Returns:
            JSON with updated rule or error
        """
        # BUG-276-RCRUD-001: Guard against empty update (all params None)
        if not any([name, category, priority, directive, status, rule_type, semantic_id, applicability]):
            return format_mcp_result({"error": "No update fields provided"})

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
                semantic_id=semantic_id,
                applicability=applicability
            )

            if rule:
                # Instrument: log rule update event (GAP-MONITOR-INSTRUMENT-001)
                log_monitor_event(
                    event_type="rule_change",
                    source="mcp-rule-update",
                    details={"rule_id": rule_id, "action": "update"},
                    severity="WARNING"
                )
                return format_mcp_result({
                    "success": True,
                    "message": f"Rule {rule_id} updated successfully",
                    "rule": asdict(rule)
                })
            else:
                return format_mcp_result({"error": f"Failed to update rule {rule_id}"})

        except Exception as e:
            return format_mcp_result({"error": f"rule_update failed: {e}"})

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
                # Instrument: log rule deprecation event (GAP-MONITOR-INSTRUMENT-001)
                log_monitor_event(
                    event_type="rule_change",
                    source="mcp-rule-deprecate",
                    details={"rule_id": rule_id, "action": "deprecate", "reason": reason},
                    severity="WARNING"
                )
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

        except Exception as e:
            return format_mcp_result({"error": f"rule_deprecate failed: {e}"})

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
        # BUG-304-DEL-001: Use identity check (is not True) to prevent bypass
        # via truthy non-True values (e.g., confirm=1, confirm="yes")
        if confirm is not True:
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
                # Instrument: log rule deletion event (GAP-MONITOR-INSTRUMENT-001)
                log_monitor_event(
                    event_type="rule_change",
                    source="mcp-rule-delete",
                    details={"rule_id": rule_id, "action": "delete"},
                    severity="CRITICAL"
                )
                return format_mcp_result({
                    "success": True,
                    "message": f"Rule {rule_id} permanently deleted (archived for recovery)",
                    "rule_id": rule_id,
                    "archived": True
                })
            else:
                return format_mcp_result({"error": f"Rule {rule_id} not found"})

        # BUG-B185-005: Add except to match rule_create pattern
        except Exception as e:
            return format_mcp_result({"error": f"rule_delete failed: {e}"})

        finally:
            client.close()
