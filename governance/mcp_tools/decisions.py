"""
Decision MCP Tools
==================
Decision impact and health check operations.

Per RULE-012: DSP Semantic Code Structure
Per FP + Digital Twin Paradigm: Decision entity module
Per GAP-MCP-002: Dependency health check with action_required pattern
"""

import json
import os
from datetime import datetime

from governance.mcp_tools.common import (
    get_typedb_client,
    TYPEDB_HOST,
    TYPEDB_PORT,
    DATABASE_NAME,
)

# ChromaDB configuration
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8001"))


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
        Check governance system health (GAP-MCP-002).

        Checks both TypeDB and ChromaDB dependencies. Returns structured
        response with action_required for Claude Code integration.

        RULE-021 Compliance:
        - Level 1: Pre-operation health check
        - Level 2: Session start audit
        - Level 3: Recovery protocol with action_required

        Returns:
            JSON object with health status. If unhealthy, includes:
            - action_required: "START_SERVICES" (for Claude Code)
            - services: list of failed service names
            - recovery_hint: Docker command to fix

        Example unhealthy response:
            {
                "status": "unhealthy",
                "error": "DEPENDENCY_FAILURE",
                "action_required": "START_SERVICES",
                "services": ["typedb"],
                "recovery_hint": "docker compose up -d typedb"
            }
        """
        import socket

        failed_services = []
        service_status = {}

        # Check TypeDB (port 1729)
        typedb_healthy = False
        typedb_error = None
        try:
            client = get_typedb_client()
            if client.connect():
                typedb_healthy = True
                client.close()
        except Exception as e:
            typedb_error = str(e)

        service_status["typedb"] = {
            "healthy": typedb_healthy,
            "host": f"{TYPEDB_HOST}:{TYPEDB_PORT}",
            "error": typedb_error
        }
        if not typedb_healthy:
            failed_services.append("typedb")

        # Check ChromaDB (port 8001)
        chromadb_healthy = False
        chromadb_error = None
        try:
            # Simple TCP check first
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((CHROMADB_HOST, CHROMADB_PORT))
            sock.close()
            if result == 0:
                # Port open, try HTTP heartbeat
                import urllib.request
                req = urllib.request.Request(
                    f"http://{CHROMADB_HOST}:{CHROMADB_PORT}/api/v2/heartbeat",
                    method="GET"
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status == 200:
                        chromadb_healthy = True
        except Exception as e:
            chromadb_error = str(e)

        service_status["chromadb"] = {
            "healthy": chromadb_healthy,
            "host": f"{CHROMADB_HOST}:{CHROMADB_PORT}",
            "error": chromadb_error
        }
        if not chromadb_healthy:
            failed_services.append("chromadb")

        # Determine overall status
        if failed_services:
            # GAP-MCP-002: Return action_required for Claude Code
            return json.dumps({
                "status": "unhealthy",
                "error": "DEPENDENCY_FAILURE",
                "action_required": "START_SERVICES",
                "services": failed_services,
                "recovery_hint": f"docker compose --profile dev up -d {' '.join(failed_services)}",
                "details": service_status,
                "timestamp": datetime.now().isoformat()
            }, indent=2)

        # All healthy - get statistics
        stats = {}
        try:
            client = get_typedb_client()
            if client.connect():
                rules = client.get_all_rules()
                stats = {
                    "rules_count": len(rules),
                    "active_rules": len([r for r in rules if r.status == "ACTIVE"])
                }
                client.close()
        except Exception:
            pass

        return json.dumps({
            "status": "healthy",
            "action_required": None,
            "details": service_status,
            "database": DATABASE_NAME,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }, indent=2)
