"""
Decision Evidence MCP Tools
============================
Decision listing and retrieval operations.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-008: Extracted from evidence.py

Tools:
- governance_list_decisions: List all strategic decisions
- governance_get_decision: Get detailed decision information

Created: 2024-12-28
"""

import glob
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

from governance.mcp_tools.common import get_typedb_client, format_mcp_result
from .common import EVIDENCE_DIR


def register_decision_tools(mcp) -> None:
    """Register decision-related MCP tools."""

    @mcp.tool()
    def governance_list_decisions() -> str:
        """
        List all strategic decisions from TypeDB and evidence files.

        Returns:
            JSON array of decisions with ID, name, status, and date
        """
        decisions = []

        # Get from TypeDB
        client = get_typedb_client()
        try:
            if client.connect():
                db_decisions = client.get_all_decisions()
                for d in db_decisions:
                    decisions.append({
                        "decision_id": d.id,
                        "name": d.name,
                        "status": d.status,
                        "date": str(d.decision_date) if d.decision_date else None,
                        "source": "typedb"
                    })
                client.close()
        except Exception as e:
            # BUG-477-EDC-1: Sanitize debug/info logger
            logger.debug(f"TypeDB decisions list failed: {type(e).__name__}")

        # Also scan evidence directory for DECISION-*.md files
        pattern = EVIDENCE_DIR / "DECISION-*.md"
        for filepath in glob.glob(str(pattern)):
            try:
                path = Path(filepath)
                filename = path.name.replace(".md", "")
                # Check if already in list from TypeDB
                if not any(d["decision_id"] == filename for d in decisions):
                    content = path.read_text(encoding="utf-8")
                    # Extract title from first # heading
                    title = filename
                    for line in content.split("\n"):
                        if line.startswith("# "):
                            title = line[2:].strip()
                            break

                    decisions.append({
                        "decision_id": filename,
                        "name": title,
                        "status": "DOCUMENTED",
                        "date": None,
                        "source": "evidence_file"
                    })
            except Exception as e:
                # BUG-477-EDC-2: Sanitize debug/info logger
                logger.debug(f"Failed to parse decision file {filepath}: {type(e).__name__}")
                continue

        return format_mcp_result({
            "decisions": decisions,
            "count": len(decisions)
        })

    @mcp.tool()
    def governance_get_decision(decision_id: str) -> str:
        """
        Get detailed decision information.

        Args:
            decision_id: Decision ID (e.g., "DECISION-003")

        Returns:
            JSON object with decision details, context, rationale, and impacts
        """
        result = {"decision_id": decision_id}

        # Get from TypeDB
        client = get_typedb_client()
        try:
            if client.connect():
                db_decisions = client.get_all_decisions()
                for d in db_decisions:
                    if d.id == decision_id:
                        result["name"] = d.name
                        result["context"] = d.context
                        result["rationale"] = d.rationale
                        result["status"] = d.status
                        result["date"] = str(d.decision_date) if d.decision_date else None
                        result["source"] = "typedb"

                        # Get impacts
                        impacts = client.get_decision_impacts(decision_id)
                        result["affected_rules"] = impacts
                        break

                client.close()
        except Exception as e:
            # BUG-477-EDC-3: Sanitize debug/info logger
            logger.debug(f"TypeDB decision get for {decision_id} failed: {type(e).__name__}")

        # Check for evidence file
        evidence_file = EVIDENCE_DIR / f"{decision_id}.md"
        if not evidence_file.exists():
            # Try with suffix
            matches = list(glob.glob(str(EVIDENCE_DIR / f"{decision_id}*.md")))
            if matches:
                evidence_file = Path(matches[0])

        if evidence_file.exists():
            result["evidence_file"] = str(evidence_file)
            result["evidence_content"] = evidence_file.read_text(encoding="utf-8")

        if len(result) == 1:  # Only has decision_id
            return format_mcp_result({"error": f"Decision {decision_id} not found"})

        return format_mcp_result(result)
