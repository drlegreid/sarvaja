"""
Session Metrics Data Access (GAP-SESSION-METRICS-UI)
====================================================
Data access functions for session metrics dashboard.

Per RULE-012: DSP Semantic Code Structure
Per SESSION-METRICS-01-v1: Session analytics

Created: 2026-01-29
"""

import os
from typing import Dict, Any, Optional

import httpx

# API base URL - configurable via environment
_API_BASE_URL = os.environ.get("GOVERNANCE_API_URL", "http://localhost:8082")


def get_session_metrics_summary(
    days: int = 5,
    idle_threshold_min: int = 30,
) -> Dict[str, Any]:
    """Fetch session metrics summary from API.

    Args:
        days: Number of days to include
        idle_threshold_min: Idle threshold for session splitting

    Returns:
        Metrics dict with totals, days, tool_breakdown, correlation, agents
    """
    try:
        with httpx.Client(base_url=_API_BASE_URL, timeout=30.0) as client:
            response = client.get(
                "/api/metrics/summary",
                params={"days": days, "idle_threshold_min": idle_threshold_min},
            )
            if response.status_code == 200:
                return response.json()
            return {
                "error": f"Failed to fetch metrics: {response.status_code}",
                "totals": {},
                "days": [],
                "tool_breakdown": {},
            }
    except Exception as e:
        return {
            "error": str(e),
            "totals": {},
            "days": [],
            "tool_breakdown": {},
        }


def search_session_content(
    query: str = "",
    session_id: Optional[str] = None,
    git_branch: Optional[str] = None,
    max_results: int = 50,
) -> Dict[str, Any]:
    """Search session logs via API.

    Args:
        query: Text to search for
        session_id: Optional session ID filter
        git_branch: Optional git branch filter
        max_results: Maximum results

    Returns:
        Dict with results list and total_matches
    """
    try:
        params: Dict[str, Any] = {"query": query, "max_results": max_results}
        if session_id:
            params["session_id"] = session_id
        if git_branch:
            params["git_branch"] = git_branch

        with httpx.Client(base_url=_API_BASE_URL, timeout=30.0) as client:
            response = client.get("/api/metrics/search", params=params)
            if response.status_code == 200:
                return response.json()
            return {
                "error": f"Search failed: {response.status_code}",
                "results": [],
                "total_matches": 0,
            }
    except Exception as e:
        return {
            "error": str(e),
            "results": [],
            "total_matches": 0,
        }


def get_activity_timeline(days: int = 30) -> Dict[str, Any]:
    """Fetch activity timeline from API.

    Args:
        days: Number of days to include

    Returns:
        Dict with timeline list and metadata
    """
    try:
        with httpx.Client(base_url=_API_BASE_URL, timeout=30.0) as client:
            response = client.get(
                "/api/metrics/timeline",
                params={"days": days},
            )
            if response.status_code == 200:
                return response.json()
            return {
                "error": f"Timeline failed: {response.status_code}",
                "timeline": [],
            }
    except Exception as e:
        return {
            "error": str(e),
            "timeline": [],
        }
