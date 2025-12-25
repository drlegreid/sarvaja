"""
Decision MCP Tools
==================
Decision impact and health check operations.

Per RULE-012: DSP Semantic Code Structure
Per FP + Digital Twin Paradigm: Decision entity module
"""

import json
from datetime import datetime

from governance.mcp_tools.common import (
    get_typedb_client,
    TYPEDB_HOST,
    TYPEDB_PORT,
    DATABASE_NAME,
)


def register_decision_tools(mcp) -> None:
    """Register decision-related MCP tools."""

    @mcp.tool()
    def governance_get_decision_impacts(decision_id: str) -> str:
        """
        Get all rules affected by a decision (uses TypeDB inference).

        Args:
            decision_id: The decision ID (e.g., "DECISION-003")

        Returns:
            JSON array of affected rule IDs
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            impacts = client.get_decision_impacts(decision_id)
            return json.dumps(impacts, indent=2)

        finally:
            client.close()

    @mcp.tool()
    def governance_health() -> str:
        """
        Check governance system health.

        Returns:
            JSON object with health status and statistics
        """
        client = get_typedb_client()

        try:
            connected = client.connect()

            if not connected:
                return json.dumps({
                    "status": "unhealthy",
                    "typedb_connected": False,
                    "error": "Cannot connect to TypeDB"
                })

            # Get counts
            rules = client.get_all_rules()

            return json.dumps({
                "status": "healthy",
                "typedb_connected": True,
                "typedb_host": f"{TYPEDB_HOST}:{TYPEDB_PORT}",
                "database": DATABASE_NAME,
                "statistics": {
                    "rules_count": len(rules),
                    "active_rules": len([r for r in rules if r.status == "ACTIVE"])
                },
                "timestamp": datetime.now().isoformat()
            }, indent=2)

        finally:
            client.close()
