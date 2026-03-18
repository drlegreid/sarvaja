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
        # BUG-440-HCC-001: Upgrade debug→warning + exc_info for operational visibility
        # BUG-470-HCC-001: Sanitize logger message — exc_info=True already captures full stack
        logger.warning(f"Heuristic API call failed: {endpoint}: {type(e).__name__}", exc_info=True)
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
    # BUG-319-INGEST-001: Cap inner loop to prevent unbounded N+1 API calls
    # (200 sessions × 10s timeout = 2000s worst case without cap)
    for s in cc_sessions[:30]:
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

    # BUG-207-INGESTION-001: Return SKIP when no sessions were actually checked
    # (e.g., all ingestion status API calls failed)
    if checked == 0:
        return {
            "status": "SKIP",
            "message": f"Could not check ingestion for {len(cc_sessions)} CC sessions (API unreachable)",
            "violations": [],
        }

    return {
        "status": "FAIL" if violations else "PASS",
        "message": (
            f"{len(violations)}/{checked} CC sessions have incomplete ingestion"
            if violations
            else f"All {checked} CC sessions have completed ingestion"
        ),
        "violations": violations[:20],
    }


def check_cc_session_tool_pairing(api_base_url: str) -> dict:
    """H-SESSION-CC-003: CC sessions should have matched tool call/result pairs.

    Validates that every tool_use in a CC session JSONL has a corresponding
    tool_result, and vice versa. Orphaned calls indicate lost execution context.
    """
    sessions = _api_get(api_base_url, "/api/sessions?limit=200")
    if not sessions:
        return {"status": "SKIP", "message": "No sessions to check", "violations": []}

    cc_sessions = [
        s for s in sessions
        if s.get("session_id", "").startswith("SESSION-") and "-CC-" in s.get("session_id", "")
    ]
    if not cc_sessions:
        return {"status": "SKIP", "message": "No CC-ingested sessions found", "violations": []}

    violations = []
    checked = 0
    for s in cc_sessions[:30]:
        sid = s.get("session_id", "unknown")
        validation = _api_get(api_base_url, f"/api/sessions/{sid}/validate")
        if not isinstance(validation, dict) or "orphaned_tool_calls" not in validation:
            continue
        checked += 1
        orphaned = validation.get("orphaned_tool_calls", 0) + validation.get("orphaned_tool_results", 0)
        if orphaned > 0:
            total = validation.get("tool_calls_total", 0)
            violations.append(f"{sid} ({orphaned} orphaned of {total} calls)")

    if checked == 0:
        return {
            "status": "SKIP",
            "message": f"Could not validate tool pairing for {len(cc_sessions)} CC sessions",
            "violations": [],
        }

    return {
        "status": "FAIL" if violations else "PASS",
        "message": (
            f"{len(violations)}/{checked} CC sessions have orphaned tool calls/results"
            if violations
            else f"All {checked} CC sessions have complete tool call/result pairing"
        ),
        "violations": violations[:20],
    }


def check_cc_session_mcp_metadata(api_base_url: str) -> dict:
    """H-SESSION-CC-004: CC session MCP calls should have server metadata.

    Validates that MCP tool calls (mcp__*) in CC session JSONL have
    mcpMeta.serverName populated for traceability to the originating
    MCP server (gov-core, gov-tasks, gov-sessions, etc.).
    """
    sessions = _api_get(api_base_url, "/api/sessions?limit=200")
    if not sessions:
        return {"status": "SKIP", "message": "No sessions to check", "violations": []}

    cc_sessions = [
        s for s in sessions
        if s.get("session_id", "").startswith("SESSION-") and "-CC-" in s.get("session_id", "")
    ]
    if not cc_sessions:
        return {"status": "SKIP", "message": "No CC-ingested sessions found", "violations": []}

    violations = []
    checked = 0
    for s in cc_sessions[:30]:
        sid = s.get("session_id", "unknown")
        validation = _api_get(api_base_url, f"/api/sessions/{sid}/validate")
        if not isinstance(validation, dict) or "mcp_calls_total" not in validation:
            continue
        checked += 1
        mcp_total = validation.get("mcp_calls_total", 0)
        mcp_without = validation.get("mcp_calls_without_server", 0)
        if mcp_without > 0:
            violations.append(f"{sid} ({mcp_without}/{mcp_total} MCP calls lack server metadata)")

    if checked == 0:
        return {
            "status": "SKIP",
            "message": f"Could not validate MCP metadata for {len(cc_sessions)} CC sessions",
            "violations": [],
        }

    return {
        "status": "FAIL" if violations else "PASS",
        "message": (
            f"{len(violations)}/{checked} CC sessions have MCP calls without server metadata"
            if violations
            else f"All {checked} CC sessions have complete MCP server metadata"
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
        "id": "H-SESSION-CC-003",
        "domain": "SESSION",
        "name": "CC session tool call/result pairing",
        "check_fn": check_cc_session_tool_pairing,
    },
    {
        "id": "H-SESSION-CC-004",
        "domain": "SESSION",
        "name": "CC session MCP server metadata",
        "check_fn": check_cc_session_mcp_metadata,
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
