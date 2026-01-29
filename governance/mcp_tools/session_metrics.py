"""
Session Metrics MCP Tools
=========================
Claude Code JSONL log analytics.

Per SESSION-METRICS-01-v1: Session duration extraction from Claude Code logs.
Per RULE-012: DSP Semantic Code Structure.
"""

import os
from pathlib import Path
from typing import Optional

from governance.mcp_tools.common import format_mcp_result


def _resolve_project_dir(project_path: Optional[str] = None) -> Path:
    """Resolve Claude Code project log directory.

    Auto-detects from cwd if project_path is None.
    Converts cwd to Claude Code's slug format: /home/user/project → -home-user-project
    """
    if project_path:
        return Path(project_path)

    cwd = os.getcwd()
    slug = cwd.replace("/", "-").lstrip("-")
    slug = "-" + slug if not slug.startswith("-") else slug
    return Path.home() / ".claude" / "projects" / slug


def register_session_metrics_tools(mcp) -> None:
    """Register session metrics MCP tools."""

    @mcp.tool()
    def session_metrics(
        days: int = 5,
        project_path: Optional[str] = None,
        idle_threshold_min: int = 30,
        include_thinking: bool = False,
    ) -> str:
        """Parse Claude Code JSONL session logs and return duration analytics.

        Extracts session duration, tool call metadata, thinking process stats,
        and per-day aggregated metrics from local Claude Code log files.

        Args:
            days: Number of days to include (default: 5)
            project_path: Override project log directory (auto-detect if None)
            idle_threshold_min: Minutes of idle to split sessions (default: 30)
            include_thinking: Include thinking block char counts (default: False)

        Returns:
            JSON with per-day breakdown, totals, tool breakdown, and metadata.
        """
        from governance.session_metrics.parser import (
            discover_log_files,
            parse_log_file,
        )
        from governance.session_metrics.calculator import (
            calculate_metrics,
            filter_entries_by_days,
        )

        log_dir = _resolve_project_dir(project_path)

        if not log_dir.is_dir():
            return format_mcp_result({
                "error": f"Log directory not found: {log_dir}",
                "hint": "Provide project_path or ensure Claude Code has been used in this project.",
            })

        log_files = discover_log_files(log_dir, include_agents=False)
        if not log_files:
            return format_mcp_result({
                "error": f"No JSONL log files found in: {log_dir}",
            })

        # Parse all main log files
        all_entries = []
        total_lines = 0
        for lf in log_files:
            for entry in parse_log_file(lf, include_thinking=include_thinking):
                all_entries.append(entry)
                total_lines += 1

        if not all_entries:
            return format_mcp_result({
                "error": "No parseable entries found in log files.",
            })

        # Filter by date range
        filtered = filter_entries_by_days(all_entries, days=days)

        # Calculate metrics
        metrics = calculate_metrics(filtered, idle_threshold_min=idle_threshold_min)
        result = metrics.to_dict()

        # Add metadata
        result["metadata"] = {
            "log_dir": str(log_dir),
            "log_files": [f.name for f in log_files],
            "total_entries_parsed": total_lines,
            "entries_in_range": len(filtered),
            "idle_threshold_min": idle_threshold_min,
            "days_requested": days,
        }

        return format_mcp_result(result)
