"""
Core Query Functions (GAP-FILE-007)
===================================
Core backward compatibility exports for rules, sessions, decisions, tasks.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-007: Extracted from mcp_server.py

Created: 2024-12-28
"""

import json
import glob
import re
from pathlib import Path
from dataclasses import asdict

from governance.mcp_tools.common import get_typedb_client
from governance.mcp_tools.evidence import EVIDENCE_DIR, BACKLOG_DIR


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
                    "status": d.status,
                    "decision_date": d.decision_date.isoformat() if d.decision_date else None
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
    """
    List tasks from TypeDB (primary) with markdown fallback.

    Per DECISION-003: TypeDB-First Strategy
    Per P10.4: MCP Tools for CRUD
    """
    # Try TypeDB first (DECISION-003)
    try:
        from governance.client import TypeDBClient
        from dataclasses import asdict

        client = TypeDBClient()
        if client.connect():
            try:
                tasks_from_db = client.get_all_tasks()
                tasks = []
                for t in tasks_from_db:
                    task_dict = asdict(t) if hasattr(t, '__dataclass_fields__') else t
                    # Apply filters
                    task_status = task_dict.get('status', '')
                    task_phase = task_dict.get('phase', '')
                    if phase and task_phase != phase:
                        continue
                    if status and task_status.upper() != status.upper():
                        continue
                    tasks.append({
                        "task_id": task_dict.get('id'),
                        "status": task_status,
                        "phase": task_phase,
                        "description": task_dict.get('name', task_dict.get('description', '')),
                        "agent_id": task_dict.get('agent_id'),
                        "body": task_dict.get('body')
                    })
                return json.dumps({"tasks": tasks, "count": len(tasks), "source": "typedb"}, indent=2)
            finally:
                client.close()
    except Exception:
        pass  # Fall through to markdown fallback

    # Fallback to markdown parsing (backward compatibility)
    tasks = []
    backlog_file = BACKLOG_DIR / "R&D-BACKLOG.md"
    if backlog_file.exists():
        content = backlog_file.read_text(encoding="utf-8")
        table_pattern = r"\|\s*([\w.-]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"
        for match in re.finditer(table_pattern, content):
            task_id = match.group(1).strip()
            status_field = match.group(2).strip()
            if task_id in ("ID", "Task", "Pillar", "Factor") or task_id.startswith("-"):
                continue
            if not re.match(r'^(P\d+\.\d+|RD-\d+|FH-\d+|DOC-\d+|TEST-\d+|TOOL-\d+)', task_id):
                continue
            # Extract phase from task_id
            phase_match = re.match(r'^(P\d+|RD|FH|DOC|TEST|TOOL)', task_id)
            task_phase = phase_match.group(1) if phase_match else "UNKNOWN"
            # Determine status from status field
            if "✅" in status_field or "DONE" in status_field.upper():
                task_status = "DONE"
            elif "📋" in status_field or "TODO" in status_field.upper():
                task_status = "TODO"
            elif "⏸️" in status_field or "BLOCKED" in status_field.upper():
                task_status = "BLOCKED"
            elif "IN_PROGRESS" in status_field.upper() or "IN PROGRESS" in status_field.upper():
                task_status = "IN_PROGRESS"
            else:
                task_status = "TODO"
            # Apply filters
            if phase and task_phase != phase:
                continue
            if status and task_status != status:
                continue
            tasks.append({"task_id": task_id, "status": task_status, "phase": task_phase})
    return json.dumps({"tasks": tasks, "count": len(tasks), "source": "markdown"}, indent=2)


def governance_get_task_deps(task_id):
    """Get task deps (backward compat export)."""
    blocked_by = []
    blocks = []
    # Infer phase dependencies from task_id
    phase_match = re.match(r'^P(\d+)\.', task_id)
    if phase_match:
        current_phase = int(phase_match.group(1))
        # Earlier phases block this task
        for earlier in range(1, current_phase):
            blocked_by.append(f"P{earlier}")
        # This task blocks later phases (up to P10)
        for later in range(current_phase + 1, 11):
            blocks.append(f"P{later}")
    return json.dumps({"task_id": task_id, "blocked_by": blocked_by, "blocks": blocks}, indent=2)


def governance_evidence_search(query, top_k=5, source_type=None):
    """Search evidence (backward compat export)."""
    results = []
    query_lower = query.lower()
    for filepath in glob.glob(str(EVIDENCE_DIR / "*.md")):
        try:
            path = Path(filepath)
            content = path.read_text(encoding="utf-8")
            content_lower = content.lower()
            if query_lower in content_lower:
                # Calculate simple relevance score
                occurrences = content_lower.count(query_lower)
                score = min(1.0, occurrences * 0.1)
                # Determine source_type from filename pattern
                stem = path.stem
                if stem.startswith("SESSION-"):
                    src_type = "session"
                elif stem.startswith("DSM-"):
                    src_type = "dsm"
                elif stem.startswith("DECISION-"):
                    src_type = "decision"
                else:
                    src_type = "evidence"
                results.append({
                    "source": stem,
                    "source_type": src_type,
                    "content": content[:200],
                    "score": round(score, 2)
                })
        except Exception:
            continue
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return json.dumps({
        "query": query,
        "search_method": "keyword_match",
        "results": results[:top_k],
        "count": len(results[:top_k])
    }, indent=2)
