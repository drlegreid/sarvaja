"""
Decision MCP Tools
==================
Decision impact and health check operations.

Per RULE-012: DSP Semantic Code Structure
Per FP + Digital Twin Paradigm: Decision entity module
Per GAP-MCP-002: Dependency health check with action_required pattern
"""

import os
from datetime import datetime

from governance.mcp_tools.common import (
    get_typedb_client,
    TYPEDB_HOST,
    TYPEDB_PORT,
    DATABASE_NAME,
    format_mcp_result,
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
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            impacts = client.get_decision_impacts(decision_id)
            return format_mcp_result(impacts)

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
            return format_mcp_result({
                "status": "unhealthy",
                "error": "DEPENDENCY_FAILURE",
                "action_required": "START_SERVICES",
                "services": failed_services,
                "recovery_hint": f"docker compose --profile dev up -d {' '.join(failed_services)}",
                "details": service_status,
                "timestamp": datetime.now().isoformat()
            })

        # All healthy - get statistics
        stats = {}
        entropy_alerts = []
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

        # GAP-HEALTH-002: Document entropy detection for DSP trigger
        entropy_alerts = _detect_document_entropy()
        dsp_suggested = len(entropy_alerts) >= 2  # Multiple entropy signals

        result = {
            "status": "healthy",
            "details": service_status,
            "database": DATABASE_NAME,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }

        if dsp_suggested:
            result["action_required"] = "DSP_SUGGESTED"
            result["entropy_alerts"] = entropy_alerts
            result["dsp_hint"] = "Document entropy high. Consider running DSP cycle (RULE-012)"
        else:
            result["action_required"] = None
            if entropy_alerts:
                result["entropy_alerts"] = entropy_alerts

        return format_mcp_result(result)

    # =========================================================================
    # PHASE 1: Domain-Based Aliases (RD-MCP-TOOL-NAMING)
    # =========================================================================

    def decision_impacts(decision_id: str) -> str:
        """Get decision impacts. Alias for governance_get_decision_impacts."""
        return governance_get_decision_impacts(decision_id)

    def health_check() -> str:
        """Check governance health. Alias for governance_health."""
        return governance_health()

    # Register domain-based aliases
    mcp.tool()(decision_impacts)
    mcp.tool()(health_check)


def _detect_document_entropy() -> list:
    """
    Detect document entropy indicators for DSP trigger.

    Per GAP-HEALTH-002 and RULE-012: Deep Sleep Protocol.

    Entropy signals:
    1. Many open gaps (>30 HIGH priority)
    2. Large files (>300 lines) in key directories
    3. DSM cycle not run recently (>7 days)
    4. Session evidence files accumulating

    Returns:
        List of entropy alert messages
    """
    from pathlib import Path

    alerts = []

    # 1. Check gap entropy via GAP-INDEX parsing
    try:
        gap_index = Path(__file__).parent.parent.parent / "docs" / "gaps" / "GAP-INDEX.md"
        if gap_index.exists():
            content = gap_index.read_text(encoding="utf-8")
            # Count OPEN + HIGH priority gaps
            open_high = content.count("| OPEN |") + content.count("| PARTIAL |")
            if open_high > 50:
                alerts.append(f"HIGH gap entropy: {open_high} open gaps (threshold: 50)")
    except Exception:
        pass

    # 2. Check for large Python files (>300 lines per RULE-012)
    try:
        governance_dir = Path(__file__).parent.parent
        large_files = []
        for py_file in governance_dir.glob("**/*.py"):
            if py_file.stat().st_size > 15000:  # ~300 lines * 50 chars
                line_count = len(py_file.read_text(encoding="utf-8").splitlines())
                if line_count > 300:
                    large_files.append(f"{py_file.name}:{line_count}")
        if large_files:
            alerts.append(f"Large files detected (>300 lines): {', '.join(large_files[:3])}")
    except Exception:
        pass

    # 3. Check DSM state for last cycle
    try:
        dsm_state = Path(__file__).parent.parent.parent / ".dsm_state.json"
        if dsm_state.exists():
            import json as json_mod
            state = json_mod.loads(dsm_state.read_text())
            last_updated = state.get("last_updated")
            if last_updated:
                last_dt = datetime.fromisoformat(last_updated)
                days_ago = (datetime.now() - last_dt).days
                if days_ago > 7:
                    alerts.append(f"No DSP cycle in {days_ago} days (threshold: 7)")
    except Exception:
        pass

    # 4. Check evidence file accumulation
    try:
        evidence_dir = Path(__file__).parent.parent.parent / "evidence"
        if evidence_dir.exists():
            session_files = list(evidence_dir.glob("SESSION-*.md"))
            if len(session_files) > 20:
                alerts.append(f"Evidence accumulation: {len(session_files)} session files")
    except Exception:
        pass

    return alerts
