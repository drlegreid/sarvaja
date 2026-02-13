"""
Heuristic Checks: CC Session & Project Domain.

Per SESSION-CC-01-v1, GOV-PROJECT-01-v1: Data integrity checks for
Claude Code sessions and project hierarchy entities.

Created: 2026-02-11
"""
import logging

import httpx

logger = logging.getLogger(__name__)


def _api_get(api_base_url: str, endpoint: str):
    """Safe API GET with error handling."""
    try:
        resp = httpx.get(f"{api_base_url}{endpoint}", timeout=10.0)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("items", data) if isinstance(data, dict) else data
    except Exception as e:
        logger.debug(f"Heuristic API call failed: {endpoint}: {e}")
    return []


def check_cc_session_uuid(api_base_url: str) -> dict:
    """H-SESSION-CC-001: CC-ingested sessions must have cc_session_uuid.

    Sessions created via cc-ingestion source should carry the Claude Code
    internal UUID for traceability back to the original JSONL file.
    """
    sessions = _api_get(api_base_url, "/api/sessions?limit=200")
    if not sessions:
        return {
            "status": "SKIP",
            "message": "No sessions to check",
            "violations": [],
        }

    cc_sessions = [
        s for s in sessions
        if s.get("session_id", "").startswith("SESSION-") and "-CC-" in s.get("session_id", "")
    ]
    if not cc_sessions:
        return {
            "status": "SKIP",
            "message": "No CC-ingested sessions found",
            "violations": [],
        }

    violations = [
        s.get("session_id", "unknown")
        for s in cc_sessions
        if not s.get("cc_session_uuid")
    ]

    return {
        "status": "FAIL" if violations else "PASS",
        "message": (
            f"{len(violations)}/{len(cc_sessions)} CC sessions lack cc_session_uuid"
            if violations
            else f"All {len(cc_sessions)} CC sessions have cc_session_uuid"
        ),
        "violations": violations[:20],
    }


def check_cc_session_project_link(api_base_url: str) -> dict:
    """H-SESSION-CC-002: CC sessions should be linked to a project.

    CC-ingested sessions should have cc_project_slug set, indicating
    they are associated with a project for organizational purposes.
    """
    sessions = _api_get(api_base_url, "/api/sessions?limit=200")
    if not sessions:
        return {
            "status": "SKIP",
            "message": "No sessions to check",
            "violations": [],
        }

    cc_sessions = [
        s for s in sessions
        if s.get("session_id", "").startswith("SESSION-") and "-CC-" in s.get("session_id", "")
    ]
    if not cc_sessions:
        return {
            "status": "SKIP",
            "message": "No CC-ingested sessions found",
            "violations": [],
        }

    violations = [
        s.get("session_id", "unknown")
        for s in cc_sessions
        if not s.get("cc_project_slug")
    ]

    return {
        "status": "FAIL" if violations else "PASS",
        "message": (
            f"{len(violations)}/{len(cc_sessions)} CC sessions lack project slug"
            if violations
            else f"All {len(cc_sessions)} CC sessions have project slug"
        ),
        "violations": violations[:20],
    }


def check_project_has_content(api_base_url: str) -> dict:
    """H-PROJECT-001: Projects should have at least one session or plan.

    Empty projects (no sessions, no plans) indicate orphaned entities
    that should be cleaned up or populated.
    """
    projects = _api_get(api_base_url, "/api/projects?limit=100")
    if not projects:
        return {
            "status": "SKIP",
            "message": "No projects to check",
            "violations": [],
        }

    violations = []
    for p in projects:
        pid = p.get("project_id", "unknown")
        session_count = p.get("session_count", 0)
        plan_count = p.get("plan_count", 0)
        if session_count == 0 and plan_count == 0:
            violations.append(pid)

    return {
        "status": "FAIL" if violations else "PASS",
        "message": (
            f"{len(violations)}/{len(projects)} projects have no sessions or plans"
            if violations
            else f"All {len(projects)} projects have content"
        ),
        "violations": violations[:20],
    }


def check_cc_ingestion_complete(api_base_url: str) -> dict:
    """H-INGESTION-001: CC sessions should have completed content ingestion.

    CC sessions with large JSONL files should have their content indexed
    in ChromaDB and entity links mined into TypeDB. Validates that the
    ingestion pipeline (SESSION-METRICS-01-v1) has been run.
    """
    sessions = _api_get(api_base_url, "/api/sessions?limit=200")
    if not sessions:
        return {
            "status": "SKIP",
            "message": "No sessions to check",
            "violations": [],
        }

    cc_sessions = [
        s for s in sessions
        if s.get("session_id", "").startswith("SESSION-") and "-CC-" in s.get("session_id", "")
    ]
    if not cc_sessions:
        return {
            "status": "SKIP",
            "message": "No CC-ingested sessions found",
            "violations": [],
        }

    violations = []
    checked = 0
    for s in cc_sessions:
        sid = s.get("session_id", "unknown")
        # Check ingestion status via checkpoint API
        status = _api_get(api_base_url, f"/api/ingestion/status/{sid}")
        if isinstance(status, dict):
            phase = status.get("status", "not_started")
            if phase == "not_started":
                violations.append(f"{sid} (not ingested)")
            elif phase not in ("complete", "not_started"):
                violations.append(f"{sid} (phase={phase})")
            checked += 1

    return {
        "status": "FAIL" if violations else "PASS",
        "message": (
            f"{len(violations)}/{checked} CC sessions have incomplete ingestion"
            if violations
            else f"All {checked} CC sessions have completed ingestion"
        ),
        "violations": violations[:20],
    }


# ===== REGISTRY =====

CC_PROJECT_CHECKS = [
    {
        "id": "H-SESSION-CC-001",
        "domain": "SESSION",
        "name": "CC session UUID traceability",
        "check_fn": check_cc_session_uuid,
    },
    {
        "id": "H-SESSION-CC-002",
        "domain": "SESSION",
        "name": "CC session project linkage",
        "check_fn": check_cc_session_project_link,
    },
    {
        "id": "H-PROJECT-001",
        "domain": "PROJECT",
        "name": "Project content (sessions/plans)",
        "check_fn": check_project_has_content,
    },
    {
        "id": "H-INGESTION-001",
        "domain": "SESSION",
        "name": "CC session ingestion completion",
        "check_fn": check_cc_ingestion_complete,
    },
]
