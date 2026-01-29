"""
Session Metrics Routes.

Per SESSION-METRICS-01-v1: REST API endpoints for session analytics.
Per GAP-SESSION-METRICS-UI Phase 1: API routes.
Per RULE-012: DSP Semantic Code Structure.

Created: 2026-01-29
"""

from fastapi import APIRouter, Query
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Session Metrics"])


# =============================================================================
# INTERNAL HELPERS (called by endpoints, mockable in tests)
# =============================================================================

def _get_session_metrics(
    days: int = 5,
    idle_threshold_min: int = 30,
) -> dict:
    """Compute session metrics from Claude Code JSONL logs.

    Wraps the session_metrics engine for REST API consumption.
    """
    from governance.session_metrics.parser import discover_log_files, parse_log_file
    from governance.session_metrics.calculator import calculate_metrics, filter_entries_by_days
    from governance.session_metrics.correlation import correlate_tool_calls, summarize_correlation
    from governance.session_metrics.agents import calculate_agent_metrics
    from governance.mcp_tools.session_metrics import _resolve_project_dir

    log_dir = _resolve_project_dir()

    if not log_dir.is_dir():
        return {"error": f"Log directory not found: {log_dir}"}

    log_files = discover_log_files(log_dir, include_agents=False)
    if not log_files:
        return {"error": f"No JSONL log files found in: {log_dir}"}

    all_entries = []
    for lf in log_files:
        for entry in parse_log_file(lf, include_thinking=False):
            all_entries.append(entry)

    if not all_entries:
        return {"error": "No parseable entries found in log files."}

    filtered = filter_entries_by_days(all_entries, days=days)
    metrics = calculate_metrics(filtered, idle_threshold_min=idle_threshold_min)
    result = metrics.to_dict()

    # Correlation
    correlated = correlate_tool_calls(filtered)
    result["correlation"] = summarize_correlation(correlated)

    # Agent metrics
    result["agents"] = calculate_agent_metrics(log_dir)

    # Metadata
    result["metadata"] = {
        "log_dir": str(log_dir),
        "log_files": [f.name for f in log_files],
        "total_entries_parsed": len(all_entries),
        "entries_in_range": len(filtered),
        "days_requested": days,
    }

    return result


def _search_session_content(
    query: str = "",
    session_id: Optional[str] = None,
    git_branch: Optional[str] = None,
    max_results: int = 50,
) -> dict:
    """Search session logs by content, session ID, or git branch."""
    from governance.session_metrics.parser import discover_log_files, parse_log_file_extended
    from governance.session_metrics.search import search_entries, results_to_dicts
    from governance.mcp_tools.session_metrics import _resolve_project_dir

    log_dir = _resolve_project_dir()

    if not log_dir.is_dir():
        return {"error": f"Log directory not found: {log_dir}"}

    log_files = discover_log_files(log_dir, include_agents=False)
    if not log_files:
        return {"error": f"No JSONL log files found in: {log_dir}"}

    all_entries = []
    for lf in log_files:
        for entry in parse_log_file_extended(lf):
            all_entries.append(entry)

    results = search_entries(
        all_entries,
        query=query,
        session_id=session_id,
        git_branch=git_branch,
        max_results=max_results,
    )

    return {
        "results": results_to_dicts(results),
        "total_matches": len(results),
        "metadata": {
            "total_entries_searched": len(all_entries),
            "query": query,
            "session_id": session_id,
            "git_branch": git_branch,
        },
    }


def _get_activity_timeline(days: int = 30) -> list:
    """Generate per-day activity timeline."""
    from governance.session_metrics.parser import discover_log_files, parse_log_file_extended
    from governance.session_metrics.calculator import filter_entries_by_days
    from governance.session_metrics.temporal import activity_timeline
    from governance.mcp_tools.session_metrics import _resolve_project_dir

    log_dir = _resolve_project_dir()

    if not log_dir.is_dir():
        return []

    log_files = discover_log_files(log_dir, include_agents=False)
    if not log_files:
        return []

    all_entries = []
    for lf in log_files:
        for entry in parse_log_file_extended(lf):
            all_entries.append(entry)

    filtered = filter_entries_by_days(all_entries, days=days)
    return activity_timeline(filtered)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/metrics/summary")
async def get_metrics_summary(
    days: int = Query(5, ge=1, le=365, description="Number of days to include"),
    idle_threshold_min: int = Query(30, ge=5, le=120, description="Idle threshold in minutes"),
):
    """Get aggregated session metrics summary.

    Per SESSION-METRICS-01-v1: Parses Claude Code JSONL logs and returns
    totals, per-day breakdown, tool breakdown, correlation, and agent metrics.
    """
    return _get_session_metrics(days=days, idle_threshold_min=idle_threshold_min)


@router.get("/metrics/search")
async def search_session_content(
    query: str = Query("", description="Text to search for (case-insensitive)"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    git_branch: Optional[str] = Query(None, description="Filter by git branch"),
    max_results: int = Query(50, ge=1, le=500, description="Maximum results"),
):
    """Search session logs by content, session ID, or git branch.

    Per SESSION-METRICS-01-v1: Provides deliberate content/decision search
    within session transcripts.
    """
    return _search_session_content(
        query=query,
        session_id=session_id,
        git_branch=git_branch,
        max_results=max_results,
    )


@router.get("/metrics/timeline")
async def get_activity_timeline(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
):
    """Get per-day activity timeline summary.

    Per SESSION-METRICS-01-v1: Returns daily activity summaries with
    tools used, git branches, and text snippets.
    """
    timeline = _get_activity_timeline(days=days)
    return {
        "timeline": timeline,
        "metadata": {
            "days_requested": days,
            "days_returned": len(timeline),
        },
    }
