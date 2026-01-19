"""
Audit Trail MCP Tools
=====================
Audit trail query operations for debugging agent decisions.

Per RD-DEBUG-AUDIT Phase 4: MCP tool for claude-mem integration.
Per RULE-012: DSP Semantic Code Structure

Provides tools for:
- Querying audit trail by entity ID
- Searching by correlation ID
- Getting audit statistics
"""

from typing import Optional

from governance.mcp_tools.common import format_mcp_result


def register_audit_tools(mcp) -> None:
    """Register audit trail MCP tools."""

    @mcp.tool()
    def audit_query(
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        action_type: Optional[str] = None,
        correlation_id: Optional[str] = None,
        limit: int = 20
    ) -> str:
        """
        Query the audit trail with optional filters.

        Use this to trace agent decisions and rule applications.
        Per RD-DEBUG-AUDIT: Audit trail queryable by entity_id.

        Args:
            entity_id: Filter by entity ID (e.g., task ID, session ID)
            entity_type: Filter by type (task, session, rule, agent)
            action_type: Filter by action (CREATE, UPDATE, CLAIM, COMPLETE, DELETE)
            correlation_id: Filter by correlation ID for tracing
            limit: Maximum entries to return (default: 20)

        Returns:
            JSON array of audit entries with timestamps, actors, and applied rules
        """
        from governance.stores import query_audit_trail

        try:
            entries = query_audit_trail(
                entity_id=entity_id,
                entity_type=entity_type,
                action_type=action_type,
                correlation_id=correlation_id,
                limit=limit
            )

            result = {
                "count": len(entries),
                "entries": entries
            }
            return format_mcp_result(result)

        except Exception as e:
            return format_mcp_result({"error": f"Failed to query audit trail: {str(e)}"})

    @mcp.tool()
    def audit_summary() -> str:
        """
        Get audit trail summary statistics.

        Returns counts by action type, entity type, and actor.
        Use for debugging "what happened" during a session.

        Returns:
            JSON object with audit statistics
        """
        from governance.stores import get_audit_summary

        try:
            summary = get_audit_summary()
            return format_mcp_result(summary)
        except Exception as e:
            return format_mcp_result({"error": f"Failed to get audit summary: {str(e)}"})

    @mcp.tool()
    def audit_entity_trail(entity_id: str) -> str:
        """
        Get complete audit trail for a specific entity.

        Use this to answer "why was this decision made?" queries.
        Returns all audit entries for the entity, ordered by timestamp.

        Args:
            entity_id: The entity ID to get audit trail for (e.g., TASK-001)

        Returns:
            JSON object with entity audit history
        """
        from governance.stores import query_audit_trail

        try:
            entries = query_audit_trail(entity_id=entity_id, limit=100)

            if not entries:
                return format_mcp_result({
                    "entity_id": entity_id,
                    "count": 0,
                    "message": "No audit entries found for this entity",
                    "entries": []
                })

            # Extract timeline summary
            actions = [e.get("action_type") for e in entries]
            actors = list(set(e.get("actor_id") for e in entries))
            rules = []
            for e in entries:
                if e.get("applied_rules"):
                    rules.extend(e.get("applied_rules", []))
            unique_rules = list(set(rules))

            result = {
                "entity_id": entity_id,
                "count": len(entries),
                "timeline_summary": {
                    "actions": actions,
                    "actors": actors,
                    "rules_applied": unique_rules
                },
                "entries": entries
            }
            return format_mcp_result(result)

        except Exception as e:
            return format_mcp_result({"error": f"Failed to get entity audit trail: {str(e)}"})

    @mcp.tool()
    def audit_trace(correlation_id: str) -> str:
        """
        Trace all operations with a specific correlation ID.

        Correlation IDs link related operations across entities.
        Use to trace a complete operation flow.

        Args:
            correlation_id: The correlation ID (e.g., CORR-20260117-120000-abc123)

        Returns:
            JSON object with all correlated operations
        """
        from governance.stores import query_audit_trail

        try:
            entries = query_audit_trail(correlation_id=correlation_id, limit=100)

            if not entries:
                return format_mcp_result({
                    "correlation_id": correlation_id,
                    "count": 0,
                    "message": "No operations found with this correlation ID",
                    "entries": []
                })

            # Group by entity for summary
            by_entity = {}
            for entry in entries:
                eid = entry.get("entity_id", "unknown")
                if eid not in by_entity:
                    by_entity[eid] = []
                by_entity[eid].append(entry.get("action_type"))

            result = {
                "correlation_id": correlation_id,
                "count": len(entries),
                "affected_entities": by_entity,
                "entries": entries
            }
            return format_mcp_result(result)

        except Exception as e:
            return format_mcp_result({"error": f"Failed to trace correlation: {str(e)}"})
