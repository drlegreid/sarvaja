"""
Heuristic Checks: Session Evidence Domain.

Per D.4: Rule-driven integrity checks for session evidence.
Per DOC-SIZE-01-v1: Split from heuristic_checks.py to stay under 300 lines.

Validates that sessions contain MCP tool calls, thoughts, and evidence files
as captured by gov-sessions MCP tools (session_tool_call, session_thought,
test_evidence_push).

Created: 2026-02-01
"""
import logging

import httpx

logger = logging.getLogger(__name__)


def _api_get(api_base_url: str, endpoint: str) -> dict:
    """Safe API GET with error handling."""
    try:
        resp = httpx.get(f"{api_base_url}{endpoint}", timeout=10.0)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("items", data) if isinstance(data, dict) else data
    except Exception as e:
        logger.debug(f"Heuristic API call failed: {endpoint}: {e}")
    return []


def _get_completed_sessions(api_base_url: str, limit: int = 50) -> list:
    """Fetch completed (ended) sessions."""
    sessions = _api_get(api_base_url, f"/api/sessions?limit={limit}")
    return [s for s in sessions if s.get("status") == "COMPLETED" or s.get("end_time")]


def _is_backfilled_session(session: dict) -> bool:
    """Check if a session was created via backfill (no live MCP data expected).

    Backfilled sessions lack agent_id and have description indicating
    they were reconstructed from evidence files, not live sessions.
    """
    desc = (session.get("description") or "").lower()
    return (
        "backfill" in desc
        or (not session.get("agent_id") and not session.get("session_id", "").startswith("SESSION-2026-01-30"))
    )


def check_session_evidence_files(api_base_url: str) -> dict:
    """H-SESSION-002: Ended sessions must have evidence files.

    Sessions that have completed should have at least one evidence file
    linked via the has-evidence relation or file_path field.
    """
    completed = _get_completed_sessions(api_base_url)
    if not completed:
        return {
            "status": "SKIP",
            "message": "No completed sessions to check",
            "violations": [],
        }

    violations = []
    checked = 0
    for s in completed[:30]:  # Cap to avoid excessive API calls
        sid = s.get("session_id", "unknown")
        has_file = bool(s.get("file_path"))
        has_evidence = bool(s.get("evidence_files"))
        if not has_file and not has_evidence:
            # Double-check via evidence endpoint
            ev = _api_get(api_base_url, f"/api/sessions/{sid}/evidence")
            if isinstance(ev, dict):
                if ev.get("evidence_count", 0) == 0:
                    violations.append(sid)
            elif not ev:
                violations.append(sid)
        checked += 1

    return {
        "status": "FAIL" if violations else "PASS",
        "message": (
            f"{len(violations)}/{checked} ended sessions lack evidence files"
            if violations
            else f"All {checked} checked sessions have evidence"
        ),
        "violations": violations[:20],
    }


def check_session_stale_active(api_base_url: str) -> dict:
    """H-SESSION-003: Sessions >24h old should not be ACTIVE.

    Long-running ACTIVE sessions indicate forgotten cleanup or
    missing session_end calls.
    """
    from datetime import datetime, timedelta, timezone

    sessions = _api_get(api_base_url, "/api/sessions?limit=200")
    active = [s for s in sessions if s.get("status") == "ACTIVE"]
    if not active:
        return {"status": "PASS", "message": "No active sessions", "violations": []}

    threshold = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    violations = []
    for s in active:
        start = s.get("start_time", "")
        if start and start < threshold:
            violations.append(s.get("session_id", "unknown"))

    return {
        "status": "FAIL" if violations else "PASS",
        "message": (
            f"{len(violations)} sessions active >24h (stale)"
            if violations
            else f"All {len(active)} active sessions are recent"
        ),
        "violations": violations[:20],
    }


def check_session_tool_calls(api_base_url: str) -> dict:
    """H-SESSION-005: Ended sessions should have MCP tool call records.

    Gov-sessions MCP tool session_tool_call should be called during
    session operations. Sessions without any tool_call records indicate
    the integration gap: operations happen but aren't captured.
    """
    completed = _get_completed_sessions(api_base_url)
    if not completed:
        return {
            "status": "SKIP",
            "message": "No completed sessions to check",
            "violations": [],
        }

    violations = []
    checked = 0
    skipped = 0
    for s in completed[:20]:  # Cap to avoid N+1 overhead
        if _is_backfilled_session(s):
            skipped += 1
            continue
        sid = s.get("session_id", "unknown")
        tc = _api_get(api_base_url, f"/api/sessions/{sid}/tool_calls")
        count = 0
        if isinstance(tc, dict):
            count = tc.get("tool_call_count", 0)
        elif isinstance(tc, list):
            count = len(tc)

        if count == 0:
            violations.append(sid)
        checked += 1

    if checked == 0:
        return {
            "status": "SKIP",
            "message": f"All {skipped} sessions are backfilled (no live MCP data expected)",
            "violations": [],
        }

    return {
        "status": "FAIL" if violations else "PASS",
        "message": (
            f"{len(violations)}/{checked} live sessions have NO tool call records"
            f" ({skipped} backfilled skipped)"
            if violations
            else f"All {checked} live sessions have tool call records"
            f" ({skipped} backfilled skipped)"
        ),
        "violations": violations[:20],
    }


def check_session_thoughts(api_base_url: str) -> dict:
    """H-SESSION-006: Ended sessions should have thought/reasoning records.

    Gov-sessions MCP tool session_thought should capture reasoning steps.
    Sessions without thoughts indicate missing cognitive trace capture.
    Skips backfilled sessions that predate MCP integration.
    """
    completed = _get_completed_sessions(api_base_url)
    if not completed:
        return {
            "status": "SKIP",
            "message": "No completed sessions to check",
            "violations": [],
        }

    violations = []
    checked = 0
    skipped = 0
    for s in completed[:20]:
        if _is_backfilled_session(s):
            skipped += 1
            continue
        sid = s.get("session_id", "unknown")
        th = _api_get(api_base_url, f"/api/sessions/{sid}/thoughts")
        count = 0
        if isinstance(th, dict):
            count = th.get("thought_count", 0)
        elif isinstance(th, list):
            count = len(th)

        if count == 0:
            violations.append(sid)
        checked += 1

    if checked == 0:
        return {
            "status": "SKIP",
            "message": f"All {skipped} sessions are backfilled (no live MCP data expected)",
            "violations": [],
        }

    return {
        "status": "FAIL" if violations else "PASS",
        "message": (
            f"{len(violations)}/{checked} live sessions have NO thought records"
            f" ({skipped} backfilled skipped)"
            if violations
            else f"All {checked} live sessions have thought records"
            f" ({skipped} backfilled skipped)"
        ),
        "violations": violations[:20],
    }


# ===== REGISTRY (Session Evidence checks only) =====

SESSION_EVIDENCE_CHECKS = [
    {
        "id": "H-SESSION-002",
        "domain": "SESSION",
        "name": "Ended session evidence files",
        "check_fn": check_session_evidence_files,
    },
    {
        "id": "H-SESSION-003",
        "domain": "SESSION",
        "name": "Stale active sessions (>24h)",
        "check_fn": check_session_stale_active,
    },
    {
        "id": "H-SESSION-005",
        "domain": "SESSION",
        "name": "Session MCP tool call records",
        "check_fn": check_session_tool_calls,
    },
    {
        "id": "H-SESSION-006",
        "domain": "SESSION",
        "name": "Session thought/reasoning records",
        "check_fn": check_session_thoughts,
    },
]
