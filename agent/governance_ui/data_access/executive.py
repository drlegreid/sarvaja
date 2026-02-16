"""
Executive Reports Functions (GAP-FILE-006)
===========================================
Executive reports for GAP-UI-044.

Per RULE-012: DSP Semantic Code Structure
Per RULE-029: Executive Reporting Pattern
Per GAP-FILE-006: Extracted from data_access.py

Created: 2024-12-28
"""

import os
from typing import Dict, Any, Optional


def get_executive_report(
    session_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch executive report from API.

    Per GAP-UI-044: Executive Reporting UI
    Per RULE-029: Executive Reporting Pattern

    Args:
        session_id: Optional session ID to generate report for
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)

    Returns:
        Executive report dict with sections and metrics
    """
    try:
        import httpx

        params = {}
        if session_id:
            params["session_id"] = session_id
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        base_url = api_base_url or os.environ.get("GOVERNANCE_API_URL", "http://localhost:8082")
        with httpx.Client(base_url=base_url, timeout=15.0) as client:
            response = client.get("/api/reports/executive", params=params)
            if response.status_code == 200:
                return response.json()
            return {
                "error": f"Failed to fetch report: {response.status_code}",
                "sections": [],
                "overall_status": "error",
                "metrics_summary": {},
            }
    except Exception as e:
        return {
            "error": str(e),
            "sections": [],
            "overall_status": "error",
            "metrics_summary": {},
        }
