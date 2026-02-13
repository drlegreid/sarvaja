"""
Context Compactor MCP Tools (G.1)
=================================
Compiled view transforms for context window management.

Per EPIC-G: Holographic Memory Model.
Provides zoom-level summaries that preserve session state across compaction.

Zoom levels:
  0: One-line summary (~50 tokens)
  1: Task names + decision summaries (~200 tokens)
  2: Tool call sequence + error patterns (~500 tokens)
  3: Full evidence markdown (~2000+ tokens)

Created: 2026-02-09
"""

import logging
from typing import Optional

from governance.mcp_tools.common import format_mcp_result

logger = logging.getLogger(__name__)


def _get_session_data(session_id: str) -> dict:
    """Fetch session data from store or TypeDB."""
    from governance.stores import _sessions_store, get_typedb_client

    # Try in-memory first (fastest)
    if session_id in _sessions_store:
        return _sessions_store[session_id]

    # Try TypeDB
    client = get_typedb_client()
    if client:
        try:
            session = client.get_session(session_id)
            if session:
                return {
                    "session_id": getattr(session, "id", session_id),
                    "status": getattr(session, "status", "UNKNOWN"),
                    "description": getattr(session, "description", ""),
                    "agent_id": getattr(session, "agent_id", ""),
                }
        except Exception as e:
            logger.debug(f"TypeDB session fetch failed for {session_id}: {e}")
    return {}


def _compile_zoom_0(session_data: dict, tasks: list, tool_calls: list,
                     thoughts: list, decisions: list) -> str:
    """Zoom 0: One-line overview (~50 tokens)."""
    done = sum(1 for t in tasks if t.get("status") in ("DONE", "COMPLETED"))
    return (
        f"Session {session_data.get('session_id', '?')}: "
        f"{len(tasks)} tasks ({done} done), "
        f"{len(tool_calls)} tool calls, "
        f"{len(thoughts)} thoughts, "
        f"{len(decisions)} decisions. "
        f"Status: {session_data.get('status', 'UNKNOWN')}"
    )


def _compile_zoom_1(session_data: dict, tasks: list, tool_calls: list,
                     thoughts: list, decisions: list) -> str:
    """Zoom 1: Task names + decision summaries (~200 tokens)."""
    lines = [_compile_zoom_0(session_data, tasks, tool_calls, thoughts, decisions)]
    if tasks:
        lines.append("\nTasks:")
        for t in tasks[:10]:
            status = t.get("status", "?")
            name = t.get("description", t.get("task_id", "?"))[:60]
            lines.append(f"  [{status}] {name}")
    if decisions:
        lines.append("\nDecisions:")
        for d in decisions[:5]:
            lines.append(f"  - {d.get('name', d.get('decision_id', '?'))[:80]}")
    return "\n".join(lines)


def _compile_zoom_2(session_data: dict, tasks: list, tool_calls: list,
                     thoughts: list, decisions: list) -> str:
    """Zoom 2: Tool call sequence + error patterns (~500 tokens)."""
    lines = [_compile_zoom_1(session_data, tasks, tool_calls, thoughts, decisions)]
    if tool_calls:
        lines.append("\nTool Call Sequence:")
        for tc in tool_calls[:20]:
            name = tc.get("tool_name", "?")
            result = str(tc.get("result", ""))[:50]
            duration = tc.get("duration_ms", "?")
            lines.append(f"  {name} ({duration}ms) -> {result}")
        # Error patterns
        errors = [tc for tc in tool_calls if "error" in str(tc.get("result", "")).lower()]
        if errors:
            lines.append(f"\nErrors: {len(errors)} tool calls had errors")
    if thoughts:
        lines.append("\nKey Thoughts:")
        for th in thoughts[:10]:
            lines.append(f"  [{th.get('thought_type', '?')}] {th.get('thought', '')[:80]}")
    return "\n".join(lines)


def _compile_zoom_3(session_data: dict, tasks: list, tool_calls: list,
                     thoughts: list, decisions: list) -> str:
    """Zoom 3: Full evidence markdown (~2000+ tokens)."""
    lines = [
        f"# Session: {session_data.get('session_id', '?')}",
        f"**Status**: {session_data.get('status', 'UNKNOWN')}",
        f"**Agent**: {session_data.get('agent_id', 'N/A')}",
        f"**Description**: {session_data.get('description', 'N/A')}",
        "",
        f"## Tasks ({len(tasks)})",
    ]
    for t in tasks:
        lines.append(f"- **{t.get('task_id', '?')}** [{t.get('status', '?')}]: "
                      f"{t.get('description', '')[:100]}")
    lines.append(f"\n## Tool Calls ({len(tool_calls)})")
    for tc in tool_calls:
        lines.append(f"- `{tc.get('tool_name', '?')}` ({tc.get('duration_ms', '?')}ms): "
                      f"{str(tc.get('result', ''))[:100]}")
    lines.append(f"\n## Thoughts ({len(thoughts)})")
    for th in thoughts:
        lines.append(f"- [{th.get('thought_type', '?')}] {th.get('thought', '')}")
    lines.append(f"\n## Decisions ({len(decisions)})")
    for d in decisions:
        lines.append(f"- **{d.get('name', '?')}**: {d.get('rationale', '')[:150]}")
    return "\n".join(lines)


def register_context_compactor_tools(mcp) -> None:
    """Register context compactor MCP tools."""

    @mcp.tool()
    def context_compile(
        session_id: Optional[str] = None,
        zoom: int = 1,
    ) -> str:
        """Compile a session into a zoomed summary for context window management.

        Creates a compressed view of session state at different detail levels.
        Use zoom=0 for minimal overview, zoom=3 for full evidence.
        Persists compiled view to ChromaDB for recovery after compaction.

        Args:
            session_id: Session to compile (default: most recent active)
            zoom: Detail level 0-3 (0=minimal, 3=full)

        Returns:
            Compiled session view at the requested zoom level.
        """
        from governance.stores import _sessions_store

        # Find session
        if not session_id:
            # Find most recent ACTIVE session
            active = [
                (sid, data) for sid, data in _sessions_store.items()
                if data.get("status") == "ACTIVE"
            ]
            if active:
                session_id = active[-1][0]
            else:
                return format_mcp_result({
                    "error": "No active session found",
                    "hint": "Pass session_id explicitly",
                })

        session_data = _get_session_data(session_id)
        if not session_data:
            return format_mcp_result({"error": f"Session {session_id} not found"})

        # Gather related data
        store_data = _sessions_store.get(session_id, {})
        tasks = store_data.get("tasks", [])
        tool_calls = store_data.get("tool_calls", [])
        thoughts = store_data.get("thoughts", [])
        decisions = store_data.get("decisions", [])

        zoom = max(0, min(3, zoom))
        compile_fns = [_compile_zoom_0, _compile_zoom_1, _compile_zoom_2, _compile_zoom_3]
        compiled = compile_fns[zoom](session_data, tasks, tool_calls, thoughts, decisions)

        # Persist to ChromaDB for recovery
        try:
            from governance.mcp_tools.common import log_monitor_event
            log_monitor_event("context_compile", "context-compactor",
                              {"session_id": session_id, "zoom": zoom})
        except Exception as e:
            logger.debug(f"Monitor event logging failed: {e}")

        return format_mcp_result({
            "session_id": session_id,
            "zoom": zoom,
            "token_estimate": len(compiled.split()),
            "compiled_view": compiled,
        })
