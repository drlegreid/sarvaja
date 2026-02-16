"""TypeQL query builders for session metrics (SESSION-METRICS-01-v1).

Generates TypeQL insert queries for persisting session metrics
into TypeDB as work-session + evidence-file entities.

Note: These are query builders only — no TypeDB connection required.
Actual execution is done by the MCP tool layer.
"""

from __future__ import annotations

from datetime import datetime


def _escape_typeql(s: str) -> str:
    """Escape a string for safe TypeQL interpolation.

    BUG-TYPEDB-QUERIES-ESCAPE-INCOMPLETE-001: Handle newlines + backslashes + quotes.
    """
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


def build_metrics_insert_query(
    session_id: str,
    metrics: dict,
) -> str:
    """Build a TypeQL insert query for a session metrics work-session entity.

    Args:
        session_id: Session identifier (e.g., SESSION-2026-01-29-METRICS)
        metrics: Output of MetricsResult.to_dict()

    Returns:
        TypeQL insert query string.
    """
    totals = metrics.get("totals", {})
    active = totals.get("active_minutes", 0)
    sessions = totals.get("session_count", 0)
    messages = totals.get("message_count", 0)
    tools = totals.get("tool_calls", 0)
    mcp = totals.get("mcp_calls", 0)
    errors = totals.get("api_errors", 0)
    days = totals.get("days_covered", 0)

    description = (
        f"Session metrics: {active} active_minutes, "
        f"{sessions} sessions, {messages} messages, "
        f"{tools} tool_calls, {mcp} mcp_calls, "
        f"{errors} api_errors over {days} days"
    )
    desc_escaped = _escape_typeql(description)

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    # BUG-TYPEQL-METRICS-001: Escape all fields for TypeQL consistency
    session_id_escaped = _escape_typeql(session_id)
    name = f"Metrics Report {session_id}"
    name_escaped = _escape_typeql(name)

    return (
        f'insert $s isa work-session,\n'
        f'    has session-id "{session_id_escaped}",\n'
        f'    has session-name "{name_escaped}",\n'
        f'    has session-description "{desc_escaped}",\n'
        f'    has started-at {now};'
    )


def build_evidence_insert_query(
    evidence_id: str,
    source: str,
    evidence_type: str,
    content_preview: str,
) -> str:
    """Build a TypeQL insert query for an evidence-file entity.

    Args:
        evidence_id: Evidence identifier
        source: Source system (e.g., "session_metrics")
        evidence_type: Type of evidence (e.g., "metrics")
        content_preview: Short content preview (truncated to 200 chars)

    Returns:
        TypeQL insert query string.
    """
    preview = _escape_typeql(content_preview[:200])
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    # BUG-TYPEQL-METRICS-001: Escape all fields for TypeQL consistency
    evidence_id_escaped = _escape_typeql(evidence_id)
    source_escaped = _escape_typeql(source)
    type_escaped = _escape_typeql(evidence_type)

    return (
        f'insert $e isa evidence-file,\n'
        f'    has evidence-id "{evidence_id_escaped}",\n'
        f'    has evidence-source "{source_escaped}",\n'
        f'    has evidence-type "{type_escaped}",\n'
        f'    has evidence-content-preview "{preview}",\n'
        f'    has evidence-created-at {now};'
    )


def build_evidence_link_query(
    session_id: str,
    evidence_id: str,
) -> str:
    """Build a TypeQL query to link a session to its evidence file.

    Creates a has-evidence relation between work-session and evidence-file.

    Args:
        session_id: Session identifier
        evidence_id: Evidence identifier

    Returns:
        TypeQL insert query string.
    """
    # BUG-TYPEQL-METRICS-001: Escape all fields for TypeQL consistency
    session_id_escaped = _escape_typeql(session_id)
    evidence_id_escaped = _escape_typeql(evidence_id)
    return (
        f'match\n'
        f'    $s isa work-session, has session-id "{session_id_escaped}";\n'
        f'    $e isa evidence-file, has evidence-id "{evidence_id_escaped}";\n'
        f'insert\n'
        f'    (evidence-session: $s, session-evidence: $e) isa has-evidence;'
    )
