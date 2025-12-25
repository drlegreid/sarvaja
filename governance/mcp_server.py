"""
Governance MCP Server - Multi-Agent Conflict Resolution
========================================================
Thin coordinator (per DSP FP + Digital Twin paradigm).

Created: 2024-12-24 (RULE-011, DECISION-005)
Refactored: 2024-12-25 (DSP Semantic Restructure)

Protocol: MCP (Model Context Protocol)
Backend: TypeDB 2.29.1

Structure (per RULE-012):
    mcp_tools/           - MCP tools by entity/concern
        rules.py         - Rule query/CRUD
        trust.py         - Trust score operations
        proposals.py     - Proposal/vote/dispute
        decisions.py     - Decision impact
        sessions.py      - Session evidence
        dsm.py           - DSM tracker (RULE-012)
        evidence.py      - Evidence viewing

Usage:
    python governance/mcp_server.py

Or add to MCP config:
    {
        "governance": {
            "command": "python",
            "args": ["governance/mcp_server.py"],
            "env": {"TYPEDB_HOST": "localhost", "TYPEDB_PORT": "1729"}
        }
    }
"""

import os
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("governance")

# =============================================================================
# REGISTER ALL TOOLS FROM mcp_tools PACKAGE
# =============================================================================

from governance.mcp_tools import register_all_tools
register_all_tools(mcp)


# =============================================================================
# BACKWARD COMPATIBILITY EXPORTS
# =============================================================================
# These functions are used by agent/governance_ui/data_access.py
# They wrap the internal implementations for direct Python calls

import json
from governance.mcp_tools.common import get_typedb_client
from governance.mcp_tools.evidence import EVIDENCE_DIR, BACKLOG_DIR
import glob
import re
from pathlib import Path
from dataclasses import asdict


def governance_query_rules(category=None, status=None, priority=None):
    """Query rules (backward compat export)."""
    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})
        if status == "ACTIVE":
            rules = client.get_active_rules()
        else:
            rules = client.get_all_rules()
        if category:
            rules = [r for r in rules if r.category == category]
        if priority:
            rules = [r for r in rules if r.priority == priority]
        if status and status != "ACTIVE":
            rules = [r for r in rules if r.status == status]
        return json.dumps([asdict(r) for r in rules], default=str, indent=2)
    finally:
        client.close()


def governance_list_sessions(limit=20, session_type=None):
    """List sessions (backward compat export)."""
    sessions = []
    pattern = EVIDENCE_DIR / "SESSION-*.md"
    for filepath in sorted(glob.glob(str(pattern)), reverse=True)[:limit]:
        try:
            path = Path(filepath)
            filename = path.name
            parts = filename.replace(".md", "").split("-")
            if len(parts) >= 4:
                date_str = f"{parts[1]}-{parts[2]}-{parts[3]}"
                topic = "-".join(parts[4:]) if len(parts) > 4 else "general"
            else:
                date_str = "unknown"
                topic = filename
            if session_type and session_type.upper() not in topic.upper():
                continue
            sessions.append({
                "session_id": filename.replace(".md", ""),
                "date": date_str,
                "topic": topic,
                "path": str(filepath)
            })
        except Exception:
            continue
    return json.dumps({"sessions": sessions, "count": len(sessions)}, indent=2)


def governance_get_session(session_id):
    """Get session (backward compat export)."""
    if not session_id.endswith(".md"):
        session_id = session_id + ".md"
    filepath = EVIDENCE_DIR / session_id
    if not filepath.exists():
        return json.dumps({"error": f"Session not found: {session_id}"})
    try:
        content = filepath.read_text(encoding="utf-8")
        return json.dumps({
            "session_id": session_id.replace(".md", ""),
            "content": content
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def governance_list_decisions():
    """List decisions (backward compat export)."""
    decisions = []
    client = get_typedb_client()
    try:
        if client.connect():
            db_decisions = client.get_all_decisions()
            for d in db_decisions:
                decisions.append({
                    "decision_id": d.id,
                    "name": d.name,
                    "status": d.status
                })
            client.close()
    except Exception:
        pass
    return json.dumps({"decisions": decisions, "count": len(decisions)}, indent=2)


def governance_get_decision(decision_id):
    """Get decision (backward compat export)."""
    result = {"decision_id": decision_id}
    client = get_typedb_client()
    try:
        if client.connect():
            db_decisions = client.get_all_decisions()
            for d in db_decisions:
                if d.id == decision_id:
                    result["name"] = d.name
                    result["status"] = d.status
                    break
            client.close()
    except Exception:
        pass
    if len(result) == 1:
        return json.dumps({"error": f"Decision {decision_id} not found"})
    return json.dumps(result, indent=2)


def governance_list_tasks(phase=None, status=None):
    """List tasks (backward compat export)."""
    tasks = []
    backlog_file = BACKLOG_DIR / "R&D-BACKLOG.md"
    if backlog_file.exists():
        content = backlog_file.read_text(encoding="utf-8")
        table_pattern = r"\|\s*([\w.-]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"
        for match in re.finditer(table_pattern, content):
            task_id = match.group(1).strip()
            if task_id in ("ID", "Task", "Pillar") or task_id.startswith("-"):
                continue
            if not re.match(r'^(P\d+\.\d+|RD-\d+|FH-\d+)', task_id):
                continue
            tasks.append({"task_id": task_id, "status": "TODO"})
    return json.dumps({"tasks": tasks, "count": len(tasks)}, indent=2)


def governance_get_task_deps(task_id):
    """Get task deps (backward compat export)."""
    return json.dumps({"task_id": task_id, "blocked_by": [], "blocks": []}, indent=2)


def governance_evidence_search(query, top_k=5, source_type=None):
    """Search evidence (backward compat export)."""
    results = []
    query_lower = query.lower()
    for filepath in glob.glob(str(EVIDENCE_DIR / "*.md")):
        try:
            path = Path(filepath)
            content = path.read_text(encoding="utf-8")
            if query_lower in content.lower():
                results.append({"source": path.stem, "content": content[:200]})
        except Exception:
            continue
    return json.dumps({"results": results[:top_k], "count": len(results[:top_k])}, indent=2)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    from governance.mcp_tools.common import TYPEDB_HOST, TYPEDB_PORT, DATABASE_NAME

    print("Starting Governance MCP Server...")
    print(f"TypeDB: {TYPEDB_HOST}:{TYPEDB_PORT}/{DATABASE_NAME}")
    print("Tools registered from governance.mcp_tools package")
    mcp.run()
