"""Evidence generation for session metrics (SESSION-METRICS-01-v1).

Generates markdown evidence reports from MetricsResult data,
and writes them to the evidence/ directory.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional


def generate_evidence_markdown(metrics: dict) -> str:
    """Generate a markdown evidence report from metrics dict.

    Args:
        metrics: Output of MetricsResult.to_dict()

    Returns:
        Markdown string with totals, per-day table, and tool breakdown.
    """
    totals = metrics.get("totals", {})
    days = metrics.get("days", [])
    tool_breakdown = metrics.get("tool_breakdown", {})

    lines = []

    # Title
    date_str = datetime.now().strftime("%Y-%m-%d")
    lines.append(f"# Session Metrics Evidence — {date_str}")
    lines.append("")
    lines.append(f"**Rule:** SESSION-METRICS-01-v1")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}")
    lines.append("")

    # Totals summary
    lines.append("## Totals")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Active Minutes | {totals.get('active_minutes', 0)} |")
    lines.append(f"| Session Count | {totals.get('session_count', 0)} |")
    lines.append(f"| Message Count | {totals.get('message_count', 0)} |")
    lines.append(f"| Tool Calls | {totals.get('tool_calls', 0)} |")
    lines.append(f"| MCP Calls | {totals.get('mcp_calls', 0)} |")
    lines.append(f"| Thinking Chars | {totals.get('thinking_chars', 0)} |")
    lines.append(f"| Days Covered | {totals.get('days_covered', 0)} |")
    lines.append(f"| API Errors | {totals.get('api_errors', 0)} |")
    lines.append(f"| Error Rate | {totals.get('error_rate', 0.0)} |")
    lines.append("")

    # Per-day breakdown
    if days:
        lines.append("## Per-Day Breakdown")
        lines.append("")
        lines.append("| Date | Active Min | Sessions | Messages | Tools | MCP | Errors |")
        lines.append("|------|-----------|----------|----------|-------|-----|--------|")
        for day in days:
            lines.append(
                f"| {day['date']} "
                f"| {day.get('active_minutes', 0)} "
                f"| {day.get('session_count', 0)} "
                f"| {day.get('message_count', 0)} "
                f"| {day.get('tool_calls', 0)} "
                f"| {day.get('mcp_calls', 0)} "
                f"| {day.get('api_errors', 0)} |"
            )
        lines.append("")

    # Tool breakdown
    if tool_breakdown:
        lines.append("## Tool Breakdown")
        lines.append("")
        lines.append("| Tool | Count |")
        lines.append("|------|-------|")
        for name, count in sorted(tool_breakdown.items(), key=lambda x: -x[1]):
            lines.append(f"| {name} | {count} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Per SESSION-METRICS-01-v1 | Auto-generated evidence*")

    return "\n".join(lines)


def write_evidence_file(
    metrics: dict,
    output_dir: Optional[Path] = None,
    date_str: Optional[str] = None,
) -> Path:
    """Write evidence markdown to a file.

    Args:
        metrics: Output of MetricsResult.to_dict()
        output_dir: Directory for output (default: evidence/)
        date_str: Override date string (default: today)

    Returns:
        Path to the written file.
    """
    if output_dir is None:
        output_dir = Path("evidence")

    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"SESSION-{date_str}-METRICS.md"
    filepath = output_dir / filename

    content = generate_evidence_markdown(metrics)
    filepath.write_text(content, encoding="utf-8")

    return filepath
