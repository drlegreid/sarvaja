"""
Task Metrics MCP Tools (H.2)
============================
Task velocity, completion rates, and search.

Per EPIC-H: Gov-Tasks MCP Parity with Gov-Sessions.
Mirrors session_metrics pattern for tasks.

Created: 2026-02-09
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from collections import Counter

from governance.mcp_tools.common import format_mcp_result

logger = logging.getLogger(__name__)


def register_task_metrics_tools(mcp) -> None:
    """Register task metrics MCP tools."""

    @mcp.tool()
    def task_metrics(days: int = 7) -> str:
        """Calculate task velocity and completion metrics.

        Provides task throughput, completion rates, agent performance,
        and status distribution over the specified time period.

        Args:
            days: Number of days to analyze (default: 7)

        Returns:
            Task metrics including velocity, completion rate, and agent stats.
        """
        from governance.services.tasks import list_tasks

        result = list_tasks(limit=500)
        all_tasks = result.get("items", [])

        # Time filter
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [t for t in all_tasks if (t.get("created_at") or "") >= cutoff
                  or (t.get("updated_at") or "") >= cutoff]

        # Status distribution
        status_counts = Counter(t.get("status", "UNKNOWN") for t in recent)

        # Completion rate
        total = len(recent)
        done = status_counts.get("DONE", 0) + status_counts.get("COMPLETED", 0)
        rate = round(done / total * 100, 1) if total else 0

        # Agent performance
        agent_stats = {}
        for t in recent:
            agent = t.get("agent_id") or "(unassigned)"
            if agent not in agent_stats:
                agent_stats[agent] = {"total": 0, "done": 0}
            agent_stats[agent]["total"] += 1
            if t.get("status") in ("DONE", "COMPLETED"):
                agent_stats[agent]["done"] += 1

        # Phase distribution
        phase_counts = Counter(t.get("phase", "UNKNOWN") for t in recent)

        # Velocity: tasks completed per day
        velocity = round(done / max(days, 1), 1)

        return format_mcp_result({
            "period_days": days,
            "total_tasks": total,
            "velocity": velocity,
            "completion_rate_pct": rate,
            "status_distribution": dict(status_counts),
            "phase_distribution": dict(phase_counts),
            "agent_performance": agent_stats,
            "all_tasks_total": len(all_tasks),
        })

    @mcp.tool()
    def task_search(query: str, limit: int = 10) -> str:
        """Search tasks by content across descriptions, IDs, and details.

        Args:
            query: Search query (case-insensitive substring match)
            limit: Max results to return

        Returns:
            Matching tasks with relevance ranking.
        """
        from governance.services.tasks import list_tasks

        result = list_tasks(limit=500)
        all_tasks = result.get("items", [])

        query_lower = query.lower()
        matches = []
        for t in all_tasks:
            score = 0
            tid = (t.get("task_id") or "").lower()
            desc = (t.get("description") or "").lower()
            phase = (t.get("phase") or "").lower()

            if query_lower in tid:
                score += 3
            if query_lower in desc:
                score += 2
            if query_lower in phase:
                score += 1

            if score > 0:
                matches.append({
                    "task_id": t.get("task_id"),
                    "description": (t.get("description") or "")[:150],
                    "status": t.get("status"),
                    "phase": t.get("phase"),
                    "agent_id": t.get("agent_id"),
                    "relevance": score,
                })

        matches.sort(key=lambda m: m["relevance"], reverse=True)
        return format_mcp_result({
            "query": query,
            "total_matches": len(matches),
            "results": matches[:limit],
        })
