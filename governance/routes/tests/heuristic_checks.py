"""
Heuristic Data Integrity Checks.

Per D.4: Rule-driven data integrity checks across domains.
Each check is a callable that takes (api_base_url) and returns
a result dict with status, message, and details.

Domains: TASK, SESSION, RULE, AGENT, CROSS-ENTITY

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


# ===== TASK DOMAIN =====

def check_task_descriptions(api_base_url: str) -> dict:
    """H-TASK-001: Non-CLOSED tasks must have descriptions >10 chars."""
    tasks = _api_get(api_base_url, "/api/tasks?limit=200")
    violations = []
    for t in tasks:
        if t.get("status") not in ("DONE", "CLOSED"):
            desc = t.get("description", "")
            if len(desc) < 10:
                violations.append(t.get("task_id", "unknown"))
    return {
        "status": "FAIL" if violations else "PASS",
        "message": f"{len(violations)} tasks with short/missing descriptions" if violations else "All tasks have descriptions",
        "violations": violations[:20],
    }


def check_in_progress_agent(api_base_url: str) -> dict:
    """H-TASK-002: IN_PROGRESS tasks must have agent_id."""
    tasks = _api_get(api_base_url, "/api/tasks?status=IN_PROGRESS&limit=200")
    violations = [
        t.get("task_id", "unknown")
        for t in tasks
        if not t.get("agent_id")
    ]
    return {
        "status": "FAIL" if violations else "PASS",
        "message": f"{len(violations)} IN_PROGRESS tasks without agent" if violations else "All IN_PROGRESS tasks have agents",
        "violations": violations[:20],
    }


def check_done_completed_at(api_base_url: str) -> dict:
    """H-TASK-003: DONE tasks must have completed_at timestamp."""
    tasks = _api_get(api_base_url, "/api/tasks?status=DONE&limit=200")
    violations = [
        t.get("task_id", "unknown")
        for t in tasks
        if not t.get("completed_at")
    ]
    return {
        "status": "FAIL" if violations else "PASS",
        "message": f"{len(violations)} DONE tasks without completed_at" if violations else "All DONE tasks have timestamps",
        "violations": violations[:20],
    }


def check_no_test_tasks(api_base_url: str) -> dict:
    """H-TASK-004: No TEST-* tasks should exist outside test runs."""
    tasks = _api_get(api_base_url, "/api/tasks?limit=200")
    test_tasks = [
        t.get("task_id", "unknown")
        for t in tasks
        if (t.get("task_id") or "").startswith("TEST-")
    ]
    return {
        "status": "FAIL" if test_tasks else "PASS",
        "message": f"{len(test_tasks)} TEST-* tasks found (should be cleaned)" if test_tasks else "No TEST-* task artifacts",
        "violations": test_tasks[:20],
    }


# ===== SESSION DOMAIN =====

def check_session_agent_id(api_base_url: str) -> dict:
    """H-SESSION-001: Active sessions must have agent_id."""
    sessions = _api_get(api_base_url, "/api/sessions?limit=200")
    active = [s for s in sessions if s.get("status") == "ACTIVE"]
    violations = [
        s.get("session_id", "unknown")
        for s in active
        if not s.get("agent_id")
    ]
    return {
        "status": "FAIL" if violations else "PASS",
        "message": f"{len(violations)} active sessions without agent_id" if violations else "All active sessions have agents",
        "violations": violations[:20],
    }


def check_no_test_sessions(api_base_url: str) -> dict:
    """H-SESSION-004: No TEST-* sessions should exist outside test runs."""
    sessions = _api_get(api_base_url, "/api/sessions?limit=200")
    test_sessions = [
        s.get("session_id", "unknown")
        for s in sessions
        if (s.get("session_id") or "").startswith("TEST-")
    ]
    return {
        "status": "FAIL" if test_sessions else "PASS",
        "message": f"{len(test_sessions)} TEST-* sessions found" if test_sessions else "No TEST-* session artifacts",
        "violations": test_sessions[:20],
    }


# ===== RULE DOMAIN =====

def check_rule_directives(api_base_url: str) -> dict:
    """H-RULE-003: Rule directives must be non-empty (>10 chars)."""
    rules = _api_get(api_base_url, "/api/rules?limit=200")
    active = [r for r in rules if r.get("status") == "ACTIVE"]
    violations = [
        r.get("rule_id", "unknown")
        for r in active
        if len(r.get("directive", "")) < 10
    ]
    return {
        "status": "FAIL" if violations else "PASS",
        "message": f"{len(violations)} rules with short/missing directives" if violations else "All rules have directives",
        "violations": violations[:20],
    }


def check_no_test_rules(api_base_url: str) -> dict:
    """H-RULE-004: No TEST-* rules outside test runs."""
    rules = _api_get(api_base_url, "/api/rules?limit=200")
    test_rules = [
        r.get("rule_id", "unknown")
        for r in rules
        if (r.get("rule_id") or "").startswith("TEST-")
    ]
    return {
        "status": "FAIL" if test_rules else "PASS",
        "message": f"{len(test_rules)} TEST-* rules found" if test_rules else "No TEST-* rule artifacts",
        "violations": test_rules[:20],
    }


# ===== AGENT DOMAIN =====

def check_agent_trust_scores(api_base_url: str) -> dict:
    """H-AGENT-001: Registered agents must have trust_score > 0."""
    agents = _api_get(api_base_url, "/api/agents")
    if isinstance(agents, dict):
        agents = agents.get("items", [])
    violations = [
        a.get("agent_id", "unknown")
        for a in agents
        if (a.get("trust_score") or 0) <= 0
    ]
    return {
        "status": "FAIL" if violations else "PASS",
        "message": f"{len(violations)} agents with zero trust score" if violations else "All agents have trust scores",
        "violations": violations[:20],
    }


def check_agent_last_active(api_base_url: str) -> dict:
    """H-AGENT-002: Agent last_active should be within 30 days."""
    from datetime import datetime, timedelta
    agents = _api_get(api_base_url, "/api/agents")
    if isinstance(agents, dict):
        agents = agents.get("items", [])
    threshold = (datetime.now() - timedelta(days=30)).isoformat()
    violations = []
    for a in agents:
        last = a.get("last_active")
        if last and last < threshold:
            violations.append(a.get("agent_id", "unknown"))
    return {
        "status": "FAIL" if violations else "PASS",
        "message": f"{len(violations)} agents inactive >30 days" if violations else "All agents recently active or new",
        "violations": violations[:20],
    }


# ===== REGISTRY =====
# Per DOC-SIZE-01-v1: Cross-entity/API/UI checks split to heuristic_checks_cross.py

from governance.routes.tests.heuristic_checks_cross import CROSS_API_UI_CHECKS

HEURISTIC_CHECKS = [
    {"id": "H-TASK-001", "domain": "TASK", "name": "Task descriptions", "check_fn": check_task_descriptions},
    {"id": "H-TASK-002", "domain": "TASK", "name": "IN_PROGRESS agent assignment", "check_fn": check_in_progress_agent},
    {"id": "H-TASK-003", "domain": "TASK", "name": "DONE completion timestamps", "check_fn": check_done_completed_at},
    {"id": "H-TASK-004", "domain": "TASK", "name": "No TEST-* task artifacts", "check_fn": check_no_test_tasks},
    {"id": "H-SESSION-001", "domain": "SESSION", "name": "Active session agent_id", "check_fn": check_session_agent_id},
    {"id": "H-SESSION-004", "domain": "SESSION", "name": "No TEST-* session artifacts", "check_fn": check_no_test_sessions},
    {"id": "H-RULE-003", "domain": "RULE", "name": "Rule directive content", "check_fn": check_rule_directives},
    {"id": "H-RULE-004", "domain": "RULE", "name": "No TEST-* rule artifacts", "check_fn": check_no_test_rules},
    {"id": "H-AGENT-001", "domain": "AGENT", "name": "Agent trust scores", "check_fn": check_agent_trust_scores},
    {"id": "H-AGENT-002", "domain": "AGENT", "name": "Agent last_active recency", "check_fn": check_agent_last_active},
] + CROSS_API_UI_CHECKS
