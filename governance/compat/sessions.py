"""
Session Collector Exports (GAP-FILE-007)
========================================
Session backward compatibility exports for test imports.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-007: Extracted from mcp_server.py

Created: 2024-12-28
"""

import json

# Try to import session collector
try:
    from governance.session_collector import (
        SessionCollector,
        get_or_create_session,
        end_session as _end_session,
        list_active_sessions
    )
    from governance.client import TypeDBClient
    _SESSION_AVAILABLE = True
    _TYPEDB_AVAILABLE = True
except ImportError:
    _SESSION_AVAILABLE = False
    _TYPEDB_AVAILABLE = False


def session_start(topic, session_type="general"):
    """Start session (backward compat export)."""
    if not _SESSION_AVAILABLE:
        return json.dumps({"error": "SessionCollector not available"})
    collector = get_or_create_session(topic, session_type)
    return json.dumps({
        "session_id": collector.session_id,
        "topic": topic,
        "session_type": session_type,
        "started_at": collector.start_time.isoformat(),
        "message": f"Session started: {collector.session_id}"
    }, indent=2)


def session_decision(decision_id, name, context, rationale, topic=None):
    """Record decision (backward compat export)."""
    if not _SESSION_AVAILABLE:
        return json.dumps({"error": "SessionCollector not available"})
    sessions = list_active_sessions()
    if not sessions and not topic:
        return json.dumps({"error": "No active session. Call session_start first."})
    collector = get_or_create_session(topic or sessions[-1].split("-")[-1].lower() if sessions else "general")
    decision = collector.capture_decision(
        decision_id=decision_id,
        name=name,
        context=context,
        rationale=rationale
    )
    return json.dumps({
        "decision_id": decision_id,
        "session_id": collector.session_id,
        "name": name,
        "indexed_to_typedb": _TYPEDB_AVAILABLE,
        "message": f"Decision {decision_id} recorded and indexed"
    }, indent=2)


def session_task(task_id, name, description, status="pending", priority="MEDIUM", topic=None):
    """Record task (backward compat export)."""
    if not _SESSION_AVAILABLE:
        return json.dumps({"error": "SessionCollector not available"})
    sessions = list_active_sessions()
    if not sessions and not topic:
        return json.dumps({"error": "No active session. Call session_start first."})
    collector = get_or_create_session(topic or sessions[-1].split("-")[-1].lower() if sessions else "general")
    task = collector.capture_task(
        task_id=task_id,
        name=name,
        description=description,
        status=status,
        priority=priority
    )
    return json.dumps({
        "task_id": task_id,
        "session_id": collector.session_id,
        "name": name,
        "status": status,
        "message": f"Task {task_id} recorded"
    }, indent=2)


def session_end(topic):
    """End session (backward compat export)."""
    if not _SESSION_AVAILABLE:
        return json.dumps({"error": "SessionCollector not available"})
    log_path = _end_session(topic)
    if log_path:
        return json.dumps({
            "topic": topic,
            "log_path": log_path,
            "synced_to_chromadb": True,
            "message": f"Session ended. Log: {log_path}"
        }, indent=2)
    else:
        return json.dumps({"error": f"Session for topic '{topic}' not found"})


def session_list():
    """List sessions (backward compat export)."""
    if not _SESSION_AVAILABLE:
        return json.dumps({"error": "SessionCollector not available"})
    sessions = list_active_sessions()
    return json.dumps({
        "active_sessions": sessions,
        "count": len(sessions)
    }, indent=2)
