"""
Workflow Compliance API Client.

Per DOC-SIZE-01-v1: Extracted from workflow_compliance.py.
Provides REST API data fetching for compliance checks.

Created: 2026-01-20
"""

import logging
import os
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# API base URL - configurable for container vs local
API_BASE = os.environ.get("GOVERNANCE_API_URL", "http://localhost:8082")


def fetch_tasks() -> List[Dict[str, Any]]:
    """Fetch all tasks from REST API."""
    try:
        import httpx
        response = httpx.get(f"{API_BASE}/api/tasks", timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                return data.get("items", data.get("tasks", []))
            return data
    except Exception as e:
        # BUG-474-WAC-1: Sanitize logger message + add exc_info for stack trace preservation
        logger.error(f"Failed to fetch tasks: {type(e).__name__}", exc_info=True)
    return []


def fetch_rules() -> List[Dict[str, Any]]:
    """Fetch all rules from REST API."""
    try:
        import httpx
        response = httpx.get(f"{API_BASE}/api/rules", timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return data
            return data.get("rules", data.get("items", []))
    except Exception as e:
        # BUG-474-WAC-2: Sanitize logger message + add exc_info for stack trace preservation
        logger.error(f"Failed to fetch rules: {type(e).__name__}", exc_info=True)
    return []


def fetch_sessions() -> List[Dict[str, Any]]:
    """Fetch all sessions from REST API."""
    try:
        import httpx
        response = httpx.get(f"{API_BASE}/api/sessions?limit=100", timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            return data.get("sessions", []) if isinstance(data, dict) else data
    except Exception as e:
        # BUG-474-WAC-3: Sanitize logger message + add exc_info for stack trace preservation
        logger.error(f"Failed to fetch sessions: {type(e).__name__}", exc_info=True)
    return []
