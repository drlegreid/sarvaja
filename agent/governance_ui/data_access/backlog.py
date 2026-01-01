"""
Agent Task Backlog Functions (GAP-FILE-006)
============================================
Agent task backlog data access for TODO-6.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-006: Extracted from data_access.py

Created: 2024-12-28
"""

import os
import httpx
from typing import Dict, List, Any, Optional

# API base URL - configurable via environment
_API_BASE_URL = os.environ.get("GOVERNANCE_API_URL", "http://localhost:8082")


def get_api_base_url() -> str:
    """Get the configured API base URL."""
    return _API_BASE_URL


def get_available_tasks() -> List[Dict[str, Any]]:
    """
    Get tasks available for agents to claim.

    Per TODO-6: Agent Task Backlog UI
    Calls GET /api/tasks/available endpoint.

    Returns:
        List of task dicts with status=TODO and no agent_id
    """
    try:
        with httpx.Client(base_url=_API_BASE_URL, timeout=10.0) as client:
            response = client.get("/api/tasks/available")
            if response.status_code == 200:
                return response.json()
            return []
    except Exception:
        return []


def claim_task(task_id: str, agent_id: str) -> Dict[str, Any]:
    """
    Agent claims a task.

    Per TODO-6: Agent Task Backlog UI
    Calls PUT /api/tasks/{task_id}/claim endpoint.

    Args:
        task_id: Task ID to claim
        agent_id: Agent ID claiming the task

    Returns:
        Updated task dict or error dict
    """
    try:
        with httpx.Client(base_url=_API_BASE_URL, timeout=10.0) as client:
            response = client.put(
                f"/api/tasks/{task_id}/claim",
                params={"agent_id": agent_id}
            )
            if response.status_code == 200:
                return response.json()
            return {"error": response.text, "status_code": response.status_code}
    except Exception as e:
        return {"error": str(e)}


def complete_task(task_id: str, evidence: Optional[str] = None) -> Dict[str, Any]:
    """
    Complete a claimed task.

    Per TODO-6: Agent Task Backlog UI
    Calls PUT /api/tasks/{task_id}/complete endpoint.

    Args:
        task_id: Task ID to complete
        evidence: Optional evidence/notes

    Returns:
        Updated task dict or error dict
    """
    try:
        params = {}
        if evidence:
            params["evidence"] = evidence

        with httpx.Client(base_url=_API_BASE_URL, timeout=10.0) as client:
            response = client.put(
                f"/api/tasks/{task_id}/complete",
                params=params
            )
            if response.status_code == 200:
                return response.json()
            return {"error": response.text, "status_code": response.status_code}
    except Exception as e:
        return {"error": str(e)}


def get_agent_tasks(agent_id: str) -> List[Dict[str, Any]]:
    """
    Get tasks assigned to a specific agent.

    Per TODO-6: Agent Task Backlog UI

    Args:
        agent_id: Agent ID

    Returns:
        List of tasks assigned to the agent
    """
    try:
        with httpx.Client(base_url=_API_BASE_URL, timeout=10.0) as client:
            response = client.get("/api/tasks", params={"agent_id": agent_id})
            if response.status_code == 200:
                return response.json()
            return []
    except Exception:
        return []


# =============================================================================
# SESSION EVIDENCE LINKING (P11.5)
# =============================================================================

def link_evidence_to_session(
    session_id: str,
    evidence_source: str
) -> Dict[str, Any]:
    """
    Link an evidence file to a session.

    Per P11.5: Session Evidence Attachments.
    Per GAP-DATA-003: Evidence attachment functionality.
    Calls POST /api/sessions/{session_id}/evidence endpoint.

    Args:
        session_id: Session ID
        evidence_source: Path to evidence file

    Returns:
        Success dict or error dict
    """
    try:
        with httpx.Client(base_url=_API_BASE_URL, timeout=10.0) as client:
            response = client.post(
                f"/api/sessions/{session_id}/evidence",
                json={"evidence_source": evidence_source}
            )
            if response.status_code == 201:
                return response.json()
            return {"error": response.text, "status_code": response.status_code}
    except Exception as e:
        return {"error": str(e)}


def get_session_evidence(session_id: str) -> List[str]:
    """
    Get all evidence files linked to a session.

    Per P11.5: Session Evidence Attachments.
    Calls GET /api/sessions/{session_id}/evidence endpoint.

    Args:
        session_id: Session ID

    Returns:
        List of evidence file paths
    """
    try:
        with httpx.Client(base_url=_API_BASE_URL, timeout=10.0) as client:
            response = client.get(f"/api/sessions/{session_id}/evidence")
            if response.status_code == 200:
                data = response.json()
                return data.get("evidence_files", [])
            return []
    except Exception:
        return []
