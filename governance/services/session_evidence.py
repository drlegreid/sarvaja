"""Session Evidence Auto-Generation Service.

Generates comprehensive markdown evidence documents from session data,
collating tool calls, decisions, and tasks WITHOUT LLM processing.

Per P0 architectural fix: Sessions completed via REST API or MCP
should automatically have evidence documents generated and attached.

Created: 2026-02-15
"""
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default evidence directory (relative to project root)
_DEFAULT_EVIDENCE_DIR = Path(__file__).parent.parent.parent / "evidence"


def compile_evidence_data(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """Gather and normalize session artifacts into a structured dict.

    Extracts tool calls, decisions, tasks, and metadata from session_data
    (which may come from _sessions_store or TypeDB response).

    Args:
        session_data: Raw session dict with optional tool_calls, decisions, tasks.

    Returns:
        Normalized evidence dict with all required keys.
    """
    session_id = session_data.get("session_id", "UNKNOWN")
    start_time = session_data.get("start_time", "")
    end_time = session_data.get("end_time", "")

    # Compute duration
    duration = _compute_duration(start_time, end_time)

    return {
        "session_id": session_id,
        "start_time": start_time,
        "end_time": end_time,
        "duration": duration,
        "description": session_data.get("description", ""),
        "agent_id": session_data.get("agent_id", ""),
        "status": session_data.get("status", ""),
        "tool_calls": session_data.get("tool_calls", []) or [],
        "decisions": session_data.get("decisions", []) or [],
        "tasks": session_data.get("tasks", []) or [],
        "tasks_completed": session_data.get("tasks_completed"),
    }


def _compute_duration(start_time: str, end_time: str) -> str:
    """Compute human-readable duration between ISO timestamps.

    Returns:
        String like '1h 30m' or 'unknown' if parsing fails.
    """
    if not start_time or not end_time:
        return "unknown"
    try:
        # Handle both full ISO and truncated formats
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                start = datetime.fromisoformat(start_time.replace("Z", ""))
                end = datetime.fromisoformat(end_time.replace("Z", ""))
                break
            except ValueError:
                continue
        else:
            return "unknown"

        delta = end - start
        total_minutes = int(delta.total_seconds() / 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    except Exception:
        return "unknown"


def render_evidence_markdown(evidence_data: Dict[str, Any]) -> str:
    """Convert evidence data dict to a markdown document.

    No LLM is used — this is pure data collation and formatting.

    Args:
        evidence_data: Output of compile_evidence_data().

    Returns:
        Markdown string with session metadata, tool summary, decisions, tasks.
    """
    session_id = evidence_data.get("session_id", "UNKNOWN")
    lines: List[str] = []

    # Header
    lines.append(f"# Session Evidence: {session_id}")
    lines.append("")
    lines.append(f"**Session ID:** {session_id}")
    if evidence_data.get("description"):
        lines.append(f"**Description:** {evidence_data['description']}")
    if evidence_data.get("agent_id"):
        lines.append(f"**Agent:** {evidence_data['agent_id']}")
    lines.append(f"**Status:** {evidence_data.get('status', 'COMPLETED')}")
    lines.append(f"**Start:** {evidence_data.get('start_time', 'N/A')}")
    lines.append(f"**End:** {evidence_data.get('end_time', 'N/A')}")
    lines.append(f"**Duration:** {evidence_data.get('duration', 'unknown')}")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Tool Calls section
    tool_calls = evidence_data.get("tool_calls", [])
    if tool_calls:
        lines.append("## Tool Calls")
        lines.append("")
        lines.append(f"**Total:** {len(tool_calls)}")
        lines.append("")

        # Summary by tool name
        tool_counts = Counter(tc.get("tool_name", "unknown") for tc in tool_calls)
        lines.append("### Tool Summary")
        lines.append("")
        lines.append("| Tool | Count |")
        lines.append("|------|-------|")
        for name, count in tool_counts.most_common():
            lines.append(f"| {name} | {count} |")
        lines.append("")

        # Detailed list (max 50 entries to keep file reasonable)
        if len(tool_calls) <= 50:
            lines.append("### Detailed Log")
            lines.append("")
            for tc in tool_calls:
                ts = tc.get("timestamp", "")
                name = tc.get("tool_name", "unknown")
                args_str = ""
                if tc.get("args"):
                    args_str = f" — `{_truncate(str(tc['args']), 100)}`"
                lines.append(f"- **{ts}** `{name}`{args_str}")
            lines.append("")
        else:
            lines.append(f"_({len(tool_calls)} tool calls — showing summary only)_")
            lines.append("")
    else:
        lines.append("## Tool Calls")
        lines.append("")
        lines.append("_No tool calls recorded._")
        lines.append("")

    # Decisions section
    decisions = evidence_data.get("decisions", [])
    if decisions:
        lines.append("## Decisions")
        lines.append("")
        lines.append("| ID | Title | Rationale |")
        lines.append("|----|-------|-----------|")
        for dec in decisions:
            did = dec.get("decision_id", "N/A")
            title = dec.get("title", "N/A")
            rationale = _truncate(dec.get("rationale", ""), 80)
            lines.append(f"| {did} | {title} | {rationale} |")
        lines.append("")
    else:
        lines.append("## Decisions")
        lines.append("")
        lines.append("_No decisions recorded._")
        lines.append("")

    # Tasks section
    tasks = evidence_data.get("tasks", [])
    if tasks:
        lines.append("## Tasks")
        lines.append("")
        lines.append("| ID | Description | Status |")
        lines.append("|----|-------------|--------|")
        for task in tasks:
            tid = task.get("task_id", "N/A")
            desc = _truncate(task.get("description", "N/A"), 60)
            status = task.get("status", "N/A")
            lines.append(f"| {tid} | {desc} | {status} |")
        lines.append("")
    else:
        lines.append("## Tasks")
        lines.append("")
        lines.append("_No tasks linked._")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("_Auto-generated by session evidence service. No LLM processing._")
    lines.append("")

    return "\n".join(lines)


def _truncate(s: str, max_len: int) -> str:
    """Truncate string to max_len, adding ellipsis if needed."""
    if len(s) <= max_len:
        return s
    return s[:max_len - 3] + "..."


def generate_session_evidence(
    session_data: Dict[str, Any],
    output_dir: Optional[Path] = None,
) -> Optional[str]:
    """Generate an evidence document for a completed session.

    Args:
        session_data: Session dict (from _sessions_store or TypeDB).
        output_dir: Where to write the .md file (default: evidence/).

    Returns:
        Path to the generated evidence file, or None if session is not completed.
    """
    status = session_data.get("status", "")
    if status not in ("COMPLETED", "completed", "DONE"):
        return None

    session_id = session_data.get("session_id", "UNKNOWN")
    output_dir = output_dir or _DEFAULT_EVIDENCE_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    filepath = output_dir / f"{session_id}.md"

    # Idempotent: don't overwrite existing evidence
    if filepath.exists():
        logger.debug(f"Evidence already exists: {filepath}")
        return str(filepath)

    # Compile data and render
    evidence_data = compile_evidence_data(session_data)
    markdown = render_evidence_markdown(evidence_data)

    # Write file
    filepath.write_text(markdown, encoding="utf-8")
    logger.info(f"Generated session evidence: {filepath}")

    return str(filepath)
